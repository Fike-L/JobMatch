<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2>智能招聘平台</h2>
      <p class="login-subtitle">从求职、招聘到平台运营，统一进入同一套招聘软件工作台。</p>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="账号登录" name="login">
          <el-form :model="loginForm" label-position="top">
            <el-form-item label="用户名">
              <el-input v-model="loginForm.username" placeholder="请输入用户名" />
            </el-form-item>
            <el-form-item label="密码">
              <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" />
            </el-form-item>
            <el-button class="btn-primary" type="primary" style="width: 100%" @click="handleLogin">立即登录</el-button>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="新用户注册" name="register">
          <el-form :model="regForm" label-position="top">
            <el-form-item label="选择角色">
              <el-radio-group v-model="regForm.role">
                <el-radio label="seeker">我是求职者</el-radio>
                <el-radio label="hr">我是HR/企业</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="用户名">
              <el-input v-model="regForm.username" />
            </el-form-item>
            <el-form-item label="密码">
              <el-input v-model="regForm.password" type="password" />
            </el-form-item>
            <el-button class="btn-register" type="success" style="width: 100%" @click="handleRegister">提交注册</el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
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
      else router.push('/')
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
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f9fafb;
  background-image: radial-gradient(#e5e7eb 0.7px, transparent 0.7px);
  background-size: 20px 20px;
}

.login-card {
  width: 420px;
  padding: 10px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
}

h2 {
  text-align: center;
  color: #111827;
  font-weight: 600;
  margin-bottom: 10px;
  letter-spacing: -0.5px;
}

.login-subtitle {
  margin: 0 0 24px;
  text-align: center;
  color: #6b7280;
  line-height: 1.6;
  font-size: 14px;
}

:deep(.el-tabs__item.is-active) {
  color: #374151 !important;
}

:deep(.el-tabs__active-bar) {
  background-color: #374151 !important;
}

.btn-primary {
  background-color: #1f2937 !important;
  border-color: #1f2937 !important;
  font-weight: 500;
}

.btn-primary:hover {
  background-color: #374151 !important;
  border-color: #374151 !important;
}

.btn-register {
  background-color: #5b7c7d !important;
  border-color: #5b7c7d !important;
}

.btn-register:hover {
  background-color: #6b8e8f !important;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #374151 inset !important;
}

:deep(.el-radio__input.is-checked .el-radio__inner) {
  background-color: #374151 !important;
  border-color: #374151 !important;
}

:deep(.el-radio__input.is-checked + .el-radio__label) {
  color: #374151 !important;
}
</style>
