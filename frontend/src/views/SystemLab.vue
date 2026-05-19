<template>
  <div class="dashboard-container">
    <div class="lab-shell">
      <aside class="lab-aside">
        <div class="lab-title">管理后台</div>
        <div class="lab-subtitle">公告、反馈、词库、词云和算法配置集中处理。</div>

        <el-menu :default-active="activeSection" class="lab-menu" @select="handleSectionChange">
          <el-menu-item index="overview">
            <el-icon><Grid /></el-icon>
            <span>平台总览</span>
          </el-menu-item>
          <el-menu-item index="announcements">
            <el-icon><Bell /></el-icon>
            <span>公告发布</span>
          </el-menu-item>
          <el-menu-item index="feedbacks">
            <el-icon><MessageBox /></el-icon>
            <span>用户反馈</span>
          </el-menu-item>
          <el-menu-item index="weights">
            <el-icon><DataLine /></el-icon>
            <span>权重配置</span>
          </el-menu-item>
          <el-menu-item index="dictionary">
            <el-icon><Collection /></el-icon>
            <span>技能词库</span>
          </el-menu-item>
          <el-menu-item index="wordcloud">
            <el-icon><Collection /></el-icon>
            <span>技能词云</span>
          </el-menu-item>
          <el-menu-item index="sandbox">
            <el-icon><Cpu /></el-icon>
            <span>算法验证</span>
          </el-menu-item>
        </el-menu>
      </aside>

      <div class="lab-main">
        <section v-show="activeSection === 'overview'" class="lab-panel">
          <el-card class="overview-head">
            <div class="overview-head-content">
              <div>
                <div class="overview-kicker">平台总览</div>
                <div class="overview-head-title">查看平台运行状态与最近用户操作</div>
              </div>
              <el-button type="primary" @click="activeSection = 'announcements'">发布公告</el-button>
            </div>
          </el-card>

          <el-row :gutter="18">
            <el-col v-for="item in stats" :key="item.title" :span="6">
              <el-card shadow="hover" class="stat-card">
                <div class="stat-content">
                  <el-icon :size="38" :color="item.color">
                    <component :is="item.icon" />
                  </el-icon>
                  <div class="stat-text">
                    <div class="stat-title">{{ item.title }}</div>
                    <div class="stat-value">{{ item.value }}</div>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>

          <el-row :gutter="18" style="margin-top: 18px;">
            <el-col :span="24">
              <el-card header="最近用户操作">
                <el-table :data="logs" size="small" height="340">
                  <el-table-column prop="username" label="用户" width="120" />
                  <el-table-column label="动作" width="140">
                    <template #default="{ row }">
                      <el-tag :type="logType(row.action_type)" effect="light">{{ formatAction(row.action_type) }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="action_time" label="时间" />
                </el-table>
              </el-card>
            </el-col>
          </el-row>
        </section>

        <section v-show="activeSection === 'announcements'" class="lab-panel">
          <el-card header="公告发布">
            <el-form :model="annoForm" label-position="top">
              <el-form-item label="公告标题">
                <el-input v-model="annoForm.title" />
              </el-form-item>
              <el-form-item label="公告内容">
                <el-input v-model="annoForm.content" type="textarea" :rows="5" />
              </el-form-item>
              <el-button type="primary" @click="submitAnno">立即推送</el-button>
            </el-form>
          </el-card>
        </section>

        <section v-show="activeSection === 'feedbacks'" class="lab-panel">
          <el-card header="用户反馈">
            <div class="section-toolbar">
              <el-button type="warning" @click="loadFeedbacks">刷新反馈数据</el-button>
            </div>
            <el-tabs>
              <el-tab-pane label="求职者反馈">
                <el-table :data="seekerFbs" stripe height="320">
                  <el-table-column prop="username" label="用户" width="120" />
                  <el-table-column prop="content" label="反馈内容" />
                  <el-table-column prop="submit_time" label="时间" width="180" />
                </el-table>
              </el-tab-pane>
              <el-tab-pane label="HR 反馈">
                <el-table :data="hrFbs" stripe height="320">
                  <el-table-column prop="username" label="用户" width="120" />
                  <el-table-column prop="content" label="反馈内容" />
                  <el-table-column prop="submit_time" label="时间" width="180" />
                </el-table>
              </el-tab-pane>
            </el-tabs>
          </el-card>
        </section>

        <section v-show="activeSection === 'weights'" class="lab-panel">
          <el-card shadow="hover" header="匹配权重配置">
            <div class="weight-item">
              <span>技能匹配权重（{{ weights.skill }}%）</span>
              <el-slider v-model="weights.skill" :step="10" show-stops @change="handleWeightChange" />
            </div>
            <div class="weight-item">
              <span>语义相似度权重（{{ weights.semantic }}%）</span>
              <el-slider v-model="weights.semantic" :step="10" show-stops @change="handleWeightChange" />
            </div>
            <el-alert
              style="margin-top: 15px"
              title="权重调整会影响岗位推荐和人才匹配结果。"
              type="warning"
              show-icon
              :closable="false"
            />
          </el-card>
        </section>

        <section v-show="activeSection === 'dictionary'" class="lab-panel">
          <el-card header="技能词库管理" shadow="hover">
            <div class="dictionary-toolbar">
              <el-input v-model="newSkill.name" placeholder="输入技能名称" size="small" style="width: 180px" />
              <el-select v-model="newSkill.category" placeholder="选择分类" size="small" style="width: 150px">
                <el-option label="IT" value="IT" />
                <el-option label="财务" value="财务" />
                <el-option label="人力资源" value="人力资源" />
                <el-option label="行政" value="行政" />
                <el-option label="营销" value="营销" />
                <el-option label="供应链" value="供应链" />
                <el-option label="法务" value="法务" />
                <el-option label="软技能" value="软技能" />
              </el-select>
              <el-button type="primary" size="small" @click="handleAddSkill">添加</el-button>
            </div>

            <el-table :data="dictionary" size="small" height="500">
              <el-table-column prop="term" label="技能词" />
              <el-table-column prop="category" label="分类" width="120" />
              <el-table-column label="操作" width="90">
                <template #default="{ row }">
                  <el-button type="danger" link size="small" @click="handleDelSkill(row.term)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </section>

        <section v-show="activeSection === 'wordcloud'" class="lab-panel">
          <el-card shadow="hover">
            <template #header>
              <div class="cloud-header">
                <div>
                  <div class="cloud-kicker">技能热度</div>
                  <div class="cloud-title">技能词云</div>
                </div>
                <el-tag type="primary" effect="plain">{{ wordCloudData.length }} 个词</el-tag>
              </div>
            </template>

            <div class="cloud-note">基于词库和岗位数据生成静态词云图，便于查看当前平台高频技能分布。</div>
            <div class="wordcloud-chart">
              <img v-if="wordCloudImageUrl" :src="wordCloudImageUrl" alt="技能词云图" class="wordcloud-image" />
              <el-empty v-else description="暂无词云数据" :image-size="64" />
            </div>

            <div class="top-terms">
              <div class="top-terms-title">高频技能</div>
              <div v-for="item in topWordCloudTerms" :key="item.name" class="top-term-row">
                <span>{{ item.name }}</span>
                <strong>{{ item.value }}</strong>
              </div>
            </div>
          </el-card>
        </section>

        <section v-show="activeSection === 'sandbox'" class="lab-panel">
          <el-card shadow="hover">
            <template #header>
              <div class="card-header">
                <span>即时算法验证</span>
                <el-tag type="danger">Scikit-learn / TF-IDF</el-tag>
              </div>
            </template>

            <el-row :gutter="10">
              <el-col :md="11" :span="24">
                <div class="label">测试简历片段</div>
                <el-input
                  v-model="valData.resumeText"
                  type="textarea"
                  :rows="12"
                  placeholder="输入简历中的技能、项目经历或自我介绍"
                />
              </el-col>
              <el-col :md="2" :span="24" class="vs-icon">VS</el-col>
              <el-col :md="11" :span="24">
                <div class="label">测试岗位描述</div>
                <el-input
                  v-model="valData.jdText"
                  type="textarea"
                  :rows="12"
                  placeholder="输入岗位职责、任职要求或技能要求"
                />
              </el-col>
            </el-row>

            <div class="result-area">
              <div class="score-display">
                <p>语义相似度</p>
                <h2>{{ similarityScore }}</h2>
              </div>
              <el-button type="primary" size="large" :loading="loading" @click="calculateSim">
                立即计算
              </el-button>
            </div>
          </el-card>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Bell, Briefcase, Check, Collection, Cpu, DataLine, Grid, MessageBox, Timer, User } from '@element-plus/icons-vue'

const API_BASE = 'http://127.0.0.1:8000'

const weights = ref({ skill: 70, semantic: 30 })
const dictionary = ref([])
const wordCloudData = ref([])
const newSkill = ref({ name: '', category: 'IT' })
const valData = ref({ resumeText: '', jdText: '' })
const similarityScore = ref('0.00')
const loading = ref(false)
const activeSection = ref('overview')
const stats = ref([])
const logs = ref([])
const annoForm = ref({ title: '', content: '' })
const seekerFbs = ref([])
const hrFbs = ref([])
const wordCloudImageUrl = ref('')

const iconMap = { User, Timer, Check, Briefcase }
const topWordCloudTerms = computed(() => wordCloudData.value.slice(0, 6))

const normalizeStats = (items = []) => items.map((item) => ({
  ...item,
  icon: typeof item.icon === 'string' ? (iconMap[item.icon] || User) : (item.icon || User)
}))

const handleSectionChange = (key) => {
  activeSection.value = key
}

const formatAction = (type) => {
  const map = {
    login: '登录',
    save_resume: '保存简历',
    apply: '投递岗位',
    favorite_job: '收藏岗位'
  }
  return map[type] || type
}

const logType = (type) => {
  if (type === 'apply') return 'success'
  if (type === 'save_resume') return 'warning'
  if (type === 'login') return 'primary'
  return 'info'
}

const submitAnno = async () => {
  try {
    await axios.post(`${API_BASE}/admin/announcements/post`, annoForm.value)
    ElMessage.success('公告已发布')
    annoForm.value = { title: '', content: '' }
  } catch {
    ElMessage.error('发布公告失败')
  }
}

const loadFeedbacks = async () => {
  try {
    const res = await axios.get(`${API_BASE}/admin/all_feedbacks`)
    seekerFbs.value = res.data.seeker_fb || []
    hrFbs.value = res.data.hr_fb || []
  } catch {
    ElMessage.error('获取反馈失败')
  }
}

const fetchStats = async () => {
  try {
    const res = await axios.get(`${API_BASE}/system_stats`)
    if (res.data.status === 'success') {
      stats.value = normalizeStats(res.data.stats || [])
      logs.value = res.data.logs || []
    }
  } catch {
    stats.value = [
      { title: '用户总量', value: '-', icon: User, color: '#2563eb' },
      { title: '今日活跃', value: '-', icon: Timer, color: '#16a34a' },
      { title: '申请总数', value: '-', icon: Check, color: '#ea580c' },
      { title: '系统岗位数', value: '-', icon: Briefcase, color: '#dc2626' }
    ]
  }
}

const fetchDict = async () => {
  try {
    const res = await axios.get(`${API_BASE}/get_dictionary`)
    dictionary.value = res.data.data || []
  } catch {
    ElMessage.error('获取词库失败')
  }
}

const refreshWordCloudImage = () => {
  wordCloudImageUrl.value = `${API_BASE}/admin/dictionary_wordcloud_image?t=${Date.now()}`
}

const fetchWordCloud = async () => {
  try {
    const res = await axios.get(`${API_BASE}/admin/dictionary_wordcloud`)
    wordCloudData.value = res.data.data || []
    refreshWordCloudImage()
  } catch {
    ElMessage.error('获取词云失败')
  }
}

const handleWeightChange = async () => {
  weights.value.semantic = 100 - weights.value.skill
  try {
    const res = await axios.post(`${API_BASE}/update_algorithm_weights`, {
      skill: weights.value.skill,
      semantic: weights.value.semantic
    })
    if (res.data.status === 'success') {
      ElMessage.success('权重已更新')
      if (valData.value.resumeText && valData.value.jdText) calculateSim()
    }
  } catch {
    ElMessage.error('同步权重失败')
  }
}

const calculateSim = async () => {
  if (!valData.value.resumeText || !valData.value.jdText) {
    ElMessage.warning('请先输入要对比的文本')
    return
  }

  loading.value = true
  try {
    const res = await axios.post(`${API_BASE}/calculate_instant_sim`, valData.value)
    similarityScore.value = res.data.score
    ElMessage.success('计算完成')
  } catch {
    ElMessage.error('计算失败')
  } finally {
    loading.value = false
  }
}

const handleAddSkill = async () => {
  if (!newSkill.value.name) {
    ElMessage.warning('请输入技能名称')
    return
  }

  try {
    const res = await axios.post(`${API_BASE}/admin/skills/add`, newSkill.value)
    if (res.data.status === 'success') {
      ElMessage.success('词库已更新')
      newSkill.value.name = ''
      await fetchDict()
      await fetchWordCloud()
    } else {
      ElMessage.error(res.data.message)
    }
  } catch {
    ElMessage.error('添加技能失败')
  }
}

const handleDelSkill = (name) => {
  ElMessageBox.confirm(`确定从词库中删除“${name}”吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await axios.post(`${API_BASE}/admin/skills/delete`, { name })
      ElMessage.success('已删除')
      await fetchDict()
      await fetchWordCloud()
    } catch {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

watch(activeSection, (value) => {
  if (value === 'wordcloud') {
    refreshWordCloudImage()
  }
})

onMounted(async () => {
  await Promise.all([fetchStats(), fetchDict(), fetchWordCloud()])
})

</script>

<style scoped>
.dashboard-container {
  min-height: calc(100vh - 140px);
}

.lab-shell {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 20px;
}

.lab-aside {
  padding: 22px;
  border-radius: 24px;
  background: #ffffff;
  border: 1px solid #dbe7f3;
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.06);
}

.lab-title {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
}

.lab-subtitle,
.cloud-note {
  margin-top: 10px;
  color: #64748b;
  font-size: 14px;
  line-height: 1.7;
}

.lab-menu {
  margin-top: 18px;
  border-right: none;
}

.lab-menu :deep(.el-menu-item) {
  height: 52px;
  margin-bottom: 8px;
  border-radius: 14px;
}

.lab-menu :deep(.el-menu-item.is-active) {
  background: #0f172a;
  color: #ffffff;
}

.lab-main {
  min-width: 0;
}

.lab-panel {
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  border-radius: 24px;
  border: 1px solid #dbe7f3;
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.06);
  padding: 22px;
}

.overview-head {
  margin-bottom: 18px;
}

.overview-head-content,
.stat-content,
.card-header,
.cloud-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.overview-kicker,
.cloud-kicker {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 6px;
}

.overview-head-title,
.cloud-title {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
}

.stat-card {
  margin-bottom: 18px;
}

.stat-text {
  margin-left: 14px;
}

.stat-title,
.label,
.top-terms-title {
  color: #64748b;
  font-size: 13px;
  font-weight: 700;
}

.stat-value {
  margin-top: 6px;
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
}

.section-toolbar,
.dictionary-toolbar {
  margin-bottom: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.wordcloud-chart {
  height: 360px;
  margin-top: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 20px;
  border: 1px solid #dbe7f3;
  background:
    radial-gradient(circle at 24% 20%, rgba(191, 219, 254, 0.78), transparent 28%),
    radial-gradient(circle at 80% 24%, rgba(186, 230, 253, 0.9), transparent 26%),
    linear-gradient(180deg, #f9fbff 0%, #eef5ff 100%);
}

.wordcloud-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.top-terms {
  margin-top: 16px;
}

.top-term-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px dashed #dbe7f3;
  color: #334155;
}

.weight-item {
  margin-bottom: 30px;
}

.weight-item span {
  display: block;
  margin-bottom: 12px;
  color: #475569;
  font-weight: 700;
}

.vs-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100%;
  color: #94a3b8;
  font-weight: 700;
}

.result-area {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px dashed #dbe7f3;
  text-align: center;
}

.score-display h2 {
  margin: 10px 0;
  font-size: 52px;
  color: #2563eb;
}

.lab-main :deep(.el-card) {
  border-radius: 20px;
  border: 1px solid #dbe7f3;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.05);
}

.lab-main :deep(.el-card__header) {
  padding: 18px 20px;
  border-bottom: 1px solid #e2e8f0;
  color: #0f172a;
  font-weight: 700;
}

.lab-main :deep(.el-card__body) {
  padding: 20px;
}

.lab-main :deep(.el-table) {
  --el-table-border-color: #dbe7f3;
  --el-table-header-bg-color: #f6faff;
  --el-table-row-hover-bg-color: #f8fbff;
  border: 1px solid #dbe7f3;
  border-radius: 18px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.92);
}

.lab-main :deep(.el-table th.el-table__cell) {
  color: #64748b;
  font-weight: 700;
}

.lab-main :deep(.el-button),
.lab-main :deep(.el-input__wrapper),
.lab-main :deep(.el-textarea__inner),
.lab-main :deep(.el-select__wrapper) {
  border-radius: 14px;
}

@media (max-width: 1180px) {
  .lab-shell {
    grid-template-columns: 1fr;
  }
}
</style>
