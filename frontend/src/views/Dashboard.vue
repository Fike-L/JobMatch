<template>
  <div class="dashboard-container">
    <el-row :gutter="20">
      <!-- 统计卡片 -->
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

    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 左侧：用户角色分布饼图 -->
      <el-col :span="10">
        <el-card shadow="hover" header="平台用户角色构成">
          <div id="user-role-chart" style="width: 100%; height: 350px;"></div>
        </el-card>
      </el-col>

      <!-- 右侧：实时活动日志 -->
      <el-col :span="14">
        <el-card shadow="hover" header="实时系统监控日志">
          <el-table :data="systemLogs" size="small" style="width: 100%" height="350">
            <el-table-column prop="username" label="操作用户" width="100" />
            <el-table-column label="动作">
              <template #default="scope">
                <el-tag :type="getActionTag(scope.row.action_type)" size="small">
                  {{ formatAction(scope.row.action_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="action_time" label="发生时间" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'
import axios from 'axios'
import { User, Timer, Check, Close } from '@element-plus/icons-vue'

const stats = ref([])
const systemLogs = ref([])
let myChart = null

const fetchStats = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:8000/system_stats')
    if (res.data.status === 'success') {
      stats.value = res.data.stats
      systemLogs.value = res.data.logs
      initUserChart(res.data.chart_data)
    }
  } catch (error) {
    console.error("加载数据失败")
  }
}

const initUserChart = (data) => {
  const chartDom = document.getElementById('user-role-chart')
  if (!chartDom) return
  myChart = echarts.init(chartDom)

  const option = {
    tooltip: {trigger: 'item'},
    legend: {bottom: '5%', left: 'center'},
    series: [{
      name: '用户角色',
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: {borderRadius: 10, borderColor: '#fff', borderWidth: 2},
      label: {show: false, position: 'center'},
      emphasis: {label: {show: true, fontSize: '20', fontWeight: 'bold'}},
      data: data.names.map((name, i) => ({value: data.values[i], name: name}))
    }]
  }
  myChart.setOption(option)
}

const formatAction = (type) => {
  const map = {
    'login': '登录系统',
    'apply': '投递简历',
    'favorite_job': '收藏岗位',
    'match_success': '匹配成功',
    'match_fail': '解析/匹配失败'
  }
  return map[type] || type
}

const getActionTag = (type) => {
  if (type === 'apply' || type === 'match_success') return 'success'
  if (type === 'match_fail') return 'danger'
  if (type === 'login') return 'primary'
  return 'info'
}

onMounted(() => {
  fetchStats()
  window.addEventListener('resize', () => myChart?.resize())
})
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
  background-color: #f0f2f5;
  min-height: 100vh;
}

.stat-card {
  border-radius: 8px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.stat-title {
  font-size: 14px;
  color: #909399;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  margin-top: 5px;
  color: #303133;
}
</style>