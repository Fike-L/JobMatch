# matcher.py 完整修复版
import mysql.connector
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re


class JobMatcher:
    def __init__(self):
        self.db_config = {'host': 'localhost', 'user': 'root', 'password': '123456', 'database': 'job_db'}
        self.skill_db = [
            "Java", "Python", "Go", "PHP", "C++", "C#", "JavaScript", "TypeScript", "HTML", "CSS",
            "Spring Boot", "Spring Cloud", "MyBatis", "Vue", "React", "Angular", "Node.js", "Django", "Flask",
            "MySQL", "Redis", "MongoDB", "Oracle", "SQL Server", "Docker", "Kubernetes", "Hadoop", "Spark",
            "数据分析", "机器学习", "深度学习", "NLP", "PyTorch", "TensorFlow", "小程序", "架构设计", "测试开发",
            "财务报表", "会计", "审计", "人力资源管理", "招聘", "行政管理", "办公软件", "市场营销", "新媒体运营"
        ]
        self.weights = {"skill": 70, "semantic": 30}

    def _get_db_connection(self):
        return mysql.connector.connect(**self.db_config)

    def _extract_keywords(self, text):
        if not text: return []
        found = []
        text_lower = str(text).lower()
        for skill in self.skill_db:
            if skill.lower() in text_lower:
                found.append(skill)
        return list(set(found))

    def _calculate_score(self, resume_text, jd_text, custom_weights=None):
        """核心匹配算法：修正权重敏感度"""
        weights = custom_weights if custom_weights else self.weights
        w_skill = float(weights.get('skill', 70)) / 100
        w_semantic = float(weights.get('semantic', 30)) / 100

        r_txt = str(resume_text).lower().strip()
        j_txt = str(jd_text).lower().strip()

        if not r_txt or not j_txt:
            return 0.0

        # 1. 关键词硬匹配得分 (KW Score)
        r_ks = set(self._extract_keywords(r_txt))
        j_ks = set(self._extract_keywords(j_txt))

        if not j_ks:
            kw_score = 60.0  # 默认及格分
        else:
            intersection = r_ks.intersection(j_ks)
            kw_score = (len(intersection) / len(j_ks)) * 100

        # 2. 语义相似度得分 (Semantic Score)
        def char_tokenizer(t):
            return " ".join(list(re.sub(r'[^\w\u4e00-\u9fa5]', '', t)))

        try:
            # 只有两个文本不同时才计算 TF-IDF，相同直接 100
            if r_txt == j_txt:
                semantic_sim = 100.0
            else:
                vectorizer = TfidfVectorizer()
                tfidf = vectorizer.fit_transform([char_tokenizer(r_txt), char_tokenizer(j_txt)])
                semantic_sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0] * 100
        except:
            semantic_sim = 0.0  # 【修正】不再默认等于 kw_score，防止权重失效

        # 3. 计算最终分
        final_score = (kw_score * w_skill) + (semantic_sim * w_semantic)

        # 4. 【智能修正】针对极短文本的奖励逻辑（仅在文本极短且关键词全中时触发）
        if len(r_txt) < 15 and len(j_txt) < 15 and kw_score >= 100:
            final_score = max(final_score, 98.0)

        # 控制台打印调试，以便确认计算过程
        print(f"计算详情 -> KW分: {kw_score}, 语义分: {semantic_sim}, 权重: {weights}, 总分: {final_score}")

        return round(float(final_score), 1)

    def calculate_recommendations(self, resume_text, top_n=10):
        conn = self._get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT `Job Id` as id, `Job Title` as title, `Salary Range` as salary, `Experience` as experience, `location` as loc, `skills`, `Job Description` as description, `Company` as company FROM jobs LIMIT 500"
        cursor.execute(query)
        jobs = cursor.fetchall()
        results = []
        for job in jobs:
            full_jd = f"{job['title']} {job['description']} {job['skills']}"
            score = self._calculate_score(resume_text, full_jd)
            results.append({"job_info": job, "score": score})
        cursor.close()
        conn.close()
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_n]

    def rank_candidates(self, jd_text):
        conn = self._get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT r.resume_name as name, r.raw_text as text FROM resumes r")
        candidates = cursor.fetchall()
        results = []
        for c in candidates:
            score = self._calculate_score(c['text'], jd_text)
            results.append({
                "name": c['name'], "score": score,
                "skills": self._extract_keywords(c['text']), "text": c['text']
            })
        cursor.close()
        conn.close()
        return sorted(results, key=lambda x: x['score'], reverse=True)

    def test_sync(self, text1, text2):
        return self._calculate_score(text1, text2, self.weights)

    def get_hr_jobs(self, hr_id):
        conn = self._get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT `Job Id` as id, `Job Title` as title, `Salary Range` as salary, `Experience` as experience, `skills`, `Job Description` as description, `Company` as company FROM jobs WHERE hr_id = %s"
        cursor.execute(query, (hr_id,))
        res = cursor.fetchall()
        cursor.close()
        conn.close()
        return res

    def update_job(self, data):
        conn = self._get_db_connection()
        cursor = conn.cursor()
        query = "UPDATE jobs SET `Job Title`=%s, `Salary Range`=%s, `Experience`=%s, `skills`=%s, `Job Description`=%s, `Company`=%s WHERE `Job Id`=%s"
        cursor.execute(query, (
        data['title'], data['salary'], data['experience'], data['skills'], data['description'], data['company'],
        data['id']))
        conn.commit()
        cursor.close()
        conn.close()