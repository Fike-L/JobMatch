import mysql.connector
from mtranslate import translate
import time
import random

# 数据库配置
db_config = {'host': 'localhost', 'user': 'root', 'password': '123456', 'database': 'job_db'}


def translate_db():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # 1. 创建新表（如果不存在）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS translated_jobs (
            `Job Id` BIGINT PRIMARY KEY,
            `Job Title` TEXT,
            `Job Description` TEXT,
            `skills` TEXT,
            `Role` TEXT,
            `Company` TEXT,
            `Salary Range` TEXT,
            `Experience` TEXT,
            `Qualifications` TEXT,
            `location` TEXT
        )
    """)

    # 2. 获取源数据
    cursor.execute("SELECT * FROM raw_jobs LIMIT 500")
    rows = cursor.fetchall()

    print(f"准备处理 {len(rows)} 条数据...")

    for i, row in enumerate(rows):
        job_id = row['Job Id']

        # 检查是否已经翻译过（断点续传）
        cursor.execute("SELECT `Job Id` FROM translated_jobs WHERE `Job Id` = %s", (job_id,))
        if cursor.fetchone():
            continue

        try:
            # --- 优化策略：合并翻译请求以减少 HTTP 调用 ---
            # 使用特殊分隔符 ### 将字段连起来
            source_text = f"{row['Job Title']} ### {row['Job Description']} ### {row['skills']} ### {row['Role']} ### {row['Company']}"

            # 发起翻译
            translated_text = translate(source_text, 'zh-CN')

            # 拆分回原来的字段
            parts = translated_text.split('###')

            # 容错处理：确保拆分出的数量正确
            if len(parts) >= 5:
                t_title, t_desc, t_skills, t_role, t_company = [p.strip() for p in parts[:5]]
            else:
                # 如果拆分失败，单独翻译（保底方案）
                t_title = translate(row['Job Title'], 'zh-CN')
                t_desc = translate(row['Job Description'], 'zh-CN')
                t_skills = translate(row['skills'], 'zh-CN')
                t_role = translate(row['Role'], 'zh-CN')
                t_company = translate(row['Company'], 'zh-CN')

            # 插入新表
            sql = """
                INSERT INTO translated_jobs 
                (`Job Id`, `Job Title`, `Job Description`, `skills`, `Role`, `Company`, `Salary Range`, `Experience`, `Qualifications`, `location`) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                job_id, t_title, t_desc, t_skills, t_role, t_company,
                row['Salary Range'], row['Experience'], row['Qualifications'], row['location']
            ))

            # 每 10 条提交一次
            if i % 10 == 0:
                conn.commit()
                print(f"已完成: {i}/{len(rows)}")

            # --- 关键：随机延迟，防止被封 ---
            time.sleep(random.uniform(1.0, 2.5))

        except Exception as e:
            print(f"第 {i} 条 (ID: {job_id}) 翻译失败: {e}")
            print("等待 10 秒后继续...")
            time.sleep(10)  # 遇到错误多歇一会

    conn.commit()
    print("所有翻译任务完成！")
    cursor.close()
    conn.close()


if __name__ == "__main__":
    translate_db()