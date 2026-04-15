<template>
  <div class="dashboard-container">
    <div class="lab-shell">
      <aside class="lab-aside">
        <div class="lab-title">管理员功能导航</div>
        <div class="lab-subtitle">从平台运营视角管理公告、反馈、词库和算法实验，而不是只展示匹配模块。</div>

        <el-menu :default-active="activeSection" class="lab-menu" @select="(key) => activeSection = key">
          <el-menu-item index="overview">
            <el-icon><Grid /></el-icon>
            <span>运营总览</span>
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
          <el-menu-item index="sandbox">
            <el-icon><Cpu /></el-icon>
            <span>算法沙箱</span>
          </el-menu-item>
        </el-menu>
      </aside>

      <div class="lab-main">
        <section v-show="activeSection === 'overview'" class="lab-panel">
          <el-card class="overview-head">
            <div class="overview-head-content">
              <div>
                <div class="overview-kicker">管理员工作区</div>
                <div class="overview-head-title">运营、治理与实验统一管理</div>
              </div>
              <el-button type="primary" @click="activeSection = 'announcements'">发布公告</el-button>
            </div>
          </el-card>

          <el-row :gutter="18">
            <el-col :span="6" v-for="item in stats" :key="item.title">
              <el-card shadow="hover" class="stat-card">
                <div class="stat-content">
                  <el-icon :size="40" :color="item.color"><component :is="item.icon" /></el-icon>
                  <div class="stat-text">
                    <div class="stat-title">{{ item.title }}</div>
                    <div class="stat-value">{{ item.value }}</div>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>

          <el-row :gutter="18" style="margin-top: 18px;">
            <el-col :span="12">
              <el-card header="运营动作快捷入口">
                <div class="quick-actions">
                  <button class="quick-action" @click="activeSection = 'announcements'">发布系统公告</button>
                  <button class="quick-action" @click="goFeedbackSection">查看用户反馈</button>
                  <button class="quick-action" @click="activeSection = 'dictionary'">维护技能词库</button>
                  <button class="quick-action" @click="activeSection = 'sandbox'">进入算法沙箱</button>
                </div>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card header="模块定位">
                <div class="module-note">当前后台不再把“推荐算法”作为唯一核心，而是把它纳入平台运营工具的一部分。</div>
                <div class="module-note">页面结构优先展示运营层、治理层和实验层，便于直接说明项目工作量和系统范围。</div>
              </el-card>
            </el-col>
          </el-row>
        </section>

        <section v-show="activeSection === 'announcements'" class="lab-panel">
          <el-card header="公告发布">
            <el-form :model="annoForm" label-position="top">
              <el-form-item label="公告标题"><el-input v-model="annoForm.title" /></el-form-item>
              <el-form-item label="详细内容"><el-input type="textarea" v-model="annoForm.content" :rows="5" /></el-form-item>
              <el-button type="primary" @click="submitAnno">立即全站推送</el-button>
            </el-form>
          </el-card>
        </section>

        <section v-show="activeSection === 'feedbacks'" class="lab-panel">
          <el-card header="用户反馈总览">
            <div style="margin-bottom: 16px;">
              <el-button type="warning" @click="loadFeedbacks">刷新反馈数据</el-button>
            </div>
            <el-tabs>
              <el-tab-pane label="求职者反馈">
                <el-table :data="seekerFbs" stripe height="300">
                  <el-table-column prop="username" label="用户" width="120" />
                  <el-table-column prop="content" label="反馈内容" />
                  <el-table-column prop="submit_time" label="时间" width="180" />
                </el-table>
              </el-tab-pane>
              <el-tab-pane label="HR反馈">
                <el-table :data="hrFbs" stripe height="300">
                  <el-table-column prop="username" label="HR用户" width="120" />
                  <el-table-column prop="content" label="反馈内容" />
                  <el-table-column prop="submit_time" label="时间" width="180" />
                </el-table>
              </el-tab-pane>
            </el-tabs>
          </el-card>
        </section>

        <section v-show="activeSection === 'weights'" class="lab-panel">
          <el-card shadow="hover" header="核心算法权重动态配置">
            <div class="weight-item">
              <span>核心技能硬匹配权重 ({{ weights.skill }}%)</span>
              <el-slider v-model="weights.skill" :step="10" show-stops @change="handleWeightChange" />
            </div>
            <div class="weight-item">
              <span>语义相似度权重 ({{ weights.semantic }}%)</span>
              <el-slider v-model="weights.semantic" :step="10" show-stops @change="handleWeightChange" />
            </div>
            <el-alert
              style="margin-top: 15px"
              title="权重调整会即时影响 HR 端和求职者端的辅助排序结果"
              type="warning"
              show-icon
              :closable="false"
            />
          </el-card>
        </section>

        <section v-show="activeSection === 'dictionary'" class="lab-panel">
          <el-card header="核心技能词库管理" shadow="hover">
            <div class="dictionary-toolbar">
              <el-input v-model="newSkill.name" placeholder="输入新技能名称" size="small" style="width: 180px;" />
              <el-select v-model="newSkill.category" placeholder="选择分类" size="small" style="width: 140px;">
                <el-option label="IT/互联网" value="IT" />
                <el-option label="财务/会计" value="财务" />
                <el-option label="行政/人事" value="行政" />
                <el-option label="市场/营销" value="营销" />
                <el-option label="通用/软技能" value="通用" />
              </el-select>
              <el-button type="primary" size="small" @click="handleAddSkill">添加</el-button>
            </div>

            <el-table :data="dictionary" size="small" style="width: 100%" height="460">
              <el-table-column prop="term" label="专业术语" />
              <el-table-column prop="category" label="分类" width="100" />
              <el-table-column label="操作" width="80">
                <template #default="scope">
                  <el-button type="danger" link size="small" @click="handleDelSkill(scope.row.term)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </section>

        <section v-show="activeSection === 'sandbox'" class="lab-panel">
          <el-card shadow="hover">
            <template #header>
              <div class="card-header">
                <span>算法即时验证沙箱</span>
                <el-tag type="danger">内核: Scikit-learn / TF-IDF</el-tag>
              </div>
            </template>

            <el-row :gutter="10">
              <el-col :span="11">
                <div class="label">测试简历片段</div>
                <el-input
                  v-model="valData.resumeText"
                  type="textarea"
                  :rows="12"
                  placeholder="在此输入简历中的自我介绍或技能描述..."
                />
              </el-col>
              <el-col :span="2" class="vs-icon">VS</el-col>
              <el-col :span="11">
                <div class="label">测试 JD 片段</div>
                <el-input
                  v-model="valData.jdText"
                  type="textarea"
                  :rows="12"
                  placeholder="在此输入岗位的任职要求描述..."
                />
              </el-col>
            </el-row>

            <div class="result-area">
              <div class="score-display">
                <p>语义相似度得分</p>
                <h2>{{ similarityScore }}</h2>
              </div>
              <el-button type="primary" size="large" :loading="loading" @click="calculateSim">
                立即运行相似度计算
              </el-button>
            </div>
          </el-card>
        </section>
      </div>
    </div>

  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Bell, Collection, Cpu, DataLine, Grid, MessageBox } from '@element-plus/icons-vue'

const weights = ref({ skill: 70, semantic: 30 })
const dictionary = ref([])
const newSkill = ref({ name: '', category: 'IT' })
const valData = ref({ resumeText: '', jdText: '' })
const similarityScore = ref('0.00')
const loading = ref(false)
const activeSection = ref('overview')

const stats = ref([])
const annoForm = ref({ title: '', content: '' })
const seekerFbs = ref([])
const hrFbs = ref([])

const submitAnno = async () => {
  try {
    await axios.post('http://127.0.0.1:8000/admin/announcements/post', annoForm.value)
    ElMessage.success('公告已发布')
    annoForm.value = { title: '', content: '' }
  } catch (error) {
    ElMessage.error('发布公告失败')
  }
}

const loadFeedbacks = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:8000/admin/all_feedbacks')
    seekerFbs.value = res.data.seeker_fb || []
    hrFbs.value = res.data.hr_fb || []
  } catch (error) {
    ElMessage.error('获取反馈失败')
  }
}

const goFeedbackSection = async () => {
  await loadFeedbacks()
  activeSection.value = 'feedbacks'
}

const fetchStats = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:8000/system_stats')
    if (res.data.status === 'success') {
      stats.value = res.data.stats || []
    }
  } catch (error) {
    stats.value = [
      { title: '平台用户量', value: '-', icon: 'User', color: '#409EFF' },
      { title: '今日活跃', value: '-', icon: 'Timer', color: '#67C23A' },
      { title: '申请总数', value: '-', icon: 'Check', color: '#E6A23C' },
      { title: '岗位数量', value: '-', icon: 'Briefcase', color: '#F56C6C' }
    ]
  }
}

const fetchDict = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:8000/get_dictionary')
    dictionary.value = res.data.data || []
  } catch (error) {
    ElMessage.error('获取词库失败')
  }
}

const handleWeightChange = async () => {
  weights.value.semantic = 100 - weights.value.skill
  try {
    const res = await axios.post('http://127.0.0.1:8000/update_algorithm_weights', {
      skill: weights.value.skill,
      semantic: weights.value.semantic
    })

    if (res.data.status === 'success') {
      ElMessage.success('系统权重已更新')
      if (valData.value.resumeText && valData.value.jdText) {
        calculateSim()
      }
    }
  } catch (error) {
    ElMessage.error('同步失败')
  }
}

const calculateSim = async () => {
  if (!valData.value.resumeText || !valData.value.jdText) {
    ElMessage.warning('请输入对比文本')
    return
  }

  loading.value = true
  try {
    const res = await axios.post('http://127.0.0.1:8000/calculate_instant_sim', valData.value)
    similarityScore.value = res.data.score
    ElMessage.success('计算完成')
  } catch (error) {
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
    const res = await axios.post('http://127.0.0.1:8000/admin/skills/add', newSkill.value)
    if (res.data.status === 'success') {
      ElMessage.success('词库已更新')
      newSkill.value.name = ''
      fetchDict()
    } else {
      ElMessage.error(res.data.message)
    }
  } catch (error) {
    ElMessage.error('添加技能失败')
  }
}

const handleDelSkill = (name) => {
  ElMessageBox.confirm(`确定要从词库中移除“${name}”吗？`, '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await axios.post('http://127.0.0.1:8000/admin/skills/delete', { name })
      ElMessage.success('已删除')
      fetchDict()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

onMounted(() => {
  fetchDict()
  fetchStats()
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

.lab-subtitle {
  margin-top: 10px;
  color: #64748b;
  font-size: 14px;
  line-height: 1.6;
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
  background: #ffffff;
  border-radius: 24px;
  border: 1px solid #dbe7f3;
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.06);
  padding: 20px;
}

.overview-kicker {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 6px;
}

.overview-head {
  border-radius: 20px;
  margin-bottom: 18px;
}

.overview-head-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.overview-head-title {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
}

@media (max-width: 768px) {
  .overview-head-content {
    align-items: flex-start;
    flex-direction: column;
  }
}

.stat-card {
  margin-bottom: 20px;
  border-radius: 18px;
}

.stat-content {
  display: flex;
  align-items: center;
}

.stat-text {
  margin-left: 15px;
}

.stat-title {
  color: #909399;
  font-size: 14px;
}

.stat-value {
  color: #303133;
  font-size: 24px;
  font-weight: bold;
  margin-top: 5px;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.quick-action {
  text-align: left;
  border: 1px solid #dbe7f3;
  background: #ffffff;
  padding: 14px 16px;
  border-radius: 14px;
  color: #0f172a;
  cursor: pointer;
  transition: all 0.2s ease;
}

.quick-action:hover {
  transform: translateY(-1px);
  border-color: #93c5fd;
  background: #eff6ff;
}

.module-note {
  line-height: 1.8;
  color: #475569;
  margin-bottom: 12px;
}

.weight-item {
  margin-bottom: 30px;
}

.weight-item span {
  display: block;
  margin-bottom: 15px;
  color: #606266;
  font-weight: bold;
}

.vs-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  color: #909399;
  font-size: 24px;
  padding-top: 100px;
}

.label {
  margin-bottom: 10px;
  font-size: 13px;
  color: #909399;
  text-align: center;
}

.result-area {
  margin-top: 30px;
  text-align: center;
  border-top: 1px dashed #dcdfe6;
  padding-top: 20px;
}

.score-display h2 {
  font-size: 54px;
  color: #409eff;
  margin: 10px 0;
  font-family: 'Courier New', Courier, monospace;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dictionary-toolbar {
  margin-bottom: 14px;
  display: flex;
  gap: 10px;
}

@media (max-width: 1100px) {
  .lab-shell {
    grid-template-columns: 1fr;
  }
}
</style>
