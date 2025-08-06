<template>
  <el-dialog
    v-model="dialogVisible"
    :title="`標籤使用統計 - ${labelName}`"
    width="700px"
    @close="handleClose"
  >
    <div v-loading="loading" class="usage-content">
      <!-- 概覽統計 -->
      <div class="usage-overview">
        <div class="overview-cards">
          <div class="overview-card">
            <div class="card-icon total">
              <el-icon><DataAnalysis /></el-icon>
            </div>
            <div class="card-content">
              <div class="card-number">{{ usageData.totalUsage }}</div>
              <div class="card-label">總使用次數</div>
            </div>
          </div>
          
          <div class="overview-card">
            <div class="card-icon recent">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="card-content">
              <div class="card-number">{{ recentUsage }}</div>
              <div class="card-label">近7天使用</div>
            </div>
          </div>
          
          <div class="overview-card">
            <div class="card-icon files">
              <el-icon><Document /></el-icon>
            </div>
            <div class="card-content">
              <div class="card-number">{{ usageData.topFiles.length }}</div>
              <div class="card-label">相關檔案</div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 使用趨勢圖表 -->
      <div class="usage-chart">
        <h4>使用趨勢</h4>
        <div class="chart-controls">
          <el-radio-group v-model="timeRange" @change="fetchUsageData">
            <el-radio-button value="7d">近7天</el-radio-button>
            <el-radio-button value="30d">近30天</el-radio-button>
            <el-radio-button value="90d">近3個月</el-radio-button>
          </el-radio-group>
        </div>
        <div ref="chartRef" class="chart-container"></div>
      </div>
      
      <!-- 關聯檔案列表 -->
      <div class="related-files">
        <h4>相關檔案</h4>
        <el-table 
          :data="usageData.topFiles" 
          size="small"
          max-height="300"
        >
          <el-table-column prop="fileName" label="檔案名稱" min-width="200">
            <template #default="{ row }">
              <div class="file-info">
                <el-icon class="file-icon"><Document /></el-icon>
                <span>{{ row.fileName }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="usage" label="使用次數" width="100" align="center">
            <template #default="{ row }">
              <el-tag type="primary" size="small">{{ row.usage }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="使用比例" width="120" align="center">
            <template #default="{ row }">
              <el-progress 
                :percentage="(row.usage / usageData.totalUsage * 100)"
                :show-text="false"
                :stroke-width="6"
                color="#409eff"
              />
              <span class="percentage-text">
                {{ ((row.usage / usageData.totalUsage) * 100).toFixed(1) }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" align="center">
            <template #default="{ row }">
              <el-button 
                type="primary" 
                link 
                size="small"
                @click="viewFile(row)"
              >
                查看
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <div v-if="!usageData.topFiles.length" class="no-files">
          <el-empty description="暫無相關檔案" :image-size="60" />
        </div>
      </div>
      
      <!-- 使用建議 -->
      <div class="usage-suggestions">
        <h4>使用建議</h4>
        <div class="suggestions-list">
          <div v-for="suggestion in suggestions" :key="suggestion.type" class="suggestion-item">
            <div class="suggestion-icon">
              <el-icon :color="suggestion.color">
                <component :is="suggestion.icon" />
              </el-icon>
            </div>
            <div class="suggestion-content">
              <div class="suggestion-title">{{ suggestion.title }}</div>
              <div class="suggestion-desc">{{ suggestion.description }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新數據
        </el-button>
        <el-button @click="exportUsageData">
          <el-icon><Download /></el-icon>
          匯出報告
        </el-button>
        <el-button type="primary" @click="handleClose">
          關閉
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  DataAnalysis, 
  TrendCharts, 
  Document, 
  Refresh, 
  Download,
  Warning,
  SuccessFilled,
  InfoFilled
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'

interface Props {
  visible: boolean
  labelId: string
  labelType: 'product' | 'feedback'
  labelName: string
}

interface Emits {
  (e: 'update:visible', value: boolean): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 響應式狀態
const loading = ref(false)
const chartRef = ref<HTMLElement>()
const timeRange = ref('30d')
let chartInstance: echarts.ECharts | null = null

const usageData = ref({
  totalUsage: 0,
  recentUsage: [],
  topFiles: []
})

// 計算屬性
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

const recentUsage = computed(() => {
  const recent7Days = usageData.value.recentUsage.slice(-7)
  return recent7Days.reduce((sum: number, item: any) => sum + item.count, 0)
})

const suggestions = computed(() => {
  const totalUsage = usageData.value.totalUsage
  const suggestions = []
  
  if (totalUsage === 0) {
    suggestions.push({
      type: 'warning',
      icon: Warning,
      color: '#e6a23c',
      title: '標籤未被使用',
      description: '此標籤尚未在任何檔案中被使用，考慮是否需要調整標籤設定或刪除。'
    })
  } else if (totalUsage < 5) {
    suggestions.push({
      type: 'info',
      icon: InfoFilled,
      color: '#409eff',
      title: '使用頻率較低',
      description: '此標籤使用頻率較低，可能需要優化標籤名稱或增加相關培訓。'
    })
  } else {
    suggestions.push({
      type: 'success',
      icon: SuccessFilled,
      color: '#67c23a',
      title: '標籤使用良好',
      description: '此標籤被正常使用，建議繼續維護和優化相關功能。'
    })
  }
  
  if (recentUsage.value === 0 && totalUsage > 0) {
    suggestions.push({
      type: 'warning',
      icon: Warning,
      color: '#e6a23c',
      title: '近期未使用',
      description: '此標籤近期未被使用，可能相關業務已發生變化。'
    })
  }
  
  return suggestions
})

// 監聽對話框顯示
watch(dialogVisible, (visible) => {
  if (visible && props.labelId) {
    fetchUsageData()
  }
})

// 獲取使用數據
const fetchUsageData = async () => {
  if (!props.labelId) return
  
  loading.value = true
  
  try {
    // 模擬API調用 - 實際環境中應該調用真實API
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 模擬數據
    const mockData = generateMockUsageData()
    usageData.value = mockData
    
    // 渲染圖表
    await nextTick()
    renderChart()
    
  } catch (error) {
    ElMessage.error('獲取使用統計失敗')
  } finally {
    loading.value = false
  }
}

// 生成模擬數據
const generateMockUsageData = () => {
  const days = timeRange.value === '7d' ? 7 : timeRange.value === '30d' ? 30 : 90
  const recentUsage = []
  
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    recentUsage.push({
      date: date.toISOString().split('T')[0],
      count: Math.floor(Math.random() * 10)
    })
  }
  
  const totalUsage = recentUsage.reduce((sum, item) => sum + item.count, 0)
  
  const topFiles = [
    { id: '1', fileName: '客戶反饋_20250101.wav', usage: 8 },
    { id: '2', fileName: '品質檢測_20250102.txt', usage: 6 },
    { id: '3', fileName: '產品諮詢_20250103.wav', usage: 4 },
    { id: '4', fileName: '服務投訴_20250104.txt', usage: 3 },
    { id: '5', fileName: '滿意度調查_20250105.wav', usage: 2 }
  ].slice(0, Math.floor(Math.random() * 5) + 1)
  
  return {
    totalUsage: Math.max(totalUsage, topFiles.reduce((sum, file) => sum + file.usage, 0)),
    recentUsage,
    topFiles
  }
}

// 渲染圖表
const renderChart = () => {
  if (!chartRef.value) return
  
  if (chartInstance) {
    chartInstance.dispose()
  }
  
  chartInstance = echarts.init(chartRef.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: usageData.value.recentUsage.map(item => {
        const date = new Date(item.date)
        return `${date.getMonth() + 1}/${date.getDate()}`
      }),
      axisLine: {
        lineStyle: {
          color: '#e4e7ed'
        }
      },
      axisLabel: {
        color: '#606266'
      }
    },
    yAxis: {
      type: 'value',
      axisLine: {
        lineStyle: {
          color: '#e4e7ed'
        }
      },
      axisLabel: {
        color: '#606266'
      },
      splitLine: {
        lineStyle: {
          color: '#f0f2f5'
        }
      }
    },
    series: [
      {
        name: '使用次數',
        type: 'line',
        smooth: true,
        data: usageData.value.recentUsage.map(item => item.count),
        lineStyle: {
          color: '#409eff'
        },
        itemStyle: {
          color: '#409eff'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
          ])
        }
      }
    ]
  }
  
  chartInstance.setOption(option)
  
  // 響應式調整
  window.addEventListener('resize', () => {
    chartInstance?.resize()
  })
}

// 查看檔案
const viewFile = (file: any) => {
  ElMessage.info(`查看檔案: ${file.fileName}`)
  // 實際環境中應該導航到檔案詳情頁面
}

// 刷新數據
const refreshData = () => {
  fetchUsageData()
}

// 匯出使用報告
const exportUsageData = () => {
  // 實際環境中應該生成並下載報告
  ElMessage.success('使用報告匯出成功')
}

// 處理關閉
const handleClose = () => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  emit('update:visible', false)
}

// 組件銷毀時清理圖表
onMounted(() => {
  return () => {
    if (chartInstance) {
      chartInstance.dispose()
    }
  }
})
</script>

<style scoped>
.usage-content {
  min-height: 400px;
}

.usage-overview {
  margin-bottom: 24px;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.overview-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.card-icon.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.card-icon.recent {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.card-icon.files {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.card-content {
  flex: 1;
}

.card-number {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  line-height: 1;
}

.card-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.usage-chart {
  margin-bottom: 24px;
  padding: 20px;
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.usage-chart h4 {
  margin: 0 0 16px 0;
  color: #303133;
}

.chart-controls {
  margin-bottom: 16px;
}

.chart-container {
  height: 300px;
  width: 100%;
}

.related-files {
  margin-bottom: 24px;
  padding: 20px;
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.related-files h4 {
  margin: 0 0 16px 0;
  color: #303133;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-icon {
  color: #409eff;
}

.percentage-text {
  font-size: 12px;
  color: #909399;
  margin-left: 8px;
}

.no-files {
  text-align: center;
  padding: 40px 20px;
}

.usage-suggestions {
  padding: 20px;
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.usage-suggestions h4 {
  margin: 0 0 16px 0;
  color: #303133;
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.suggestion-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background: #fafafa;
  border-radius: 6px;
}

.suggestion-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}

.suggestion-content {
  flex: 1;
}

.suggestion-title {
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.suggestion-desc {
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 響應式設計 */
@media (max-width: 768px) {
  .overview-cards {
    grid-template-columns: 1fr;
  }
  
  .usage-chart,
  .related-files,
  .usage-suggestions {
    padding: 16px;
  }
  
  .chart-container {
    height: 250px;
  }
}
</style>