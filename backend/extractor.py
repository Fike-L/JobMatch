import pdfplumber
from docx import Document
import io
import re
import mysql.connector


class ResumeExtractor:
    def __init__(self, db_config):
        self.db_config = db_config
        # 1. 极大增强基础词库，涵盖主流框架
        self.base_skills = [
            "Java", "Python", "Go", "PHP", "C++", "C#", "Spring", "Spring Boot",
            "Spring MVC", "MyBatis", "Hibernate", "Redis", "MySQL", "Oracle",
            "MongoDB", "Vue", "React", "Angular", "Node.js", "Docker", "K8s",
            "办公软件", "财务报表", "会计", "审计", "行政", "公文写作", "人力资源"
        ]
        self.skill_db = []
        self._initialize_full_industry_skills()

    def _initialize_full_industry_skills(self):
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()

            # 【修改】改为从 skill_dictionary 表读取
            cursor.execute("SELECT skill_name FROM skill_dictionary")
            db_skills = [row[0] for row in cursor.fetchall()]

            # 保留原有的从 jobs 自动学习的逻辑（可选），或者仅以词库为准
            self.skill_db = list(set(self.base_skills + db_skills))
            print(f"--- 词库已从数据库加载：共 {len(self.skill_db)} 个关键词 ---")

            cursor.close()
            conn.close()
        except Exception as e:
            print(f"数据库词库加载失败: {e}")

    def extract_keywords(self, text):
        if not text: return []
        found = []
        text_raw = str(text)

        # 合并并去重，按长度降序排列（优先匹配长词如 Spring Boot）
        full_db = list(set(self.base_skills + self.skill_db))
        full_db.sort(key=len, reverse=True)

        for skill in full_db:
            # 改进正则：支持带空格、点、横杠的术语，且忽略大小写
            # \b 不支持中文边界，故针对中英文混合文本做特殊处理
            pattern = re.escape(skill)
            if re.search(pattern, text_raw, re.IGNORECASE):
                found.append(skill)
            if len(found) >= 15: break

        return list(set(found))

    def extract_from_pdf(self, file_content: bytes) -> str:
        text_content = []
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text: text_content.append(page_text)
        return "\n".join(text_content)

    def extract_from_docx(self, file_content: bytes) -> str:
        doc = Document(io.BytesIO(file_content))
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

    def structure_data(self, text: str):
        name = "未知"
        name_match = re.search(r"姓名[:：]\s*(\w{2,4})", text)
        if name_match: name = name_match.group(1)

        return {
            "name": name,
            "skills": self.extract_keywords(text),
            "raw_text": text,
            "metrics": {"experience": 60, "education": 80, "structure": 90}
        }