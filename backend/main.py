import os
import sys
from datetime import date

import mysql
import mysql.connector
from fastapi import FastAPI, File, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from extractor import ResumeExtractor
from matcher import JobMatcher
from wordcloud_generator import build_wordcloud_svg

# 兼容无控制台环境，避免 stdout/stderr 为空。
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")


db_config = {"host": "localhost", "user": "root", "password": "123456", "database": "job_db"}
APP_STATUS_APPLIED = "已投递"
APP_STATUS_INTERVIEW = "待面试"
APP_STATUS_OFFER = "已录用"
APP_STATUS_REJECTED = "不合适"

app = FastAPI()
extractor = ResumeExtractor(db_config)
matcher = JobMatcher()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_conn():
    return matcher._get_db_connection()


def refresh_skill_runtime():
    extractor._initialize_full_industry_skills()
    matcher.skill_db = matcher._load_skill_db()


def safe_log_system(cursor, user_id, action_type, detail):
    try:
        cursor.execute(
            "INSERT INTO system_logs (user_id, action_type, detail) VALUES (%s, %s, %s)",
            (user_id, action_type, detail),
        )
    except Exception:
        pass


@app.get("/")
def home():
    return {"message": "招聘系统后端服务已启动"}


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

        structured_info = extractor.structure_data(raw_text)
        return {"status": "success", "data": structured_info}
    except Exception as exc:
        print(f"简历解析失败: {exc}")
        return {"status": "error", "error": str(exc)}


@app.get("/get_my_resume/{user_id}")
async def get_my_resume(user_id: int):
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM resumes WHERE user_id = %s", (user_id,))
        res = cursor.fetchone()
        if not res:
            return {"status": "error", "message": "未找到简历"}

        structured_info = extractor.structure_data(res["raw_text"])
        structured_info["name"] = res["resume_name"]
        return {"status": "success", "data": structured_info}
    finally:
        cursor.close()
        conn.close()


@app.post("/save_resume_status")
@app.post("/save_to_pool")
async def save_resume_logic(payload: dict):
    user_id = payload.get("user_id")
    raw_text = payload.get("raw_text")
    name = payload.get("name", "未命名简历")

    if not user_id or not raw_text:
        return {"status": "error", "message": "缺少用户或简历内容"}

    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "REPLACE INTO resumes (user_id, resume_name, raw_text) VALUES (%s, %s, %s)",
            (user_id, name, raw_text),
        )
        safe_log_system(cursor, user_id, "save_resume", f"保存简历: {name}")
        conn.commit()
        return {"status": "success", "message": "简历已保存"}
    finally:
        cursor.close()
        conn.close()


@app.post("/match")
async def match_jobs(payload: dict):
    raw_text = payload.get("text", "")
    if not raw_text:
        return {"status": "error", "message": "内容不能为空"}
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
        advice = (
            "建议补充与 {} 相关的技能：{}".format(job_title, ", ".join(gap))
            if gap
            else "当前技能覆盖较完整，可以继续完善项目经历。"
        )
        return {"status": "success", "gap": gap, "advice": advice}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@app.post("/apply_job")
async def apply_job(payload: dict):
    seeker_id = payload.get("user_id")
    job_id = payload.get("job_id")
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT hr_id FROM jobs WHERE id = %s", (job_id,))
        job = cursor.fetchone()
        if not job:
            return {"status": "error", "message": "岗位不存在"}

        cursor.execute(
            "INSERT INTO applications (seeker_id, job_id, hr_id, status) VALUES (%s, %s, %s, %s)",
            (seeker_id, job_id, job["hr_id"], APP_STATUS_APPLIED),
        )
        cursor.execute(
            "INSERT INTO user_actions (user_id, action_type, target_id) VALUES (%s, 'apply', %s)",
            (seeker_id, str(job_id)),
        )
        conn.commit()
        return {"status": "success", "message": "投递成功"}
    finally:
        cursor.close()
        conn.close()


@app.post("/favorite_job")
async def favorite_job(payload: dict):
    user_id = payload.get("user_id")
    job_id = payload.get("job_id")
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO user_actions (user_id, action_type, target_id) VALUES (%s, 'favorite_job', %s)",
            (user_id, str(job_id)),
        )
        conn.commit()
        return {"status": "success"}
    finally:
        cursor.close()
        conn.close()


@app.post("/unfavorite_job")
async def unfavorite_job(payload: dict):
    user_id = payload.get("user_id")
    job_id = str(payload.get("job_id"))
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM user_actions WHERE user_id = %s AND target_id = %s AND action_type = 'favorite_job'",
            (user_id, job_id),
        )
        conn.commit()
        return {"status": "success"}
    finally:
        cursor.close()
        conn.close()


@app.get("/seeker/favorites/{user_id}")
async def get_my_favorites(user_id: int):
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT
                j.id,
                j.title,
                j.company,
                j.salary_range AS salary,
                '' AS experience,
                '' AS loc,
                j.skills,
                j.detailed_requirements AS description,
                j.detailed_requirements AS responsibilities
            FROM user_actions ua
            JOIN jobs j ON ua.target_id = CAST(j.id AS CHAR)
            WHERE ua.user_id = %s AND ua.action_type = 'favorite_job'
            """,
            (user_id,),
        )
        return {"status": "success", "data": cursor.fetchall()}
    finally:
        cursor.close()
        conn.close()


@app.get("/seeker/applications/{user_id}")
async def get_seeker_apps(user_id: int):
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT a.status, a.feedback, a.apply_time, j.title AS title, j.company AS company
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE a.seeker_id = %s
            ORDER BY a.apply_time DESC
            """,
            (user_id,),
        )
        return {"status": "success", "data": cursor.fetchall()}
    finally:
        cursor.close()
        conn.close()


@app.get("/hr/my_jobs/{hr_id}")
async def get_my_jobs(hr_id: int):
    return {"status": "success", "data": matcher.get_hr_jobs(hr_id)}


@app.post("/hr/job/update")
async def update_job(payload: dict):
    matcher.update_job(payload)
    return {"status": "success"}


@app.post("/rank_candidates")
async def rank_candidates(payload: dict):
    job_text = matcher.build_job_text(payload)
    if not job_text:
        return {"status": "error", "message": "岗位信息不能为空"}
    return {"status": "success", "results": matcher.rank_candidates(job_text)}


@app.get("/jobs/all")
async def get_all_jobs():
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT
                id,
                title,
                company,
                salary_range AS salary,
                skills,
                detailed_requirements AS description
            FROM jobs
            ORDER BY id DESC
            LIMIT 500
            """
        )
        return {"status": "success", "data": cursor.fetchall()}
    finally:
        cursor.close()
        conn.close()


@app.get("/hr/applicants/{hr_id}")
async def get_hr_applicants(hr_id: int):
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT a.id AS action_id, r.resume_name AS real_name, r.raw_text,
                   j.title AS job_title, a.status, a.apply_time
            FROM applications a
            JOIN resumes r ON a.seeker_id = r.user_id
            JOIN jobs j ON a.job_id = j.id
            WHERE a.hr_id = %s
            ORDER BY a.apply_time DESC
            """,
            (hr_id,),
        )
        return {"status": "success", "data": cursor.fetchall()}
    finally:
        cursor.close()
        conn.close()


@app.post("/hr/send_intent")
async def send_intent(payload: dict):
    app_id = payload.get("action_id")
    status = payload.get("status")
    feedback = payload.get("feedback", "")

    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE applications SET status = %s, feedback = %s WHERE id = %s",
            (status, feedback, app_id),
        )
        conn.commit()

        if cursor.rowcount == 0:
            print(f"未找到申请记录 ID: {app_id}")
            return {"status": "error", "message": "未找到对应申请记录"}

        return {"status": "success", "message": "处理完成"}
    finally:
        cursor.close()
        conn.close()


@app.post("/hr/job/create")
async def create_job(payload: dict):
    hr_id = payload.get("hr_id")
    title = str(payload.get("title", "")).strip()
    company = str(payload.get("company", "")).strip()
    salary = str(payload.get("salary", "")).strip()
    skills = str(payload.get("skills", "")).strip()
    description = str(payload.get("description", "")).strip()

    if not all([hr_id, title, company, salary, skills, description]):
        return {"status": "error", "message": "请完整填写岗位标题、公司名称、薪资范围、技能关键词和岗位详细要求"}

    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO jobs (title, company, salary_range, skills, detailed_requirements, hr_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                title,
                company,
                salary,
                skills,
                description,
                hr_id,
            ),
        )
        conn.commit()
        return {"status": "success", "message": "岗位创建成功"}
    except Exception as exc:
        return {"status": "error", "message": f"岗位创建失败: {exc}"}
    finally:
        cursor.close()
        conn.close()


@app.post("/login")
async def login(payload: dict):
    username = payload.get("username")
    password = payload.get("password")

    try:
        conn = get_conn()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT id, username, role FROM users WHERE username = %s AND password = %s",
                (username, password),
            )
            user = cursor.fetchone()
            if user:
                cursor.execute("INSERT INTO user_actions (user_id, action_type) VALUES (%s, 'login')", (user["id"],))
                conn.commit()
                return {"status": "success", "user": user}
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        finally:
            cursor.close()
            conn.close()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/register")
async def register(payload: dict):
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
            (payload.get("username"), payload.get("password"), payload.get("role")),
        )
        conn.commit()
        return {"status": "success"}
    except Exception:
        return {"status": "error", "message": "用户名已存在或注册失败"}
    finally:
        cursor.close()
        conn.close()


@app.get("/system_stats")
async def get_system_stats():
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    today = date.today()
    try:
        cursor.execute("SELECT role, COUNT(*) AS count FROM users GROUP BY role")
        user_counts = {row["role"]: row["count"] for row in cursor.fetchall()}

        cursor.execute(
            "SELECT COUNT(DISTINCT user_id) AS active FROM user_actions WHERE action_type = 'login' AND DATE(action_time) = %s",
            (today,),
        )
        active_today = cursor.fetchone()["active"]

        cursor.execute("SELECT COUNT(*) AS count FROM applications")
        app_total = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) AS count FROM resumes")
        resume_total = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) AS count FROM jobs")
        job_total = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) AS count FROM interview_schedules")
        interview_total = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) AS count FROM applications WHERE status = %s", (APP_STATUS_OFFER,))
        hire_total = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) AS count FROM user_actions WHERE action_type = 'favorite_job'")
        favorite_total = cursor.fetchone()["count"]

        cursor.execute("SELECT action_type, COUNT(*) AS count FROM user_actions GROUP BY action_type")
        action_summary = {row["action_type"]: row["count"] for row in cursor.fetchall()}

        cursor.execute("SELECT status, COUNT(*) AS count FROM applications GROUP BY status")
        application_summary = {row["status"]: row["count"] for row in cursor.fetchall()}

        cursor.execute(
            """
            SELECT u.username, ua.action_type, ua.action_time
            FROM user_actions ua
            JOIN users u ON ua.user_id = u.id
            ORDER BY action_time DESC
            LIMIT 10
            """
        )
        logs = cursor.fetchall()

        return {
            "status": "success",
            "stats": [
                {"title": "用户总数", "value": str(sum(user_counts.values())), "icon": "User", "color": "#409EFF"},
                {"title": "今日活跃", "value": str(active_today), "icon": "Timer", "color": "#67C23A"},
                {"title": "投递总数", "value": str(app_total), "icon": "Check", "color": "#E6A23C"},
                {"title": "岗位总数", "value": str(job_total), "icon": "Briefcase", "color": "#F56C6C"},
            ],
            "chart_data": {
                "names": ["求职者", "HR", "管理员"],
                "values": [user_counts.get("seeker", 0), user_counts.get("hr", 0), user_counts.get("admin", 0)],
            },
            "logs": logs,
            "overview_metrics": {
                "resume_total": resume_total,
                "job_total": job_total,
                "application_total": app_total,
                "favorite_total": favorite_total,
                "interview_total": interview_total,
                "hire_total": hire_total,
                "today_active": active_today,
            },
            "action_summary": {
                "login": action_summary.get("login", 0),
                "save_resume": action_summary.get("save_resume", 0),
                "apply": action_summary.get("apply", 0),
                "favorite_job": action_summary.get("favorite_job", 0),
            },
            "application_summary": {
                "applied": application_summary.get(APP_STATUS_APPLIED, 0),
                "interview": application_summary.get(APP_STATUS_INTERVIEW, 0),
                "offer": application_summary.get(APP_STATUS_OFFER, 0),
                "rejected": application_summary.get(APP_STATUS_REJECTED, 0),
            },
        }
    finally:
        cursor.close()
        conn.close()


@app.get("/get_dictionary")
async def get_dict():
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT skill_name AS term, category FROM skill_dictionary")
        return {"status": "success", "data": cursor.fetchall()}
    finally:
        cursor.close()
        conn.close()


def build_dictionary_cloud():
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT skill_name AS term, category FROM skill_dictionary")
        dictionary = cursor.fetchall()
        cursor.execute("SELECT skills, detailed_requirements AS description FROM jobs LIMIT 1000")
        jobs = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    cloud = []
    for item in dictionary:
        term = item["term"]
        count = 0
        for job in jobs:
            haystack = f"{job.get('skills', '')} {job.get('description', '')}".lower()
            if term.lower() in haystack:
                count += 1
        cloud.append({"name": term, "value": max(count, 1), "category": item["category"]})

    cloud.sort(key=lambda row: row["value"], reverse=True)
    return cloud


@app.get("/admin/dictionary_wordcloud")
async def get_dictionary_wordcloud():
    return {"status": "success", "data": build_dictionary_cloud()[:120]}


@app.get("/admin/dictionary_wordcloud_image")
async def get_dictionary_wordcloud_image():
    svg = build_wordcloud_svg(build_dictionary_cloud())
    return Response(content=svg, media_type="image/svg+xml")


@app.post("/calculate_instant_sim")
async def calculate_instant_sim(payload: dict):
    score = matcher._calculate_score(
        payload.get("resumeText", ""),
        payload.get("jdText", ""),
        custom_weights=matcher.weights,
    )
    return {"status": "success", "score": score}


@app.post("/update_algorithm_weights")
async def update_weights(payload: dict):
    try:
        matcher.weights["skill"] = int(payload.get("skill", 70))
        matcher.weights["semantic"] = int(payload.get("semantic", 30))
        print(f"算法权重已更新: {matcher.weights}")
        return {"status": "success"}
    except Exception as exc:
        return {"status": "error", "message": f"更新失败: {exc}"}


@app.post("/admin/skills/add")
async def add_skill(payload: dict):
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO skill_dictionary (skill_name, category) VALUES (%s, %s)",
            (payload.get("name"), payload.get("category")),
        )
        conn.commit()
        refresh_skill_runtime()
        return {"status": "success"}
    except mysql.connector.Error as err:
        if err.errno == 1062:
            return {"status": "error", "message": "该技能已存在，请勿重复添加"}
        return {"status": "error", "message": f"添加技能失败: {err.msg}"}
    except Exception as exc:
        return {"status": "error", "message": f"添加技能失败: {exc}"}
    finally:
        cursor.close()
        conn.close()


@app.post("/admin/skills/delete")
async def delete_skill(payload: dict):
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM skill_dictionary WHERE skill_name = %s", (payload.get("name"),))
        conn.commit()
        refresh_skill_runtime()
        return {"status": "success"}
    finally:
        cursor.close()
        conn.close()


@app.get("/common/announcements")
async def get_announcements():
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM announcements ORDER BY create_time DESC")
    res = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"status": "success", "data": res}


@app.post("/admin/announcements/post")
async def post_announcement(payload: dict):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO announcements (title, content) VALUES (%s, %s)", (payload["title"], payload["content"]))
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success"}


@app.post("/hr/schedule_interview")
async def schedule_interview(payload: dict):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO interview_schedules (application_id, interview_time, location, notes) VALUES (%s, %s, %s, %s)",
        (payload["app_id"], payload["time"], payload["location"], payload["notes"]),
    )
    cursor.execute("UPDATE applications SET status = %s WHERE id = %s", (APP_STATUS_INTERVIEW, payload["app_id"]))
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success"}


@app.get("/seeker/interviews/{user_id}")
async def get_my_interviews(user_id: int):
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT i.*, j.title AS title, j.company
        FROM interview_schedules i
        JOIN applications a ON i.application_id = a.id
        JOIN jobs j ON a.job_id = j.id
        WHERE a.seeker_id = %s
        """,
        (user_id,),
    )
    res = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"status": "success", "data": res}


@app.post("/common/submit_feedback")
async def submit_feedback(payload: dict):
    role = payload.get("role")
    table = "seeker_feedbacks" if role == "seeker" else "hr_feedbacks"
    id_col = "seeker_id" if role == "seeker" else "hr_id"
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO {table} ({id_col}, content) VALUES (%s, %s)", (payload["user_id"], payload["content"]))
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success"}


@app.get("/admin/all_feedbacks")
async def get_all_feedbacks():
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT f.*, u.username FROM seeker_feedbacks f JOIN users u ON f.seeker_id = u.id")
    s_fb = cursor.fetchall()
    cursor.execute("SELECT f.*, u.username FROM hr_feedbacks f JOIN users u ON f.hr_id = u.id")
    h_fb = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"status": "success", "seeker_fb": s_fb, "hr_fb": h_fb}


@app.get("/forum/messages/{role}")
async def get_forum_messages(role: str):
    table = "seeker_messages" if role == "seeker" else "hr_messages"
    id_col = "seeker_id" if role == "seeker" else "hr_id"
    conn = get_conn()
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
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO {table} ({id_col}, content) VALUES (%s, %s)", (payload["user_id"], payload["content"]))
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success"}


if __name__ == "__main__":
    import uvicorn

    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
        },
        "handlers": {
            "default": {"class": "logging.StreamHandler", "formatter": "default", "stream": "ext://sys.stdout"},
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO"},
        },
    }

    uvicorn.run(app, host="127.0.0.1", port=8000, log_config=log_config)
