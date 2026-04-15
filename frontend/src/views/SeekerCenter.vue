<template>
  <div class="seeker-center">
    <div class="center-shell">
      <aside class="center-aside">
        <div class="center-title">求职者功能区</div>
        <div class="center-subtitle">把投递、收藏、面试、互动和反馈集中到同一张侧栏里。</div>

        <el-menu :default-active="activeSection" class="center-menu" @select="(key) => activeSection = key">
          <el-menu-item index="announcements">
            <el-icon><Bell /></el-icon>
            <span>平台公告</span>
          </el-menu-item>
          <el-menu-item index="applications">
            <el-icon><Briefcase /></el-icon>
            <span>投递进度</span>
          </el-menu-item>
          <el-menu-item index="interviews">
            <el-icon><Calendar /></el-icon>
            <span>面试日程</span>
          </el-menu-item>
          <el-menu-item index="favorites">
            <el-icon><Star /></el-icon>
            <span>职位收藏</span>
          </el-menu-item>
          <el-menu-item index="community">
            <el-icon><ChatDotRound /></el-icon>
            <span>求职交流</span>
          </el-menu-item>
          <el-menu-item index="feedback">
            <el-icon><EditPen /></el-icon>
            <span>意见反馈</span>
          </el-menu-item>
        </el-menu>
      </aside>

      <div class="center-main">
        <section v-show="activeSection === 'announcements'" class="center-panel">
          <el-card header="平台公告">
            <el-alert
              v-for="a in annos"
              :key="a.id"
              :title="a.title"
              type="warning"
              :description="a.content"
              show-icon
              class="panel-alert"
            />
            <el-empty v-if="!annos.length" description="暂无公告" />
          </el-card>
        </section>

        <section v-show="activeSection === 'applications'" class="center-panel">
          <el-card header="我的投递进度">
            <el-table :data="apps" stripe border>
              <el-table-column prop="title" label="投递岗位" />
              <el-table-column prop="company" label="公司" />
              <el-table-column label="状态">
                <template #default="scope">
                  <el-tag :type="scope.row.status === '邀约面试' ? 'success' : 'info'">{{ scope.row.status }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="feedback" label="HR 反馈" show-overflow-tooltip>
                <template #default="scope">
                  <span class="highlight-text">{{ scope.row.feedback || '等待处理...' }}</span>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </section>

        <section v-show="activeSection === 'interviews'" class="center-panel">
          <el-card header="面试日程表">
            <el-table :data="interviews" stripe border>
              <el-table-column prop="title" label="岗位" />
              <el-table-column prop="Company" label="公司" />
              <el-table-column prop="interview_time" label="面试时间" width="180" />
              <el-table-column prop="location" label="地点" />
              <el-table-column prop="notes" label="HR 备注" />
            </el-table>
          </el-card>
        </section>

        <section v-show="activeSection === 'favorites'" class="center-panel">
          <el-card header="职位收藏夹">
            <el-table :data="favs" stripe border>
              <el-table-column prop="title" label="职位名称" />
              <el-table-column prop="company" label="公司" />
              <el-table-column prop="salary" label="薪资" />
              <el-table-column label="操作" width="200">
                <template #default="scope">
                  <el-button type="primary" size="small" @click="goApply(scope.row)">现在投递</el-button>
                  <el-button type="danger" size="small" plain @click="cancelFav(scope.row)">取消收藏</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </section>

        <section v-show="activeSection === 'community'" class="center-panel">
          <el-card header="求职交流区">
            <div class="forum-container">
              <el-input v-model="msgInput" placeholder="在这里交流求职经验..." @keyup.enter="postMsg">
                <template #append><el-button @click="postMsg">发送</el-button></template>
              </el-input>
              <el-divider />
              <div v-for="m in messages" :key="m.id" class="msg-item">
                <strong>{{ m.username }}</strong> <small>{{ m.post_time }}</small>
                <p>{{ m.content }}</p>
              </div>
            </div>
          </el-card>
        </section>

        <section v-show="activeSection === 'feedback'" class="center-panel">
          <el-card header="意见反馈">
            <el-input type="textarea" v-model="fbInput" :rows="5" placeholder="写下你对平台流程、体验或功能的建议" />
            <el-button type="primary" @click="sendFb" style="margin-top: 12px">提交反馈</el-button>
          </el-card>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Bell, Briefcase, Calendar, ChatDotRound, EditPen, Star } from '@element-plus/icons-vue'

const apps = ref([])
const favs = ref([])
const annos = ref([])
const interviews = ref([])
const messages = ref([])
const msgInput = ref('')
const fbInput = ref('')
const activeSection = ref('applications')

const fetchData = async () => {
  const userStr = localStorage.getItem('user')
  if (!userStr) return
  const user = JSON.parse(userStr)

  try {
    const resApp = await axios.get(`http://127.0.0.1:8000/seeker/applications/${user.id}`)
    apps.value = resApp.data.data || []

    const resFav = await axios.get(`http://127.0.0.1:8000/seeker/favorites/${user.id}`)
    favs.value = (resFav.data.data || []).map((item) => ({
      id: item['Job Id'],
      title: item['Job Title'],
      company: item.Company,
      salary: item['Salary Range']
    }))

    const resAnno = await axios.get('http://127.0.0.1:8000/common/announcements')
    annos.value = resAnno.data.data || []

    const resInt = await axios.get(`http://127.0.0.1:8000/seeker/interviews/${user.id}`)
    interviews.value = resInt.data.data || []

    const resMsg = await axios.get('http://127.0.0.1:8000/forum/messages/seeker')
    messages.value = resMsg.data.data || []
  } catch (error) {
    console.error(error)
    ElMessage.error('数据加载失败，请检查网络或登录状态')
  }
}

const cancelFav = async (job) => {
  const user = JSON.parse(localStorage.getItem('user'))
  await axios.post('http://127.0.0.1:8000/unfavorite_job', {
    user_id: user.id,
    job_id: job.id
  })
  ElMessage.success('已取消收藏')
  fetchData()
}

const goApply = async (job) => {
  const user = JSON.parse(localStorage.getItem('user'))
  const res = await axios.post('http://127.0.0.1:8000/apply_job', {
    user_id: user.id,
    job_id: job.id
  })
  if (res.data.status === 'success') {
    ElMessage.success('投递成功')
    fetchData()
  }
}

const postMsg = async () => {
  if (!msgInput.value.trim()) return
  const user = JSON.parse(localStorage.getItem('user'))
  await axios.post('http://127.0.0.1:8000/forum/post', {
    role: 'seeker',
    user_id: user.id,
    content: msgInput.value
  })
  msgInput.value = ''
  fetchData()
}

const sendFb = async () => {
  if (!fbInput.value.trim()) return
  const user = JSON.parse(localStorage.getItem('user'))
  await axios.post('http://127.0.0.1:8000/common/submit_feedback', {
    role: 'seeker',
    user_id: user.id,
    content: fbInput.value
  })
  ElMessage.success('反馈成功，感谢您的建议')
  fbInput.value = ''
}

onMounted(fetchData)
</script>

<style scoped>
.seeker-center {
  min-height: calc(100vh - 140px);
}

.center-shell {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 20px;
}

.center-aside {
  border-radius: 24px;
  padding: 22px;
  background: #ffffff;
  border: 1px solid #dbe7f3;
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.06);
}

.center-title {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
}

.center-subtitle {
  margin-top: 10px;
  color: #64748b;
  font-size: 14px;
  line-height: 1.6;
}

.center-menu {
  margin-top: 18px;
  border-right: none;
}

.center-menu :deep(.el-menu-item) {
  height: 52px;
  margin-bottom: 8px;
  border-radius: 14px;
}

.center-menu :deep(.el-menu-item.is-active) {
  background: #0f172a;
  color: #ffffff;
}

.center-main {
  min-width: 0;
}

.center-panel {
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  border-radius: 24px;
  border: 1px solid #dbe7f3;
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.06);
  padding: 22px;
}

.panel-alert {
  margin-bottom: 12px;
}

.highlight-text {
  color: #2563eb;
}

.forum-container {
  max-height: 500px;
  overflow-y: auto;
  padding: 10px;
}

.msg-item {
  background: #f9f9f9;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 10px;
  border-left: 4px solid #409eff;
}

.msg-item strong {
  color: #409eff;
}

.msg-item small {
  color: #999;
  margin-left: 10px;
}

.msg-item p {
  margin: 8px 0 0;
  line-height: 1.6;
  color: #333;
}

.center-main :deep(.el-card) {
  border-radius: 20px;
  border: 1px solid #dbe7f3;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.05);
}

.center-main :deep(.el-card__header) {
  padding: 18px 20px;
  border-bottom: 1px solid #e2e8f0;
  color: #0f172a;
  font-weight: 700;
}

.center-main :deep(.el-card__body) {
  padding: 20px;
}

.center-main :deep(.el-table) {
  --el-table-border-color: #dbe7f3;
  --el-table-header-bg-color: #f6faff;
  --el-table-row-hover-bg-color: #f8fbff;
  border: 1px solid #dbe7f3;
  border-radius: 18px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.92);
}

.center-main :deep(.el-table th.el-table__cell) {
  color: #64748b;
  font-weight: 700;
  background: #f6faff;
}

.center-main :deep(.el-button) {
  border-radius: 12px;
}

.center-main :deep(.el-input__wrapper),
.center-main :deep(.el-textarea__inner) {
  border-radius: 14px;
  box-shadow: 0 0 0 1px #dbe7f3 inset;
}

@media (max-width: 1100px) {
  .center-shell {
    grid-template-columns: 1fr;
  }
}
</style>
