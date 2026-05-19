import re

import mysql.connector
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


DEFAULT_SKILLS = [
    "Java", "Python", "Go", "PHP", "C++", "C#", "JavaScript", "TypeScript",
    "Vue", "React", "Spring Boot", "MyBatis", "MySQL", "Redis", "Docker",
    "Kubernetes", "SQL", "Linux", "Git", "数据分析", "机器学习", "深度学习",
    "自然语言处理", "计算机视觉", "自动化测试", "测试开发", "产品设计",
    "项目管理", "UI设计", "数据仓库", "ETL",
]


class JobMatcher:
    def __init__(self):
        self.db_config = {"host": "localhost", "user": "root", "password": "123456", "database": "job_db"}
        self.skill_db = self._load_skill_db()
        self.weights = {"skill": 40, "token": 0, "semantic": 60}

    def _get_db_connection(self):
        return mysql.connector.connect(**self.db_config)

    def _load_skill_db(self):
        skills = set(DEFAULT_SKILLS)
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT skill_name FROM skill_dictionary")
            for row in cursor.fetchall():
                if row[0]:
                    skills.add(str(row[0]).strip())
            cursor.close()
            conn.close()
        except Exception:
            pass
        return sorted(skills, key=len, reverse=True)

    def _extract_keywords(self, text):
        if not text:
            return []
        found = []
        text_lower = str(text).lower()
        for skill in self.skill_db:
            if skill.lower() in text_lower:
                found.append(skill)
        return list(dict.fromkeys(found))

    def _extract_tokens(self, text):
        cleaned = re.sub(r"[^0-9a-zA-Z\u4e00-\u9fa5+#.]+", " ", str(text).lower())
        raw_tokens = cleaned.split()
        token_set = set()
        for token in raw_tokens:
            if len(token) <= 1:
                continue
            token_set.add(token)
            if re.fullmatch(r"[\u4e00-\u9fa5]+", token):
                for size in (2, 3, 4):
                    if len(token) <= size:
                        continue
                    for index in range(0, len(token) - size + 1):
                        token_set.add(token[index:index + size])
        return token_set

    def build_job_text(self, job):
        if isinstance(job, dict):
            return " ".join(
                filter(
                    None,
                    [
                        str(job.get("title", "")).strip(),
                        str(job.get("company", "")).strip(),
                        str(job.get("skills", "")).strip(),
                        str(job.get("description", "") or job.get("detailed_requirements", "")).strip(),
                    ],
                )
            )
        return str(job or "").strip()

    def _keyword_score(self, resume_text, jd_text):
        resume_keywords = set(self._extract_keywords(resume_text))
        jd_keywords = set(self._extract_keywords(jd_text))
        if not jd_keywords:
            return 0.0
        return (len(resume_keywords & jd_keywords) / len(jd_keywords)) * 100

    def _keyword_precision(self, resume_text, jd_text):
        resume_keywords = set(self._extract_keywords(resume_text))
        jd_keywords = set(self._extract_keywords(jd_text))
        if not resume_keywords:
            return 0.0
        return (len(resume_keywords & jd_keywords) / len(resume_keywords)) * 100

    def _token_overlap_score(self, resume_text, jd_text):
        resume_tokens = self._extract_tokens(resume_text)
        jd_tokens = self._extract_tokens(jd_text)
        if not jd_tokens:
            return 0.0, 0
        overlap = resume_tokens & jd_tokens
        return (len(overlap) / len(jd_tokens)) * 100, len(overlap)

    def _semantic_score(self, resume_text, jd_text):
        def char_tokenizer(text):
            return " ".join(list(re.sub(r"[^\w\u4e00-\u9fa5]", "", text)))

        try:
            if resume_text == jd_text:
                return 100.0
            vectorizer = TfidfVectorizer()
            tfidf = vectorizer.fit_transform([char_tokenizer(resume_text), char_tokenizer(jd_text)])
            return cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0] * 100
        except Exception:
            return 0.0

    def _calculate_score(self, resume_text, jd_text, custom_weights=None):
        weights = custom_weights if custom_weights else self.weights
        w_skill = float(weights.get("skill", 40)) / 100
        w_token = float(weights.get("token", 0)) / 100
        w_semantic = float(weights.get("semantic", 60)) / 100

        r_txt = str(resume_text).lower().strip()
        j_txt = str(jd_text).lower().strip()
        if not r_txt or not j_txt:
            return 0.0

        kw_recall = self._keyword_score(r_txt, j_txt)
        kw_precision = self._keyword_precision(r_txt, j_txt)
        token_score, overlap_count = self._token_overlap_score(r_txt, j_txt)
        semantic_score = self._semantic_score(r_txt, j_txt)
        skill_score = kw_recall * 0.7 + kw_precision * 0.3
        raw_score = skill_score * w_skill + token_score * w_token + semantic_score * w_semantic

        if overlap_count == 0 and semantic_score < 5 and skill_score < 1:
            return 20.0

        if raw_score >= 75:
            final_score = 80 + min((raw_score - 75) * 0.8, 15)
        elif raw_score >= 55:
            final_score = 60 + (raw_score - 55)
        elif raw_score >= 30:
            final_score = 35 + (raw_score - 30)
        else:
            final_score = 20 + raw_score * 0.5

        if skill_score >= 70 and semantic_score >= 45:
            final_score = max(final_score, 82.0)
        elif skill_score >= 55 and overlap_count >= 5:
            final_score = max(final_score, 74.0)

        return round(float(min(final_score, 100.0)), 1)

    def calculate_recommendations(self, resume_text, top_n=10):
        conn = self._get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, title, company, salary_range, skills, detailed_requirements, hr_id
            FROM jobs
            ORDER BY id DESC
            LIMIT 500
            """
        )
        jobs = cursor.fetchall()
        cursor.close()
        conn.close()

        results = []
        for job in jobs:
            full_jd = self.build_job_text(
                {
                    "title": job["title"],
                    "company": job["company"],
                    "skills": job["skills"],
                    "description": job["detailed_requirements"],
                }
            )
            score = self._calculate_score(resume_text, full_jd)
            results.append(
                {
                    "job_info": {
                        "id": job["id"],
                        "title": job["title"],
                        "company": job["company"],
                        "salary": job["salary_range"],
                        "skills": job["skills"],
                        "description": job["detailed_requirements"],
                    },
                    "score": score,
                }
            )

        results.sort(key=lambda item: item["score"], reverse=True)
        return results[:top_n]

    def rank_candidates(self, jd_text):
        conn = self._get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT user_id, resume_name AS name, raw_text AS text FROM resumes")
        candidates = cursor.fetchall()
        cursor.close()
        conn.close()

        results = []
        for candidate in candidates:
            score = self._calculate_score(candidate["text"], jd_text)
            results.append(
                {
                    "user_id": candidate["user_id"],
                    "name": candidate["name"],
                    "score": score,
                    "skills": self._extract_keywords(candidate["text"]),
                    "text": candidate["text"],
                }
            )
        return sorted(results, key=lambda item: item["score"], reverse=True)

    def test_sync(self, text1, text2):
        return self._calculate_score(text1, text2, self.weights)

    def get_hr_jobs(self, hr_id):
        conn = self._get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, title, company, salary_range, skills, detailed_requirements
            FROM jobs
            WHERE hr_id = %s
            ORDER BY id DESC
            """,
            (hr_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return [
            {
                "id": row["id"],
                "title": row["title"],
                "company": row["company"],
                "salary": row["salary_range"],
                "skills": row["skills"],
                "description": row["detailed_requirements"],
            }
            for row in rows
        ]

    def update_job(self, data):
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE jobs
            SET title = %s, salary_range = %s, skills = %s, detailed_requirements = %s, company = %s
            WHERE id = %s
            """,
            (
                data["title"],
                data["salary"],
                data.get("skills", ""),
                data["description"],
                data["company"],
                data["id"],
            ),
        )
        conn.commit()
        cursor.close()
        conn.close()
