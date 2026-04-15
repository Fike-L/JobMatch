import sys
import os

# --- 必须放在最前面：修复打包后无窗口模式下的环境问题 ---
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

# --- 第一部分：所有的 Import 语句 ---
import mysql
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from extractor import ResumeExtractor
from matcher import JobMatcher
from datetime import date

# --- 第二部分：基础配置与实例初始化 ---
app = FastAPI()

# 数据库配置统一管理
db_config = {'host': 'localhost', 'user': 'root', 'password': '123456', 'database': 'job_db'}

# 初始化解析引擎与匹配引擎
# 确保在路由定义前初始化，避免 NoneType 错误
extractor = ResumeExtractor(db_config)
matcher = JobMatcher()

# --- 第三部分：CORS 跨域配置 ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境必须包含 http://tauri.localhost (Windows)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 第四部分：基础路由 ---

@app.get("/")
def home():
    return {"message": "简历解析系统后端已就绪"}


# --- 第五部分：求职者简历处理逻辑 ---

@app.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    extension = file.filename.split(".")[-1].lower()
    content = await file.read()
    try:
        if extension == "pdf":
            raw_text = extractor.extract_from_pdf(content)
        elif extension in ["doc", "docx"]:
            raw_text = extractor.extract_from_docx(content)
        else:
            raise HTTPException(status_code=400, detail="不支持的文件格式")

        # 调用结构化提取
        structured_info = extractor.structure_data(raw_text)
        return {"status": "success", "data": structured_info}
    except Exception as e:
        print(f"解析报错详情: {str(e)}")
        return {"status": "error", "error": str(e)}


@app.get("/get_my_resume/{user_id}")
async def get_my_resume(user_id: int):
    conn = matcher._get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM resumes WHERE user_id = %s", (user_id,))
        res = cursor.fetchone()
        if res:
            # 【核心修复】重新结构化数据，生成前端缺失的 metrics (雷达图数据)
            structured_info = extractor.structure_data(res['raw_text'])
            structured_info['name'] = res['resume_name']
            return {"status": "success", "data": structured_info}
        return {"status": "error", "message": "未找到简历"}
    finally:
        cursor.close()
        conn.close()


@app.post("/save_resume_status")
@app.post("/save_to_pool")  # 合并自动入库和手动保存逻辑
async def save_resume_logic(payload: dict):
    user_id = payload.get("user_id")
    raw_text = payload.get("raw_text")
    name = payload.get("name", "未命名")

    if not user_id or not raw_text:
        return {"status": "error", "message": "数据不完整"}

    conn = matcher._get_db_connection()
    cursor = conn.cursor()
    try:
        # 【修正】表名：user_resumes -> resumes
        sql = "REPLACE INTO resumes (user_id, resume_name, raw_text) VALUES (%s, %s, %s)"
        cursor.execute(sql, (user_id, name, raw_text))

        # 记录日志
        log_sql = "INSERT INTO system_logs (user_id, action_type, detail) VALUES (%s, 'save_resume', %s)"
        cursor.execute(log_sql, (user_id, f"保存简历: {name}"))

        conn.commit()
        return {"status": "success", "message": "简历保存成功"}
    finally:
        cursor.close()
        conn.close()


# --- 第六部分：匹配与推荐算法接口 ---

@app.post("/match")
async def match_jobs(payload: dict):
    raw_text = payload.get("text", "")
    if not raw_text:
        return {"status": "error", "message": "内容为空"}
    recommendations = matcher.calculate_recommendations(raw_text, top_n=10)
    return {"status": "success", "recommendations": recommendations}


@app.post("/get_skill_gap")
async def get_skill_gap(payload: dict):
    try:
        user_skills = set(payload.get("user_skills", []))
        job_title = payload.get("job_title", "")
        job_skills_raw = payload.get("job_skills_text", "") or ""
        job_skills = set(extractor.extract_keywords(job_skills_raw + job_title))
        gap = list(job_skills - user_skills)
        advice = f"针对【{job_title}】岗位，建议补充：{', '.join(gap)}。" if gap else "您的技能已完全覆盖该要求！"
        return {"status": "success", "gap": gap, "advice": advice}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# --- 第七部分：求职者交互（投递、收藏） ---

@app.post("/apply_job")
async def apply_job(payload: dict):
    seeker_id = payload.get("user_id")
    job_id = payload.get("job_id")
    conn = matcher._get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT hr_id FROM jobs WHERE `Job Id` = %s", (job_id,))
        job = cursor.fetchone()
        if not job: return {"status": "error", "message": "岗位不存在"}
        sql = "INSERT INTO applications (seeker_id, job_id, hr_id) VALUES (%s, %s, %s)"
        cursor.execute(sql, (seeker_id, job_id, job['hr_id']))
        conn.commit()
        return {"status": "success", "message": "投递成功！"}
    finally:
        cursor.close()
        conn.close()


@app.post("/favorite_job")
async def favorite_job(payload: dict):
    user_id = payload.get("user_id")
    job_id = payload.get("job_id")
    conn = matcher._get_db_connection()
    cursor = conn.cursor()
    try:
        sql = "INSERT INTO user_actions (user_id, action_type, target_id) VALUES (%s, 'favorite_job', %s)"
        cursor.execute(sql, (user_id, str(job_id)))
        conn.commit()
        return {"status": "success"}
    finally:
        cursor.close()
        conn.close()


@app.get("/seeker/favorites/{user_id}")
async def get_my_favorites(user_id: int):
    conn = matcher._get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 【修正】表名：translated_jobs -> jobs
        sql = """
            SELECT j.* FROM user_actions ua
            JOIN jobs j ON ua.target_id = j.`Job Id`
            WHERE ua.user_id = %s AND ua.action_type = 'favorite_job'
        """
        cursor.execute(sql, (user_id,))
        return {"status": "success", "data": cursor.fetchall()}
    finally:
        cursor.close()
        conn.close()


@app.get("/seeker/applications/{user_id}")
async def get_seeker_apps(user_id: int):
    conn = matcher._get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT a.status, a.feedback, a.apply_time, 
                   j.`Job Title` as title, j.Company as company
            FROM applications a
            JOIN jobs j ON a.job_id = j.`Job Id`
            WHERE a.seeker_id = %s 
            ORDER BY a.apply_time DESC
        """
        cursor.execute(query, (user_id,))
        data = cursor.fetchall()
        # 打印调试，确保后端发出了 feedback
        print(f"Seeker {user_id} Applications: {data}")
        return {"status": "success", "data": data}
    finally:
        cursor.close()
        conn.close()


# --- 【新增】求职者：取消收藏 ---
@app.post("/unfavorite_job")
async def unfavorite_job(payload: dict):
    user_id = payload.get("user_id")
    job_id = str(payload.get("job_id")) # 数据库中 target_id 是字符串存储的
    conn = matcher._get_db_connection()
    cursor = conn.cursor()
    try:
        sql = "DELETE FROM user_actions WHERE user_id = %s AND target_id = %s AND action_type = 'favorite_job'"
        cursor.execute(sql, (user_id, job_id))
        conn.commit()
        return {"status": "success"}
    finally:
        cursor.close()
        conn.close()

# --- 第八部分：HR 岗位与人才管理 ---

@app.get("/hr/my_jobs/{hr_id}")
async def get_my_jobs(hr_id: int):
    jobs = matcher.get_hr_jobs(hr_id)
    return {"status": "success", "data": jobs}


@app.post("/hr/job/update")
async def update_job(payload: dict):
    matcher.update_job(payload)
    return {"status": "success"}


@app.post("/rank_candidates")
async def rank_candidates(payload: dict):
    description = payload.get("description", "")
    if not description:
        return {"status": "error", "message": "JD 描述为空"}
    results = matcher.rank_candidates(description)
    return {"status": "success", "results": results}


@app.get("/hr/applicants/{hr_id}")
async def get_hr_applicants(hr_id: int):
    conn = matcher._get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 【修正】逻辑：关联最新的 resumes 表获取姓名，关联 jobs 获取标题
        query = """
            SELECT a.id as action_id, r.resume_name as real_name, r.raw_text, 
                   j.`Job Title` as job_title, a.status, a.apply_time
            FROM applications a
            JOIN resumes r ON a.seeker_id = r.user_id
            JOIN jobs j ON a.job_id = j.`Job Id`
            WHERE a.hr_id = %s ORDER BY a.apply_time DESC
        """
        cursor.execute(query, (hr_id,))
        return {"status": "success", "data": cursor.fetchall()}
    finally:
        cursor.close()
        conn.close()


@app.post("/hr/send_intent")
async def send_intent(payload: dict):
    # 调试打印：确认前端传过来的到底是什么
    print(f"收到意向请求: {payload}")

    app_id = payload.get("action_id")
    status = payload.get("status")
    feedback = payload.get("feedback", "")

    conn = matcher._get_db_connection()
    cursor = conn.cursor()
    try:
        # 确保操作的是正确的表名 applications 和正确的字段名 id
        sql = "UPDATE applications SET status = %s, feedback = %s WHERE id = %s"
        cursor.execute(sql, (status, feedback, app_id))
        conn.commit()

        # 检查是否真的更新了行
        if cursor.rowcount == 0:
            print(f"警告：未找到 ID 为 {app_id} 的申请记录")
            return {"status": "error", "message": "更新失败，找不到该记录"}

        return {"status": "success", "message": "意向已成功同步"}
    finally:
        cursor.close()
        conn.close()


# --- 【新增】HR：发布新岗位 ---
@app.post("/hr/job/create")
async def create_job(payload: dict):
    print(f"收到发布请求: {payload}")
    hr_id = payload.get("hr_id")
    conn = matcher._get_db_connection()
    cursor = conn.cursor()
    try:
        # 注意：Kaggle 数据集有很多字段，我们必须给默认值，否则会报错
        sql = """
            INSERT INTO jobs (
                `Job Title`, `Company`, `Salary Range`, `Experience`, 
                `skills`, `Job Description`, `hr_id`, `location`,
                `Qualifications`, `Country`, `Work Type`, `Company Size`, `Job Posting Date`
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        # 补全基础数据，防止触发数据库 NOT NULL 约束
        cursor.execute(sql, (
            payload['title'],
            payload['company'],
            payload.get('salary', '$50K-$100K'),
            payload.get('experience', '1-3 Years'),
            payload['skills'],
            payload['description'],
            hr_id,
            payload.get('location', 'Remote'),
            'Bachelor', # 默认学历
            'Global',   # 默认国家
            'Full-Time',# 默认工种
            '500-1000', # 默认公司规模
            date.today().isoformat() # 今天的日期
        ))
        conn.commit()
        return {"status": "success", "message": "岗位已入库"}
    except Exception as e:
        print(f"数据库插入报错: {str(e)}")
        return {"status": "error", "message": f"发布失败: {str(e)}"}
    finally:
        cursor.close()
        conn.close()

# --- 第九部分：用户与系统管理 ---

@app.post("/login")
async def login(payload: dict):
    username = payload.get("username")
    password = payload.get("password")

    try:
        conn = matcher._get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT id, username, role FROM users WHERE username = %s AND password = %s"
            cursor.execute(query, (username, password))
            user = cursor.fetchone()
            if user:
                cursor.execute("INSERT INTO user_actions (user_id, action_type) VALUES (%s, 'login')", (user['id'],))
                conn.commit()
                return {"status": "success", "user": user}
            raise HTTPException(status_code=401, detail="账号或密码错误")
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        # 暴力记录错误到桌面，看看究竟是为什么
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        with open(os.path.join(desktop, "db_error.txt"), "a", encoding="utf-8") as f:
            f.write(f"登录报错: {str(e)}\n")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/register")
async def register(payload: dict):
    username = payload.get("username")
    password = payload.get("password")
    role = payload.get("role")
    conn = matcher._get_db_connection()
    cursor = conn.cursor()
    try:
        query = "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, password, role))
        conn.commit()
        return {"status": "success"}
    except:
        return {"status": "error", "message": "用户名已存在"}
    finally:
        cursor.close()
        conn.close()


@app.get("/system_stats")
async def get_system_stats():
    conn = matcher._get_db_connection()
    cursor = conn.cursor(dictionary=True)
    today = date.today()
    try:
        # 1. 统计用户
        cursor.execute("SELECT role, COUNT(*) as count FROM users GROUP BY role")
        user_counts = {row['role']: row['count'] for row in cursor.fetchall()}

        # 2. 今日活跃
        cursor.execute(
            "SELECT COUNT(DISTINCT user_id) as active FROM user_actions WHERE action_type='login' AND DATE(action_time)=%s",
            (today,))
        active_today = cursor.fetchone()['active']

        # 3. 投递记录
        cursor.execute("SELECT COUNT(*) as count FROM applications")
        app_total = cursor.fetchone()['count']

        # 4. 日志
        cursor.execute(
            "SELECT u.username, ua.action_type, ua.action_time FROM user_actions ua JOIN users u ON ua.user_id=u.id ORDER BY action_time DESC LIMIT 10")
        logs = cursor.fetchall()

        return {
            "status": "success",
            "stats": [
                {"title": "用户总量", "value": str(sum(user_counts.values())), "icon": "User", "color": "#409EFF"},
                {"title": "今日活跃", "value": str(active_today), "icon": "Timer", "color": "#67C23A"},
                {"title": "申请总数", "value": str(app_total), "icon": "Check", "color": "#E6A23C"},
                {"title": "系统岗位数", "value": "500", "icon": "Briefcase", "color": "#F56C6C"}
            ],
            "chart_data": {"names": ["求职者", "HR", "管理员"],
                           "values": [user_counts.get('seeker', 0), user_counts.get('hr', 0),
                                      user_counts.get('admin', 0)]},
            "logs": logs
        }
    finally:
        cursor.close()
        conn.close()


@app.get("/get_dictionary")
async def get_dict():
    conn = matcher._get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 从数据库表 skill_dictionary 读取真实的名称和分类
        cursor.execute("SELECT skill_name as term, category FROM skill_dictionary")
        data = cursor.fetchall()
        return {"status": "success", "data": data}
    finally:
        cursor.close()
        conn.close()

# --- 修正 2：即时验证接口，强制刷新权重引用 ---
@app.post("/calculate_instant_sim")
async def calculate_instant_sim(payload: dict):
    t1 = payload.get("resumeText", "")
    t2 = payload.get("jdText", "")
    # 显式传递当前全局权重，确保实验室测试结果随滑块跳变
    score = matcher._calculate_score(t1, t2, custom_weights=matcher.weights)
    return {"status": "success", "score": score}


@app.post("/admin/skills/add")
async def add_skill(payload: dict):
    name = payload.get("name")
    category = payload.get("category", "通用")
    conn = matcher._get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO skill_dictionary (skill_name, category) VALUES (%s, %s)", (name, category))
        conn.commit()
        # 关键：更新内存中的词库
        extractor._initialize_full_industry_skills()
        matcher.skill_db = extractor.skill_db
        return {"status": "success"}
    except:
        return {"status": "error", "message": "词汇已存在"}
    finally:
        cursor.close()
        conn.close()

@app.post("/admin/skills/delete")
async def delete_skill(payload: dict):
    name = payload.get("name")
    conn = matcher._get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM skill_dictionary WHERE skill_name = %s", (name,))
    conn.commit()
    extractor._initialize_full_industry_skills()
    matcher.skill_db = extractor.skill_db
    cursor.close()
    conn.close()
    return {"status": "success"}

# 1. 修复权重更新失败问题
@app.post("/update_algorithm_weights")
async def update_weights(payload: dict):
    try:
        # 确保 payload 格式为 {"skill": 70, "semantic": 30}
        matcher.weights['skill'] = int(payload.get('skill', 70))
        matcher.weights['semantic'] = int(payload.get('semantic', 30))
        print(f"管理员全局调整权重为: {matcher.weights}")
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": f"更新失败: {str(e)}"}

# 2. 修复词库添加时的报错显示
@app.post("/admin/skills/add")
async def add_skill(payload: dict):
    name = payload.get("name")
    category = payload.get("category")
    conn = matcher._get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO skill_dictionary (skill_name, category) VALUES (%s, %s)", (name, category))
        conn.commit()
        # 刷新内存
        extractor._initialize_full_industry_skills()
        matcher.skill_db = extractor.skill_db
        return {"status": "success"}
    except mysql.connector.Error as err:
        if err.errno == 1062: # 唯一索引冲突
            return {"status": "error", "message": "该词汇已在库中，请勿重复添加"}
        return {"status": "error", "message": f"数据库错误: {err.msg}"}
    except Exception as e:
        # 捕获之前提到的 ResumeExtractor 属性错误
        print(f"系统逻辑错误: {str(e)}")
        return {"status": "error", "message": f"服务器逻辑错误: {str(e)}"}
    finally:
        cursor.close()
        conn.close()

# 1. 公告系统
@app.get("/common/announcements")
async def get_announcements():
    conn = matcher._get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM announcements ORDER BY create_time DESC")
    res = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"status": "success", "data": res}

@app.post("/admin/announcements/post")
async def post_announcement(payload: dict):
    conn = matcher._get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO announcements (title, content) VALUES (%s, %s)", (payload['title'], payload['content']))
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success"}

# 2. 面试日程
@app.post("/hr/schedule_interview")
async def schedule_interview(payload: dict):
    conn = matcher._get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO interview_schedules (application_id, interview_time, location, notes) VALUES (%s, %s, %s, %s)",
        (payload['app_id'], payload['time'], payload['location'], payload['notes'])
    )
    # 同时更新申请状态为“邀请面试”
    cursor.execute("UPDATE applications SET status = '邀请面试' WHERE id = %s", (payload['app_id'],))
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success"}

@app.get("/seeker/interviews/{user_id}")
async def get_my_interviews(user_id: int):
    conn = matcher._get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT i.*, j.`Job Title` as title, j.Company 
        FROM interview_schedules i
        JOIN applications a ON i.application_id = a.id
        JOIN jobs j ON a.job_id = j.`Job Id`
        WHERE a.seeker_id = %s
    """
    cursor.execute(sql, (user_id,))
    res = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"status": "success", "data": res}

# 3. 双通道反馈系统 (管理员查看)
@app.post("/common/submit_feedback")
async def submit_feedback(payload: dict):
    role = payload.get("role")
    table = "seeker_feedbacks" if role == "seeker" else "hr_feedbacks"
    id_col = "seeker_id" if role == "seeker" else "hr_id"
    conn = matcher._get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO {table} ({id_col}, content) VALUES (%s, %s)", (payload['user_id'], payload['content']))
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success"}

@app.get("/admin/all_feedbacks")
async def get_all_feedbacks():
    conn = matcher._get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT f.*, u.username FROM seeker_feedbacks f JOIN users u ON f.seeker_id = u.id")
    s_fb = cursor.fetchall()
    cursor.execute("SELECT f.*, u.username FROM hr_feedbacks f JOIN users u ON f.hr_id = u.id")
    h_fb = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"status": "success", "seeker_fb": s_fb, "hr_fb": h_fb}

# 4. 双通道简易论坛
@app.get("/forum/messages/{role}")
async def get_forum_messages(role: str):
    table = "seeker_messages" if role == "seeker" else "hr_messages"
    id_col = "seeker_id" if role == "seeker" else "hr_id"
    conn = matcher._get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT m.*, u.username FROM {table} m JOIN users u ON m.{id_col} = u.id ORDER BY post_time DESC")
    res = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"status": "success", "data": res}

@app.post("/forum/post")
async def post_to_forum(payload: dict):
    role = payload.get("role")
    table = "seeker_messages" if role == "seeker" else "hr_messages"
    id_col = "seeker_id" if role == "seeker" else "hr_id"
    conn = matcher._get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO {table} ({id_col}, content) VALUES (%s, %s)", (payload['user_id'], payload['content']))
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success"}


# --- 第十部分：启动代码 ---
if __name__ == "__main__":
    import uvicorn

    # 定义一个空的日志配置，强制 Uvicorn 不去读取系统终端状态
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO"},
        },
    }

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_config=log_config # 使用自定义的简单配置
    )