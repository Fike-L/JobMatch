<template>
  <div class="login-container">
    <div class="login-shell">
      <section class="capability-panel">
        <div class="panel-kicker">Recruitment OS</div>
        <h1>招聘与岗位推荐系统</h1>
        <p class="panel-subtitle">海量数据库中为你“秒配”契合度最高的理想岗位。</p>

        <div class="capability-grid">
          <article class="capability-card">
            <div class="capability-title">简历资料管理</div>
            <div class="capability-text">上传、同步、编辑简历内容，并形成可持续维护的求职资料。</div>
          </article>
          <article class="capability-card">
            <div class="capability-title">岗位推荐与投递</div>
            <div class="capability-text">查看岗位推荐、执行投递动作、跟进收藏与面试安排。</div>
          </article>
          <article class="capability-card">
            <div class="capability-title">职位发布与人才匹配</div>
            <div class="capability-text">管理招聘职位、筛选候选人，并结合匹配结果推进招聘流程。</div>
          </article>
          <article class="capability-card">
            <div class="capability-title">反馈与流程协同</div>
            <div class="capability-text">处理用户反馈、面试通知、招聘反馈和平台运营动作。</div>
          </article>
        </div>

        <div class="capability-footer">
          <span class="footer-chip">求职资料</span>
          <span class="footer-chip">岗位推荐</span>
          <span class="footer-chip">人才匹配</span>
          <span class="footer-chip">招聘流程</span>
        </div>
      </section>

      <el-card class="auth-card">
        <div class="auth-head">
          <div class="auth-kicker">账号入口</div>
          <div class="auth-title">登录或注册</div>
          <div class="auth-text">登录后自动进入对应角色的工作台。</div>
        </div>

        <el-tabs v-model="activeTab" class="auth-tabs" stretch>
          <el-tab-pane label="账号登录" name="login">
            <div class="tab-panel">
              <el-form :model="loginForm" label-position="top">
                <el-form-item label="用户名">
                  <el-input v-model="loginForm.username" placeholder="请输入用户名" />
                </el-form-item>
                <el-form-item label="密码">
                  <el-input
                    v-model="loginForm.password"
                    type="password"
                    placeholder="请输入密码"
                    show-password
                    @keyup.enter="handleLogin"
                  />
                </el-form-item>
                <el-button class="auth-button primary" type="primary" @click="handleLogin">立即登录</el-button>
              </el-form>
            </div>
          </el-tab-pane>

          <el-tab-pane label="新用户注册" name="register">
            <div class="tab-panel">
              <el-form :model="regForm" label-position="top">
                <el-form-item label="注册身份">
                  <el-radio-group v-model="regForm.role" class="role-group">
                    <el-radio label="seeker">求职者</el-radio>
                    <el-radio label="hr">HR / 企业</el-radio>
                  </el-radio-group>
                </el-form-item>
                <el-form-item label="用户名">
                  <el-input v-model="regForm.username" placeholder="请设置用户名" />
                </el-form-item>
                <el-form-item label="密码">
                  <el-input
                    v-model="regForm.password"
                    type="password"
                    placeholder="请设置密码"
                    show-password
                    @keyup.enter="handleRegister"
                  />
                </el-form-item>
                <el-button class="auth-button secondary" type="primary" @click="handleRegister">提交注册</el-button>
              </el-form>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

const activeTab = ref('login')
const router = useRouter()

const loginForm = ref({ username: '', password: '' })
const regForm = ref({ username: '', password: '', role: 'seeker' })

const handleLogin = async () => {
  try {
    const res = await axios.post('http://127.0.0.1:8000/login', loginForm.value)
    if (res.data.status === 'success') {
      localStorage.setItem('user', JSON.stringify(res.data.user))
      window.dispatchEvent(new Event('storage'))
      ElMessage.success('登录成功')
      if (res.data.user.role === 'seeker') router.push('/resume')
      else if (res.data.user.role === 'hr') router.push('/hr')
      else router.push('/admin')
    }
  } catch (error) {
    ElMessage.error('登录失败，请检查账号密码')
  }
}

const handleRegister = async () => {
  const res = await axios.post('http://127.0.0.1:8000/register', regForm.value)
  if (res.data.status === 'success') {
    ElMessage.success('注册成功，请登录')
    activeTab.value = 'login'
  } else {
    ElMessage.error(res.data.message)
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 20px;
  background:
    radial-gradient(circle at top left, rgba(59, 130, 246, 0.14), transparent 24%),
    radial-gradient(circle at bottom right, rgba(191, 219, 254, 0.45), transparent 30%),
    linear-gradient(180deg, #f4f8fc 0%, #eef4fb 100%);
}

.login-shell {
  width: min(1080px, 100%);
  display: grid;
  grid-template-columns: minmax(0, 1.18fr) 410px;
  gap: 24px;
  align-items: stretch;
}

.capability-panel,
.auth-card {
  border-radius: 28px;
  border: 1px solid #dbe7f3;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.97) 0%, rgba(248, 251, 255, 0.97) 100%);
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.08);
}

.capability-panel {
  padding: 30px;
  display: flex;
  flex-direction: column;
}

.panel-kicker {
  display: inline-flex;
  width: fit-content;
  padding: 8px 14px;
  border-radius: 999px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.capability-panel h1 {
  margin: 22px 0 12px;
  color: #0f172a;
  font-size: 36px;
  line-height: 1.1;
}

.panel-subtitle {
  margin: 0;
  color: #64748b;
  font-size: 15px;
  line-height: 1.8;
}

.capability-grid {
  margin-top: 24px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.capability-card {
  padding: 20px;
  border-radius: 22px;
  border: 1px solid #dbe7f3;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
}

.capability-title {
  color: #0f172a;
  font-size: 18px;
  font-weight: 700;
}

.capability-text {
  margin-top: 10px;
  color: #475569;
  line-height: 1.8;
  font-size: 14px;
}

.capability-footer {
  margin-top: auto;
  padding-top: 18px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.footer-chip {
  padding: 10px 14px;
  border-radius: 14px;
  background: #f8fbff;
  border: 1px solid #dbe7f3;
  color: #334155;
  font-size: 13px;
  font-weight: 600;
}

.auth-card {
  padding: 10px;
}

.auth-head {
  padding-bottom: 8px;
}

.auth-kicker {
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.auth-title {
  margin-top: 12px;
  color: #0f172a;
  font-size: 28px;
  font-weight: 700;
}

.auth-text {
  margin-top: 10px;
  color: #64748b;
  font-size: 14px;
  line-height: 1.7;
}

.tab-panel {
  margin-top: 10px;
  padding: 18px;
  border-radius: 20px;
  border: 1px solid #dbe7f3;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
}

.auth-button {
  width: 100%;
  height: 44px;
  margin-top: 8px;
  border-radius: 14px;
  font-weight: 700;
}

.auth-button.primary {
  background: #2563eb !important;
  border-color: #2563eb !important;
}

.auth-button.primary:hover {
  background: #1d4ed8 !important;
  border-color: #1d4ed8 !important;
}

.auth-button.secondary {
  background: #2563eb !important;
  border-color: #2563eb !important;
}

.auth-button.secondary:hover {
  background: #1d4ed8 !important;
  border-color: #1d4ed8 !important;
}

.role-group {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  flex-wrap: nowrap;
  gap: 10px;
}

.role-group :deep(.el-radio) {
  flex: 1;
}

:deep(.el-card__body) {
  padding: 26px;
}

:deep(.el-tabs__header) {
  margin-bottom: 8px;
}

:deep(.el-tabs__item) {
  font-weight: 700;
}

:deep(.el-tabs__item.is-active) {
  color: #2563eb !important;
}

:deep(.el-tabs__active-bar) {
  background-color: #2563eb !important;
}

:deep(.el-form-item__label) {
  color: #334155 !important;
  font-weight: 600;
}

:deep(.el-input__wrapper) {
  min-height: 44px;
  border-radius: 14px;
  box-shadow: 0 0 0 1px #dbe7f3 inset !important;
  background: rgba(255, 255, 255, 0.95);
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #2563eb inset !important;
}

:deep(.el-radio) {
  margin-right: 0;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid #dbe7f3;
  background: #ffffff;
}

:deep(.el-radio__input.is-checked .el-radio__inner) {
  background-color: #2563eb !important;
  border-color: #2563eb !important;
}

:deep(.el-radio__input.is-checked + .el-radio__label) {
  color: #1d4ed8 !important;
}

@media (max-width: 980px) {
  .login-shell {
    grid-template-columns: 1fr;
  }

  .capability-grid {
    grid-template-columns: 1fr;
  }

  .capability-panel h1 {
    font-size: 30px;
  }
}

@media (max-width: 640px) {
  .login-container {
    padding: 20px 14px;
  }

  .capability-panel,
  .auth-card {
    border-radius: 22px;
  }

  .capability-panel {
    padding: 22px;
  }

  .tab-panel {
    padding: 16px;
  }

  .role-group {
    flex-direction: column;
  }

  :deep(.el-card__body) {
    padding: 20px;
  }
}
</style>
