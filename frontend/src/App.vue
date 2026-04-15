<template>
  <el-container v-if="isLoggedIn" class="layout-container">
    <el-aside width="228px" class="aside">
      <div class="brand-block">
        <div class="brand-kicker">Recruitment OS</div>
        <div class="brand-title">招聘平台总控台</div>
      </div>

      <div class="role-card">
        <div class="role-label">当前身份</div>
        <div class="role-name">{{ roleLabel }}</div>
        <div class="role-desc">{{ roleDescription }}</div>
      </div>

      <el-menu
        :default-active="route.path"
        router
        class="main-menu"
        background-color="transparent"
        text-color="#d7deea"
        active-text-color="#ffffff"
      >
        <el-menu-item v-if="role === 'seeker'" index="/resume">
          <el-icon><User /></el-icon>
          <span>求职工作台</span>
        </el-menu-item>

        <el-menu-item v-if="role === 'seeker'" index="/center">
          <el-icon><Document /></el-icon>
          <span>求职者中心</span>
        </el-menu-item>

        <el-menu-item v-if="role === 'hr'" index="/hr">
          <el-icon><Management /></el-icon>
          <span>招聘控制台</span>
        </el-menu-item>

        <el-menu-item v-if="role === 'admin'" index="/">
          <el-icon><PieChart /></el-icon>
          <span>平台总览</span>
        </el-menu-item>

        <el-menu-item v-if="role === 'admin'" index="/admin">
          <el-icon><Setting /></el-icon>
          <span>运营与实验室</span>
        </el-menu-item>
      </el-menu>

      <div class="capability-card">
        <div class="capability-title">模块看板</div>
        <div v-for="item in capabilityList" :key="item" class="capability-item">
          <span class="capability-dot"></span>
          <span>{{ item }}</span>
        </div>
      </div>

      <el-button class="logout-button" @click="logout">
        <el-icon><SwitchButton /></el-icon>
        退出系统
      </el-button>
    </el-aside>

    <el-container class="content-shell">
      <el-main class="main">
        <router-view v-slot="{ Component }">
          <keep-alive>
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </el-main>
    </el-container>
  </el-container>

  <router-view v-else />
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Document, Management, PieChart, Setting, SwitchButton, User } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const user = ref(JSON.parse(localStorage.getItem('user')))

const updateUserStatus = () => {
  user.value = JSON.parse(localStorage.getItem('user'))
}

const isLoggedIn = computed(() => !!user.value && route.path !== '/login')
const role = computed(() => user.value?.role)

const roleLabel = computed(() => {
  if (role.value === 'seeker') return '求职者'
  if (role.value === 'hr') return '企业 HR'
  if (role.value === 'admin') return '平台管理员'
  return '访客'
})

const roleDescription = computed(() => {
  if (role.value === 'seeker') return '管理求职资料、投递动作和面试进度。'
  if (role.value === 'hr') return '管理职位、候选人和招聘流程。'
  if (role.value === 'admin') return '维护平台运营能力和算法工具。'
  return '请先登录。'
})

const capabilityList = computed(() => {
  if (role.value === 'seeker') return ['求职资料管理', '岗位机会浏览', '投递与收藏', '面试与反馈']
  if (role.value === 'hr') return ['职位发布维护', '人才匹配排序', '申请处理', '招聘沟通协作']
  if (role.value === 'admin') return ['平台监控', '公告与反馈', '词库维护', '算法实验']
  return []
})

const logout = () => {
  localStorage.removeItem('user')
  user.value = null
  router.push('/login')
}

onMounted(() => {
  window.addEventListener('storage', updateUserStatus)
})

onUnmounted(() => {
  window.removeEventListener('storage', updateUserStatus)
})
</script>

<style>
.layout-container {
  height: 100vh;
  background: #eef2f7;
}

.aside {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px 14px;
  background: linear-gradient(180deg, #0f172a 0%, #132238 100%);
  color: #fff;
}

.brand-block {
  padding: 4px 8px 0;
}

.brand-kicker {
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #7dd3fc;
  margin-bottom: 8px;
}

.brand-title {
  font-size: 20px;
  font-weight: 700;
  line-height: 1.2;
}

.role-card,
.capability-card {
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(15, 23, 42, 0.38);
  border-radius: 14px;
  padding: 12px;
}

.role-label,
.capability-title {
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 8px;
}

.role-name {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 4px;
}

.role-desc {
  font-size: 12px;
  line-height: 1.5;
  color: #cbd5e1;
}

.main-menu {
  border-right: none;
  background: transparent !important;
}

.main-menu .el-menu-item {
  margin-bottom: 6px;
  border-radius: 10px;
  padding-left: 14px !important;
}

.main-menu .el-menu-item.is-active {
  background: rgba(59, 130, 246, 0.2) !important;
}

.capability-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: #dbe5f4;
  margin-bottom: 8px;
}

.capability-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #38bdf8;
}

.logout-button {
  margin-top: auto;
  justify-content: flex-start;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(148, 163, 184, 0.2);
  color: #ffffff;
}

.logout-button:hover {
  color: #ffffff;
  border-color: rgba(125, 211, 252, 0.4);
  background: rgba(59, 130, 246, 0.16);
}

.content-shell {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.main {
  padding: 16px;
  background-color: transparent;
}

body {
  margin: 0;
}

@media (max-width: 900px) {
  .aside {
    width: 220px !important;
    padding: 16px 12px;
  }

  .main {
    padding: 12px;
  }
}
</style>
