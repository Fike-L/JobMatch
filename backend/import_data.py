import pandas as pd
from sqlalchemy import create_engine, text
import urllib.parse

# 1. 配置信息
USER = "root"
PASSWORD = "123456"
HOST = "127.0.0.1"
PORT = "3306"
DB_NAME = "job_db"
FILE_PATH = "job_descriptions.csv"

# 2. 创建基础连接（不指定数据库，用于创建库）
safe_password = urllib.parse.quote_plus(PASSWORD)
base_url = f"mysql+pymysql://{USER}:{safe_password}@{HOST}:{PORT}"
engine = create_engine(base_url)

# 3. 创建数据库 (适配 SQLAlchemy 2.0 语法)
with engine.connect() as conn:
    # 关键修正：使用 text() 包装字符串，并手动提交事务
    conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4"))
    conn.commit()
    print(f"数据库 {DB_NAME} 已就绪。")

# 4. 读取数据
# 建议先读取 5000 行看看效果，100万行全部导入可能需要几分钟
print("正在读取 CSV 文件...")
try:
    df = pd.read_csv(FILE_PATH, nrows=5000)
except FileNotFoundError:
    print(f"错误：找不到文件 {FILE_PATH}，请检查路径！")
    exit()

# 5. 写入数据库
# 创建指向特定数据库的引擎
db_url = f"mysql+pymysql://{USER}:{safe_password}@{HOST}:{PORT}/{DB_NAME}"
db_engine = create_engine(db_url)

print("正在将数据写入 MySQL...")
# index=False 表示不把 Pandas 的索引列也存进去
df.to_sql('raw_jobs', con=db_engine, if_exists='replace', index=False)

print("✅ 导入成功！现在可以在 PyCharm Database 面板查看到 'raw_jobs' 表了。")

# 使用Kaggle数据集https://www.kaggle.com/datasets/ravindrasinghrana/job-description-dataset