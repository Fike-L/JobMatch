<template>
  <div class="hr-container">
    <div class="hr-shell">
      <aside class="hr-aside">
        <div class="hr-aside-title">招聘功能导航</div>
        <div class="hr-aside-subtitle">把职位、匹配、申请、沟通和反馈拆成清晰的招聘工作模块。</div>

        <el-menu :default-active="activeSection" class="hr-menu" @select="(key) => activeSection = key">
          <el-menu-item index="jobs">
            <el-icon><Suitcase /></el-icon>
            <span>职位管理</span>
          </el-menu-item>
          <el-menu-item index="matching">
            <el-icon><Search /></el-icon>
            <span>人才匹配</span>
          </el-menu-item>
          <el-menu-item index="applicants">
            <el-icon><User /></el-icon>
            <span>候选人申请</span>
          </el-menu-item>
          <el-menu-item index="community">
            <el-icon><ChatDotRound /></el-icon>
            <span>企业交流</span>
          </el-menu-item>
          <el-menu-item index="feedback">
            <el-icon><EditPen /></el-icon>
            <span>反馈管理员</span>
          </el-menu-item>
        </el-menu>
      </aside>

      <div class="hr-main">
        <section v-show="activeSection === 'jobs'" class="hr-panel">
          <div class="toolbar">
            <el-button type="primary" :icon="Plus" @click="openCreateDialog">发布新职位</el-button>
          </div>

          <el-table :data="myJobs" stripe style="width: 100%">
            <el-table-column prop="title" label="职位名称" min-width="150" />
            <el-table-column prop="salary" label="薪资范围" width="120" />
            <el-table-column prop="experience" label="经验要求" width="120" />
            <el-table-column label="操作" width="220" fixed="right">
              <template #default="scope">
                <el-button size="small" :icon="Edit" @click="handleEdit(scope.row)">编辑</el-button>
                <el-button size="small" type="success" :icon="Search" @click="goMatch(scope.row)">人才匹配</el-button>
              </template>
            </el-table-column>
          </el-table>
        </section>

        <section v-show="activeSection === 'matching'" class="hr-panel">
          <el-empty v-if="!activeJob" description="先在职位管理中选择一个职位，再进入人才匹配模块" />
          <template v-else>
            <div class="match-info">
              <el-icon><InfoFilled /></el-icon>
              正在为：<strong>{{ activeJob.title }}</strong> 检索人才库并计算匹配度
            </div>
            <el-table :data="candidates" style="width: 100%">
              <el-table-column prop="name" label="求职者姓名" width="120" />
              <el-table-column label="匹配契合度" width="180">
                <template #default="scope">
                  <el-progress
                    :percentage="scope.row.score"
                    :color="scope.row.score > 80 ? '#67C23A' : '#409EFF'"
                    :stroke-width="10"
                  />
                </template>
              </el-table-column>
              <el-table-column label="命中的核心技能">
                <template #default="scope">
                  <el-tag v-for="s in scope.row.skills" :key="s" size="small" style="margin-right: 5px; margin-bottom: 5px;">
                    {{ s }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120">
                <template #default="scope">
                  <el-button size="small" type="primary" plain @click="viewResume(scope.row)">查看简历</el-button>
                </template>
              </el-table-column>
            </el-table>
          </template>
        </section>

        <section v-show="activeSection === 'applicants'" class="hr-panel">
          <el-table :data="applicants" stripe style="width: 100%">
            <el-table-column prop="real_name" label="求职者姓名" width="120" />
            <el-table-column prop="job_title" label="申请岗位" min-width="150" />
            <el-table-column label="当前状态" width="120">
              <template #default="scope">
                <el-tag :type="getStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="apply_time" label="投递时间" width="160" />
            <el-table-column label="操作" width="350" fixed="right">
              <template #default="scope">
                <el-button size="small" :icon="Document" @click="viewResume(scope.row)">详情</el-button>
                <el-button size="small" type="success" @click="openSchedule(scope.row)">安排面试</el-button>

                <el-dropdown trigger="click" @command="(cmd) => handleIntent(scope.row, cmd)" style="margin-left: 10px">
                  <el-button size="small" type="warning">
                    发送反馈意向<el-icon class="el-icon--right"><ArrowDown /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="邀约面试">邀约面试</el-dropdown-item>
                      <el-dropdown-item command="录用通知">录用通知</el-dropdown-item>
                      <el-dropdown-item command="暂不合适">暂不合适</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </template>
            </el-table-column>
          </el-table>
        </section>

        <section v-show="activeSection === 'community'" class="hr-panel">
          <div class="forum-container">
            <el-input v-model="msgInput" placeholder="在这里分享招聘经验..." @keyup.enter="postMsg">
              <template #append><el-button @click="postMsg">发布</el-button></template>
            </el-input>
            <el-divider />
            <div class="msg-list">
              <div v-for="m in messages" :key="m.id" class="msg-item">
                <div class="msg-header">
                  <strong>{{ m.username }}</strong>
                  <small>{{ m.post_time }}</small>
                </div>
                <p class="msg-content">{{ m.content }}</p>
              </div>
            </div>
          </div>
        </section>

        <section v-show="activeSection === 'feedback'" class="hr-panel">
          <div style="max-width: 600px; padding: 20px;">
            <h3>系统改进建议</h3>
            <el-input type="textarea" v-model="fbInput" :rows="5" placeholder="对平台流程或招聘工具有建议，就写在这里" />
            <el-button type="primary" @click="sendFb" style="margin-top: 15px">提交反馈</el-button>
          </div>
        </section>
      </div>
    </div>

    <el-dialog v-model="scheVisible" title="设定面试时间地点" width="400px">
      <el-form :model="scheForm" label-position="top">
        <el-form-item label="面试时间">
          <el-date-picker
            v-model="scheForm.time"
            type="datetime"
            placeholder="选择日期时间"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="面试地点">
          <el-input v-model="scheForm.location" placeholder="如：腾讯会议号或XX大厦302" />
        </el-form-item>
        <el-form-item label="面试备注">
          <el-input v-model="scheForm.notes" type="textarea" placeholder="请带好作品集..." />
        </el-form-item>
        <el-button type="primary" @click="submitSche" style="width: 100%">确认并通知求职者</el-button>
      </el-form>
    </el-dialog>

    <el-dialog v-model="resumeDialog" title="简历原始信息预览" width="55%">
      <div class="resume-content-box">{{ currentResume }}</div>
    </el-dialog>

    <el-dialog v-model="editDialog" title="修改职位描述信息" width="50%">
      <el-form :model="editForm" label-position="top">
        <el-form-item label="职位标题"><el-input v-model="editForm.title" /></el-form-item>
        <el-form-item label="薪资范围"><el-input v-model="editForm.salary" /></el-form-item>
        <el-form-item label="详细要求 (JD)"><el-input type="textarea" :rows="8" v-model="editForm.description" /></el-form-item>
        <div style="text-align: right;">
          <el-button @click="editDialog = false">取消</el-button>
          <el-button type="primary" @click="submitUpdate">确认保存</el-button>
        </div>
      </el-form>
    </el-dialog>

    <el-dialog v-model="createVisible" title="发布全新招聘需求" width="50%">
      <el-form :model="createForm" label-position="top">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="职位名称"><el-input v-model="createForm.title" placeholder="如：Java工程师" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="薪资范围"><el-input v-model="createForm.salary" placeholder="如：$60K-$100K" /></el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="工作城市"><el-input v-model="createForm.location" placeholder="如：上海、北京、远程" /></el-form-item>
        <el-form-item label="核心技能关键词"><el-input v-model="createForm.skills" placeholder="用逗号分隔" /></el-form-item>
        <el-form-item label="详细职位描述 (JD)"><el-input type="textarea" :rows="6" v-model="createForm.description" /></el-form-item>
        <div style="text-align: right;">
          <el-button @click="createVisible = false">取消</el-button>
          <el-button type="primary" @click="submitCreate">立即发布入库</el-button>
        </div>
      </el-form>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowDown,
  ChatDotRound,
  Document,
  Edit,
  EditPen,
  InfoFilled,
  Plus,
  Search,
  Suitcase,
  User
} from '@element-plus/icons-vue'

const myJobs = ref([])
const activeJob = ref(null)
const candidates = ref([])
const applicants = ref([])
const messages = ref([])

const msgInput = ref('')
const fbInput = ref('')
const resumeDialog = ref(false)
const currentResume = ref('')
const editDialog = ref(false)
const editForm = ref({})
const createVisible = ref(false)
const createForm = ref({ title: '', salary: '', skills: '', description: '', company: '本企业', location: '' })
const scheVisible = ref(false)
const scheForm = ref({ app_id: '', time: '', location: '', notes: '' })
const activeSection = ref('jobs')

const fetchAll = async () => {
  const userStr = localStorage.getItem('user')
  if (!userStr) return
  const user = JSON.parse(userStr)

  try {
    const [resJ, resA] = await Promise.all([
      axios.get(`http://127.0.0.1:8000/hr/my_jobs/${user.id}`),
      axios.get(`http://127.0.0.1:8000/hr/applicants/${user.id}`)
    ])
    myJobs.value = resJ.data.data || []
    applicants.value = resA.data.data || []
  } catch (error) {
    ElMessage.error('获取基础数据失败')
  }
}

const loadForum = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:8000/forum/messages/hr')
    messages.value = res.data.data || []
  } catch (error) {
    console.error('社区加载失败', error)
  }
}

const goMatch = async (job) => {
  activeJob.value = job
  activeSection.value = 'matching'
  try {
    const res = await axios.post('http://127.0.0.1:8000/rank_candidates', {
      description: (job.description || '') + (job.skills || '')
    })
    candidates.value = res.data.results || []
    ElMessage.success('人才画像匹配完成')
  } catch (error) {
    ElMessage.error('算法匹配失败')
  }
}

const handleIntent = (row, command) => {
  ElMessageBox.prompt('请输入反馈留言', `发送“${command}”`, {
    confirmButtonText: '发送',
    cancelButtonText: '取消'
  }).then(async ({ value }) => {
    try {
      await axios.post('http://127.0.0.1:8000/hr/send_intent', {
        action_id: row.action_id,
        status: command,
        feedback: value || '无留言'
      })
      ElMessage.success('反馈已发送')
      fetchAll()
    } catch (error) {
      ElMessage.error('发送失败')
    }
  }).catch(() => {})
}

const openSchedule = (row) => {
  scheForm.value = { app_id: row.action_id, time: '', location: '', notes: '' }
  scheVisible.value = true
}

const submitSche = async () => {
  try {
    await axios.post('http://127.0.0.1:8000/hr/schedule_interview', scheForm.value)
    ElMessage.success('面试日程已设定并通知求职者')
    scheVisible.value = false
    fetchAll()
  } catch (error) {
    ElMessage.error('日程设定失败')
  }
}

const postMsg = async () => {
  if (!msgInput.value.trim()) return
  const user = JSON.parse(localStorage.getItem('user'))
  try {
    await axios.post('http://127.0.0.1:8000/forum/post', {
      role: 'hr',
      user_id: user.id,
      content: msgInput.value
    })
    msgInput.value = ''
    loadForum()
  } catch (error) {
    ElMessage.error('发布失败')
  }
}

const sendFb = async () => {
  if (!fbInput.value.trim()) return
  const user = JSON.parse(localStorage.getItem('user'))
  try {
    await axios.post('http://127.0.0.1:8000/common/submit_feedback', {
      role: 'hr',
      user_id: user.id,
      content: fbInput.value
    })
    ElMessage.success('感谢您的反馈')
    fbInput.value = ''
  } catch (error) {
    ElMessage.error('提交失败')
  }
}

const viewResume = (row) => {
  currentResume.value = row.text || row.raw_text || '内容为空'
  resumeDialog.value = true
}

const handleEdit = (job) => {
  editForm.value = { ...job }
  editDialog.value = true
}

const submitUpdate = async () => {
  await axios.post('http://127.0.0.1:8000/hr/job/update', editForm.value)
  ElMessage.success('更新成功')
  editDialog.value = false
  fetchAll()
}

const openCreateDialog = () => {
  createVisible.value = true
}

const submitCreate = async () => {
  const user = JSON.parse(localStorage.getItem('user'))
  await axios.post('http://127.0.0.1:8000/hr/job/create', { ...createForm.value, hr_id: user.id })
  ElMessage.success('发布成功')
  createVisible.value = false
  fetchAll()
}

const getStatusType = (status) => {
  const map = { '邀约面试': 'success', '录用通知': 'success', '暂不合适': 'danger' }
  return map[status] || 'info'
}

onMounted(() => {
  fetchAll()
  loadForum()
})
</script>

<style scoped>
.hr-container {
  min-height: calc(100vh - 140px);
}

.hr-shell {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 20px;
}

.hr-aside {
  padding: 22px;
  border-radius: 24px;
  background: #ffffff;
  border: 1px solid #dbe7f3;
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.06);
}

.hr-aside-title {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
}

.hr-aside-subtitle {
  margin-top: 10px;
  color: #64748b;
  font-size: 14px;
  line-height: 1.6;
}

.hr-menu {
  margin-top: 18px;
  border-right: none;
}

.hr-menu :deep(.el-menu-item) {
  height: 52px;
  margin-bottom: 8px;
  border-radius: 14px;
}

.hr-menu :deep(.el-menu-item.is-active) {
  background: #0f172a;
  color: #ffffff;
}

.hr-main {
  min-width: 0;
}

.hr-panel {
  background: #ffffff;
  border-radius: 24px;
  border: 1px solid #dbe7f3;
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.06);
  padding: 20px;
}

.toolbar {
  margin-bottom: 15px;
  text-align: right;
}

.match-info {
  padding: 15px;
  background: #eef5fe;
  border-left: 5px solid #409eff;
  margin-bottom: 15px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.resume-content-box {
  white-space: pre-wrap;
  background: #2b2f3a;
  color: #fff;
  padding: 25px;
  border-radius: 8px;
  font-family: monospace;
  line-height: 1.6;
  max-height: 500px;
  overflow-y: auto;
}

.forum-container {
  padding: 10px;
}

.msg-list {
  margin-top: 20px;
  max-height: 600px;
  overflow-y: auto;
}

.msg-item {
  padding: 15px;
  border-bottom: 1px solid #eee;
  transition: background 0.3s;
}

.msg-item:hover {
  background: #fafafa;
}

.msg-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.msg-header small {
  color: #999;
}

.msg-content {
  margin: 0;
  color: #444;
  line-height: 1.5;
}

@media (max-width: 1100px) {
  .hr-shell {
    grid-template-columns: 1fr;
  }
}
</style>
