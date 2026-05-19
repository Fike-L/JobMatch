import io
import re

import mysql.connector
import pdfplumber
from docx import Document


class ResumeExtractor:
    def __init__(self, db_config):
        self.db_config = db_config
        self.base_skills = [
            "Java", "Python", "Go", "PHP", "C++", "C#", "JavaScript", "TypeScript",
            "Spring", "Spring Boot", "Spring MVC", "MyBatis", "Hibernate",
            "MySQL", "Oracle", "PostgreSQL", "MongoDB", "Redis",
            "Vue", "React", "Angular", "Node.js",
            "Docker", "Kubernetes", "K8s", "Linux", "Git",
            "数据分析", "机器学习", "深度学习", "自然语言处理", "计算机视觉",
            "测试开发", "自动化测试", "产品设计", "项目管理", "UI设计", "数据仓库", "ETL",
        ]
        self.skill_db = []
        self._initialize_full_industry_skills()

    def _initialize_full_industry_skills(self):
        """加载数据库技能词典，并与内置技能合并。"""
        skills = set(self.base_skills)
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT skill_name FROM skill_dictionary")
            skills.update(str(row[0]).strip() for row in cursor.fetchall() if row[0])
            cursor.close()
            conn.close()
        except Exception as exc:
            print(f"加载技能词典失败，使用内置技能库: {exc}")
        self.skill_db = sorted(skills, key=len, reverse=True)

    def extract_keywords(self, text):
        if not text:
            return []

        text_raw = str(text)
        found = []
        for skill in self.skill_db:
            if re.search(re.escape(skill), text_raw, re.IGNORECASE):
                found.append(skill)
            if len(found) >= 20:
                break
        return list(dict.fromkeys(found))

    def extract_from_pdf(self, file_content: bytes) -> str:
        pages = []
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pages.append(page_text)
        return "\n".join(pages)

    def extract_from_docx(self, file_content: bytes) -> str:
        doc = Document(io.BytesIO(file_content))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    def structure_data(self, text: str):
        raw_text = str(text or "")

        name = "未命名"
        patterns = [
            r"姓名[:：\s]+([A-Za-z\u4e00-\u9fa5]{2,20})",
            r"Name[:：\s]+([A-Za-z\u4e00-\u9fa5]{2,40})",
        ]
        for pattern in patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                break

        skills = self.extract_keywords(raw_text)
        experience_score = min(100, 35 + len(re.findall(r"(实习|项目|开发|负责|参与|优化|设计)", raw_text)) * 6)
        education_score = 90 if re.search(r"(本科|硕士|博士|大专|学历)", raw_text) else 65
        structure_score = 90 if len(raw_text) >= 120 else 70 if len(raw_text) >= 40 else 50

        return {
            "name": name,
            "skills": skills,
            "raw_text": raw_text,
            "metrics": {
                "experience": min(experience_score, 100),
                "education": min(education_score, 100),
                "structure": min(structure_score, 100),
            },
        }
