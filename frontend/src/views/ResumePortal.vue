<template>
  <div class="resume-portal">
    <div class="workspace-shell">
      <aside class="workspace-aside">
        <div class="workspace-title">求职功能导航</div>
        <el-menu :default-active="activePanel" class="section-menu" @select="handlePanelChange">
          <el-menu-item index="overview">
            <el-icon><DataBoard /></el-icon>
            <span>工作台概览</span>
          </el-menu-item>
          <el-menu-item index="resumeSync">
            <el-icon><UploadFilled /></el-icon>
            <span>简历同步</span>
          </el-menu-item>
          <el-menu-item index="resumeEdit">
            <el-icon><EditPen /></el-icon>
            <span>资料编辑</span>
          </el-menu-item>
          <el-menu-item index="recommendations">
            <el-icon><Opportunity /></el-icon>
            <span>岗位推荐</span>
          </el-menu-item>
        </el-menu>
      </aside>

      <div class="workspace-main">
        <section v-show="activePanel === 'overview'" class="panel-section">
          <el-card class="overview-head">
            <div class="overview-head-content">
              <div>
                <div class="overview-kicker">求职工作台</div>
                <div class="overview-head-title">统一查看资料、推荐与动作</div>
              </div>
              <el-button type="primary" @click="activePanel = 'resumeSync'">同步简历</el-button>
            </div>
          </el-card>

          <el-row :gutter="18" class="summary-row">
            <el-col :span="8">
              <el-card class="summary-card">
                <div class="summary-label">简历状态</div>
                <div class="summary-value">{{ hasResumeData ? '已同步' : '待上传' }}</div>
                <div class="summary-note">当前姓名：{{ parsedData.name || '未命名简历' }}</div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card class="summary-card">
                <div class="summary-label">技能标签</div>
                <div class="summary-value">{{ parsedData.skills.length }}</div>
                <div class="summary-note">用于支持岗位推荐分析与差距提示</div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card class="summary-card">
                <div class="summary-label">岗位推荐</div>
                <div class="summary-value">{{ recommendedJobs.length }}</div>
                <div class="summary-note">推荐结果作为求职辅助</div>
              </el-card>
            </el-col>
          </el-row>

          <el-row :gutter="18">
            <el-col :span="14">
              <el-card class="overview-card" header="当前求职资料">
                <div class="overview-block">
                  <div class="overview-title">核心技能</div>
                  <div v-if="parsedData.skills.length" class="tag-wrap">
                    <el-tag v-for="s in parsedData.skills" :key="s" type="info" effect="plain">{{ s }}</el-tag>
                  </div>
                  <el-empty v-else description="暂无技能标签" :image-size="58" />
                </div>
              </el-card>
            </el-col>
            <el-col :span="10">
              <el-card class="overview-card" header="下一步动作">
                <div class="action-list">
                  <button class="action-item" @click="activePanel = 'resumeEdit'">更新简历内容并重新保存</button>
                  <button class="action-item" @click="activePanel = 'recommendations'">查看岗位推荐与投递动作</button>
                  <button class="action-item" @click="activePanel = 'resumeSync'">重新上传文件并刷新画像</button>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </section>

        <section v-show="activePanel === 'resumeSync'" class="panel-section">
          <el-card header="简历同步与信息画像" v-loading="loading">
            <div class="sync-layout">
              <div class="sync-upload">
                <el-upload drag action="" :http-request="uploadAndMatch" :show-file-list="false">
                  <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                  <div class="el-upload__text">拖拽文件或点击上传简历</div>
                </el-upload>
                <div class="sync-note">支持 PDF、DOC、DOCX，上传后自动写入当前求职账户。</div>
              </div>

              <div class="sync-chart">
                <div v-show="hasResumeData" id="radar-chart" class="chart-box"></div>
                <el-empty v-if="!hasResumeData" description="暂无画像数据" :image-size="60" />
              </div>
            </div>
          </el-card>
        </section>

        <section v-show="activePanel === 'resumeEdit'" class="panel-section">
          <el-card v-loading="loading">
            <template #header>
              <div class="card-header">
                <span>求职资料编辑</span>
                <el-button type="success" @click="saveResumeOnline">保存资料</el-button>
              </div>
            </template>
            <el-form label-position="top">
              <el-row :gutter="20">
                <el-col :span="6">
                  <el-form-item label="姓名">
                    <el-input v-model="parsedData.name" placeholder="姓名" />
                  </el-form-item>
                </el-col>
                <el-col :span="18">
                  <el-form-item label="核心技能">
                    <div class="tag-wrap">
                      <el-tag v-for="s in parsedData.skills" :key="s" closable @close="removeSkill(s)">
                        {{ s }}
                      </el-tag>
                    </div>
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="简历正文">
                <el-input type="textarea" :rows="14" v-model="parsedData.raw_text" placeholder="在这里维护求职资料与简历文本" />
              </el-form-item>
            </el-form>
          </el-card>
        </section>

        <section v-show="activePanel === 'recommendations'" class="panel-section">
          <el-card class="job-card">
            <template #header>
              <div class="recommendation-header">
                <div>
                  <div class="recommendation-kicker">岗位推荐</div>
                  <div class="recommendation-title">根据当前资料生成的推荐列表</div>
                </div>
                <el-tag type="primary" effect="plain">{{ recommendedJobs.length }} 个推荐结果</el-tag>
              </div>
            </template>

            <div v-if="recommendedJobs.length" class="recommendation-list">
              <article v-for="row in recommendedJobs" :key="row.job_info.id" class="recommendation-item">
                <div class="recommendation-score">
                  <div class="recommendation-score-value">{{ row.score }}%</div>
                  <div class="recommendation-score-label">匹配度</div>
                </div>

                <div class="recommendation-body">
                  <div class="recommendation-meta">
                    <div>
                      <div class="job-title">{{ row.job_info.title }}</div>
                      <div class="job-meta">{{ row.job_info.company }} | {{ row.job_info.loc }}</div>
                    </div>
                    <el-tag type="success" effect="light">推荐岗位</el-tag>
                  </div>

                  <div class="recommendation-skills">
                    <el-tag v-for="skill in jobSkills(row)" :key="skill" type="info" effect="plain">
                      {{ skill }}
                    </el-tag>
                  </div>

                  <div class="recommendation-actions">
                    <el-button type="primary" @click="handleApply(row)">投递</el-button>
                    <el-button type="warning" @click="handleFavorite(row)">收藏</el-button>
                    <el-button type="info" plain @click="analyzeGap(row)">差距分析</el-button>
                  </div>
                </div>
              </article>
            </div>
            <el-empty v-else description="暂无岗位推荐，请先完善简历资料" />
          </el-card>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DataBoard, EditPen, Opportunity, UploadFilled } from '@element-plus/icons-vue'

const parsedData = ref({
  name: '',
  skills: [],
  raw_text: '',
  metrics: { experience: 0, education: 0, structure: 0 }
})
const recommendedJobs = ref([])
const loading = ref(false)
const activePanel = ref('overview')
let myChart = null

const hasResumeData = computed(() => parsedData.value.raw_text && parsedData.value.raw_text.length > 5)

onMounted(async () => {
  const user = JSON.parse(localStorage.getItem('user'))
  if (!user) return

  try {
    loading.value = true
    const res = await axios.get(`http://127.0.0.1:8000/get_my_resume/${user.id}`)
    if (res.data.status === 'success') {
      parsedData.value = res.data.data
      await refreshMatches()
    }
  } catch (error) {
    console.log('未找到历史简历')
  } finally {
    loading.value = false
  }
})

const refreshMatches = async () => {
  if (!parsedData.value.raw_text) return
  try {
    const res = await axios.post('http://127.0.0.1:8000/match', {
      text: parsedData.value.raw_text
    })
    recommendedJobs.value = res.data.recommendations || []

    nextTick(() => {
      if (activePanel.value === 'resumeSync') updateChart()
    })
  } catch (error) {
    console.error('岗位匹配失败', error)
  }
}

const uploadAndMatch = async (options) => {
  const formData = new FormData()
  formData.append('file', options.file)
  const user = JSON.parse(localStorage.getItem('user'))

  loading.value = true
  try {
    const res = await axios.post('http://127.0.0.1:8000/upload', formData)
    if (res.data.status === 'success') {
      parsedData.value = res.data.data
      activePanel.value = 'resumeSync'

      await axios.post('http://127.0.0.1:8000/save_to_pool', {
        user_id: user.id,
        name: parsedData.value.name,
        raw_text: parsedData.value.raw_text
      })

      await refreshMatches()
      ElMessage.success('简历已解析并同步到求职工作台')
    }
  } catch (error) {
    ElMessage.error('解析服务异常')
  } finally {
    loading.value = false
  }
}

const saveResumeOnline = async () => {
  const user = JSON.parse(localStorage.getItem('user'))
  await axios.post('http://127.0.0.1:8000/save_resume_status', {
    user_id: user.id,
    name: parsedData.value.name,
    raw_text: parsedData.value.raw_text
  })
  ElMessage.success('保存成功')
  refreshMatches()
}

const handleApply = async (row) => {
  const user = JSON.parse(localStorage.getItem('user'))
  const res = await axios.post('http://127.0.0.1:8000/apply_job', {
    user_id: user.id,
    job_id: row.job_info.id
  })
  if (res.data.status === 'success') ElMessage.success(res.data.message)
}

const handleFavorite = async (row) => {
  const user = JSON.parse(localStorage.getItem('user'))
  const res = await axios.post('http://127.0.0.1:8000/favorite_job', {
    user_id: user.id,
    job_id: row.job_info.id
  })
  if (res.data.status === 'success') ElMessage.success('已收藏')
}

const analyzeGap = async (row) => {
  const res = await axios.post('http://127.0.0.1:8000/get_skill_gap', {
    user_skills: parsedData.value.skills,
    job_title: row.job_info.title,
    job_skills_text: row.job_info.skills + row.job_info.description
  })
  ElMessageBox.alert(res.data.advice, '改进建议')
}

const jobSkills = (row) => {
  const skills = row?.job_info?.skills || ''
  return String(skills)
    .split(/[,\uff0c/|]/)
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 6)
}

const removeSkill = (skill) => {
  parsedData.value.skills = parsedData.value.skills.filter((tag) => tag !== skill)
}

const updateChart = () => {
  const dom = document.getElementById('radar-chart')
  if (!dom) return
  if (!myChart) myChart = echarts.init(dom)

  const skillScore = Math.min(parsedData.value.skills.length * 20, 100)
  const metrics = parsedData.value.metrics || { experience: 0, education: 0, structure: 0 }

  myChart.setOption({
    radar: {
      indicator: [
        { name: '技能覆盖', max: 100 },
        { name: '经验水平', max: 100 },
        { name: '学历层次', max: 100 },
        { name: '简历质量', max: 100 }
      ],
      radius: '60%'
    },
    series: [{
      type: 'radar',
      data: [{
        value: [skillScore, metrics.experience, metrics.education, metrics.structure],
        name: '能力轨迹',
        areaStyle: { color: 'rgba(64, 158, 255, 0.4)' }
      }]
    }]
  })
}

const handlePanelChange = (panel) => {
  activePanel.value = panel
}

watch(activePanel, (panel) => {
  if (panel === 'resumeSync' && hasResumeData.value) {
    nextTick(() => {
      updateChart()
    })
  }
})
</script>

<style scoped>
.resume-portal {
  min-height: calc(100vh - 140px);
}

.workspace-shell {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 20px;
}

.workspace-aside {
  border-radius: 24px;
  padding: 22px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  border: 1px solid #dbe7f3;
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.06);
}

.workspace-title {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
}

.workspace-subtitle {
  margin-top: 10px;
  color: #64748b;
  line-height: 1.6;
  font-size: 14px;
}

.section-menu {
  margin-top: 20px;
  border-right: none;
}

.section-menu :deep(.el-menu-item) {
  height: 52px;
  margin-bottom: 8px;
  border-radius: 14px;
}

.section-menu :deep(.el-menu-item.is-active) {
  background: #0f172a;
  color: #ffffff;
}

.workspace-main {
  min-width: 0;
}

.panel-section {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.overview-head {
  border-radius: 20px;
}

.overview-head-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.overview-kicker {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 6px;
}

.overview-head-title {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
}

.summary-card {
  border-radius: 20px;
}

.summary-label {
  color: #64748b;
  font-size: 13px;
}

.summary-value {
  margin-top: 10px;
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
}

.summary-note {
  margin-top: 8px;
  color: #475569;
  font-size: 13px;
  line-height: 1.6;
}

.overview-card {
  border-radius: 20px;
}

.overview-block {
  min-height: 180px;
}

.overview-title {
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 12px;
}

.tag-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.action-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-item {
  text-align: left;
  border: 1px solid #dbe7f3;
  background: #ffffff;
  padding: 14px 16px;
  border-radius: 14px;
  color: #0f172a;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-item:hover {
  transform: translateY(-1px);
  border-color: #93c5fd;
  background: #eff6ff;
}

.sync-layout {
  display: grid;
  grid-template-columns: minmax(280px, 400px) 1fr;
  gap: 20px;
  align-items: start;
}

.sync-note {
  margin-top: 14px;
  color: #64748b;
  line-height: 1.6;
}

.sync-chart {
  min-height: 340px;
  border-radius: 18px;
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  padding: 10px;
}

.chart-box {
  width: 100%;
  height: 320px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.recommendation-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.recommendation-kicker {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 6px;
}

.recommendation-title {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
}

.recommendation-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.recommendation-item {
  display: grid;
  grid-template-columns: 108px 1fr;
  gap: 18px;
  padding: 18px;
  border: 1px solid #dbe7f3;
  border-radius: 20px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
}

.recommendation-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 18px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #1d4ed8;
}

.recommendation-score-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1;
}

.recommendation-score-label {
  margin-top: 8px;
  font-size: 12px;
}

.recommendation-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.recommendation-meta {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.recommendation-skills {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.recommendation-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.job-title {
  font-weight: 700;
  color: #2563eb;
}

.job-meta {
  font-size: 12px;
  color: #64748b;
  margin-top: 4px;
}

.workspace-main :deep(.el-card) {
  border-radius: 20px;
  border: 1px solid #dbe7f3;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.05);
}

.workspace-main :deep(.el-card__header) {
  padding: 18px 20px;
  border-bottom: 1px solid #e2e8f0;
  color: #0f172a;
  font-weight: 700;
}

.workspace-main :deep(.el-card__body) {
  padding: 20px;
}

.workspace-main :deep(.el-table) {
  --el-table-border-color: #dbe7f3;
  --el-table-header-bg-color: #f6faff;
  --el-table-row-hover-bg-color: #f8fbff;
  border: 1px solid #dbe7f3;
  border-radius: 18px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.92);
}

.workspace-main :deep(.el-table th.el-table__cell) {
  color: #64748b;
  font-weight: 700;
  background: #f6faff;
}

.workspace-main :deep(.el-button) {
  border-radius: 12px;
}

.workspace-main :deep(.el-input__wrapper),
.workspace-main :deep(.el-textarea__inner) {
  border-radius: 14px;
  box-shadow: 0 0 0 1px #dbe7f3 inset;
}

@media (max-width: 1100px) {
  .workspace-shell {
    grid-template-columns: 1fr;
  }

  .sync-layout {
    grid-template-columns: 1fr;
  }

  .recommendation-item {
    grid-template-columns: 1fr;
  }

  .recommendation-header,
  .recommendation-meta {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
