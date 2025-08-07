<template>
  <div class="dashboard-page">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">今日營運洞察</h1>
        <div class="header-actions">
          <el-button circle @click="refreshData" :loading="loading">
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>
      </div>
    </div>

    <!-- AI 洞察建議 -->
    <div class="insights-section">
      <div v-for="insight in insights" :key="insight.id" :class="[
        'insight-card',
        `insight-${insight.type}`
      ]">
        <div class="insight-icon">
          <el-icon>
            <SuccessFilled v-if="insight.type === 'success'" />
            <WarningFilled v-else-if="insight.type === 'warning'" />
            <InfoFilled v-else />
          </el-icon>
        </div>
        <div class="insight-content">
          <p>{{ insight.content }}</p>
        </div>
      </div>
    </div>

    <!-- 頂部圖表區域 -->
    <div class="charts-section top-charts">
      <!-- 熱門商品討論熱度 -->
      <div class="chart-container">
        <div class="chart-header">
          <h2 class="chart-title">熱門商品討論熱度</h2>
        </div>
        <div class="chart-wrapper">
          <div v-if="chartsLoading" class="chart-skeleton"></div>
          <canvas v-show="!chartsLoading" ref="hotProductsChart"></canvas>
        </div>
      </div>

      <!-- 反饋類別熱度排名 -->
      <div class="chart-container">
        <div class="chart-header">
          <h2 class="chart-title">反饋類別熱度排名</h2>
        </div>
        <div class="chart-wrapper">
          <div v-if="chartsLoading" class="chart-skeleton"></div>
          <canvas v-show="!chartsLoading" ref="feedbackRankingChart"></canvas>
        </div>
      </div>
    </div>

    <!-- 圓形圖表區域 -->
    <div class="charts-section circular-charts">
      <!-- 情緒指標比例 -->
      <div class="chart-container small">
        <div class="chart-header">
          <h2 class="chart-title">情緒指標比例</h2>
        </div>
        <div class="chart-wrapper small">
          <div v-if="chartsLoading" class="chart-skeleton circular"></div>
          <canvas v-show="!chartsLoading" ref="sentimentRatioChart"></canvas>
        </div>
      </div>

      <!-- 關注商品概況 -->
      <div class="chart-container small">
        <div class="chart-header">
          <h2 class="chart-title">關注商品概況</h2>
          <span class="chart-top-label">本日 Top 3</span>
        </div>
        <div class="chart-wrapper small">
          <div v-if="chartsLoading" class="chart-skeleton circular"></div>
          <canvas v-show="!chartsLoading" ref="productDistributionChart"></canvas>
        </div>
      </div>

      <!-- 關注反饋概況 -->
      <div class="chart-container small">
        <div class="chart-header">
          <h2 class="chart-title">關注反饋概況</h2>
          <span class="chart-top-label">本日 Top 3</span>
        </div>
        <div class="chart-wrapper small">
          <div v-if="chartsLoading" class="chart-skeleton circular"></div>
          <canvas v-show="!chartsLoading" ref="feedbackDistributionChart"></canvas>
        </div>
      </div>
    </div>

    <!-- 趨勢圖表區域 -->
    <div class="charts-section trend-charts">
      <!-- 商品熱門度趨勢 -->
      <div class="chart-container">
        <div class="chart-header">
          <h2 class="chart-title">
            商品熱門度趨勢 
            <span class="clickable-hint" @click="navigateToAnalysis">點選查看 ⊃</span>
          </h2>
        </div>
        <div class="chart-wrapper">
          <canvas ref="productTrendChart"></canvas>
        </div>
      </div>

      <!-- 反饋次數趨勢 -->
      <div class="chart-container">
        <div class="chart-header">
          <h2 class="chart-title">
            反饋次數趨勢 
            <span class="clickable-hint" @click="navigateToAnalysis">點選查看 ⊃</span>
          </h2>
        </div>
        <div class="chart-wrapper">
          <canvas ref="feedbackTrendChart"></canvas>
        </div>
      </div>

      <!-- 情緒指標趨勢 -->
      <div class="chart-container">
        <div class="chart-header">
          <h2 class="chart-title">
            情緒指標趨勢 
            <span class="clickable-hint" @click="navigateToAnalysis">點選查看 ⊃</span>
          </h2>
        </div>
        <div class="chart-wrapper">
          <canvas ref="sentimentTrendChart"></canvas>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  Refresh,
  SuccessFilled,
  WarningFilled,
  InfoFilled
} from '@element-plus/icons-vue'
import Chart from 'chart.js/auto'
import { dashboardService } from '@/services/dashboard.service'

const router = useRouter()
const loading = ref(false)
const chartsLoading = ref(true)

// Chart refs
const hotProductsChart = ref<HTMLCanvasElement>()
const feedbackRankingChart = ref<HTMLCanvasElement>()
const productDistributionChart = ref<HTMLCanvasElement>()
const feedbackDistributionChart = ref<HTMLCanvasElement>()
const sentimentRatioChart = ref<HTMLCanvasElement>()
const productTrendChart = ref<HTMLCanvasElement>()
const feedbackTrendChart = ref<HTMLCanvasElement>()
const sentimentTrendChart = ref<HTMLCanvasElement>()

// Chart instances
const charts: Record<string, Chart> = {}

// Dashboard data from API
const dashboardData = ref<any>(null)

// AI 洞察數據
const insights = ref([
  {
    id: 1,
    type: 'success',
    content: '客訴量較上週下降2.3%，主要歸因於配送效率提升。建議持續優化物流系統，預計可進一步降低15%客訴率。'
  },
  {
    id: 2,
    type: 'warning',
    content: '偵測到1.2個月，月增5%，鑑觀主要業主通道改革，建議持續提升營運效率並加強供應鏈整合性。'
  },
  {
    id: 3,
    type: 'info',
    content: '統計顯示1.2個月，月增5%，鑑觀主要業主通道改革建議持續提升營運效率並加強供應鏈結之基礎設施將持續支援開發運行推動投資能力。'
  }
])

// 加載儀表盤數據
const loadDashboardData = async () => {
  try {
    loading.value = true
    const response = await dashboardService.getMetrics()
    dashboardData.value = response
    console.log('Dashboard data loaded:', response)
    
    // 嘗試加載 AI insights
    try {
      const insightsData = await dashboardService.getAIInsights()
      insights.value = insightsData
    } catch (insightError) {
      console.warn('AI insights API not available, using default data')
      // insights.value 已經有預設數據，不需要修改
    }
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
    ElMessage.error('載入儀表盤數據失敗')
  } finally {
    loading.value = false
  }
}

// 初始化圖表
const initCharts = () => {
  if (!dashboardData.value) {
    console.warn('Dashboard data not loaded yet')
    return
  }

  Chart.defaults.font.family = "'Noto Sans TC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
  Chart.defaults.font.size = 14
  Chart.defaults.color = '#374151'

  // 熱門商品討論熱度 (Stacked Bar Chart)
  if (hotProductsChart.value && dashboardData.value.product_chart) {
    const productChart = dashboardData.value.product_chart
    
    // 使用真實的情感數據
    const positiveData = productChart.data.map((item: any) => item.positive_count || 0)
    const neutralData = productChart.data.map((item: any) => item.neutral_count || 0)
    const negativeData = productChart.data.map((item: any) => item.negative_count || 0)
    
    charts.hotProducts = new Chart(hotProductsChart.value, {
      type: 'bar',
      data: {
        labels: productChart.data.map((item: any) => {
          // 清理產品名稱：移除方括號和引號
          if (!item.name) return '無'
          
          let cleanName = item.name.toString()
          
          // 處理 JSON 陣列格式 ["包子"] 或 ["包子", "水餃"]
          if (cleanName.startsWith('[') && cleanName.endsWith(']')) {
            try {
              // 嘗試解析為 JSON 陣列
              const parsed = JSON.parse(cleanName)
              if (Array.isArray(parsed)) {
                return parsed.join(', ')
              }
            } catch (e) {
              // 如果解析失敗，手動清理
              cleanName = cleanName.replace(/^\[|\]$/g, '')
              cleanName = cleanName.replace(/"/g, '')
              cleanName = cleanName.replace(/'/g, '')
              return cleanName
            }
          }
          
          return cleanName || '無'
        }),
        datasets: [
          {
            label: '正向',
            data: positiveData,
            backgroundColor: '#3333FF',
            stack: 'stack1'
          },
          {
            label: '中立',
            data: neutralData,
            backgroundColor: '#FFC18F',
            stack: 'stack1'
          },
          {
            label: '負向',
            data: negativeData,
            backgroundColor: '#FF7676',
            stack: 'stack1'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 1500,
          easing: 'easeInOutQuart',
          delay: (context: any) => {
            return context.dataIndex * 100
          }
        },
        plugins: {
          legend: {
            position: 'bottom',
            labels: { 
              usePointStyle: true, 
              padding: 20, 
              color: '#374151'
            }
          },
          tooltip: {
            callbacks: {
              label: function(context: any) {
                return context.dataset.label + ': ' + context.parsed.y
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            stacked: true,
            grid: { color: 'rgba(0, 0, 0, 0.05)' },
            ticks: { 
              color: '#6b7280',
              font: {
                size: 13
              }
            }
          },
          x: {
            stacked: true,
            grid: { display: false },
            ticks: { 
              color: '#6b7280',
              maxRotation: 0,
              minRotation: 0,
              font: {
                size: 13,
                weight: '500'
              }
            }
          }
        }
      }
    })
  }

  // 反饋類別熱度排名 (Stacked Bar Chart)
  if (feedbackRankingChart.value && dashboardData.value.category_chart) {
    const categoryChart = dashboardData.value.category_chart
    
    // 使用真實的情感數據
    const positiveData = categoryChart.data.map((item: any) => item.positive_count || 0)
    const neutralData = categoryChart.data.map((item: any) => item.neutral_count || 0)
    const negativeData = categoryChart.data.map((item: any) => item.negative_count || 0)
    
    charts.feedbackRanking = new Chart(feedbackRankingChart.value, {
      type: 'bar',
      data: {
        labels: categoryChart.data.map((item: any) => item.name),
        datasets: [
          {
            label: '正向',
            data: positiveData,
            backgroundColor: '#3333FF',
            stack: 'stack1'
          },
          {
            label: '中立',
            data: neutralData,
            backgroundColor: '#FFC18F',
            stack: 'stack1'
          },
          {
            label: '負向',
            data: negativeData,
            backgroundColor: '#FF7676',
            stack: 'stack1'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 1500,
          easing: 'easeInOutQuart',
          delay: (context: any) => {
            return context.dataIndex * 100
          }
        },
        plugins: {
          legend: {
            position: 'bottom',
            labels: { 
              usePointStyle: true, 
              padding: 20, 
              color: '#374151'
            }
          },
          tooltip: {
            callbacks: {
              label: function(context: any) {
                return context.dataset.label + ': ' + context.parsed.y
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            stacked: true,
            grid: { color: 'rgba(0, 0, 0, 0.05)' },
            ticks: { 
              color: '#6b7280',
              font: {
                size: 13
              }
            }
          },
          x: {
            stacked: true,
            grid: { display: false },
            ticks: { 
              color: '#6b7280',
              maxRotation: 0,
              minRotation: 0,
              font: {
                size: 13,
                weight: '500'
              }
            }
          }
        }
      }
    })
  }

  // 關注商品概況 (Doughnut Chart)
  if (productDistributionChart.value && dashboardData.value.product_chart) {
    const productChart = dashboardData.value.product_chart
    
    // 取前3個產品，模擬相關和相同的分類
    const topProducts = productChart.data.slice(0, 3)
    const total = topProducts.reduce((sum: number, item: any) => sum + item.value, 0)
    const relatedCount = Math.floor(total * 0.8)  // 80件相關
    const sameCount = Math.floor(total * 0.2)     // 其他
    
    charts.productDistribution = new Chart(productDistributionChart.value, {
      type: 'doughnut',
      data: {
        labels: ['相關', '相同'],
        datasets: [{
          data: [relatedCount, sameCount],
          backgroundColor: [
            'rgb(139, 92, 246)',
            'rgb(251, 191, 36)'
          ],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '65%',
        animation: {
          animateRotate: true,
          animateScale: true,
          duration: 1200,
          easing: 'easeInOutQuart'
        },
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              label: function(context: any) {
                return context.label + ': ' + context.parsed + '件'
              }
            }
          }
        }
      },
      plugins: [{
        id: 'centerText',
        beforeDraw: function(chart: any) {
          const width = chart.width
          const height = chart.height
          const ctx = chart.ctx
          
          if (!ctx) return
          
          ctx.save()
          
          // 動態計算字體大小
          const baseSize = Math.min(width, height)
          const valueFontSize = Math.max(Math.floor(baseSize * 0.18), 20) // 主要數值字體大小，最小20px
          const labelFontSize = Math.max(Math.floor(baseSize * 0.08), 12) // 標籤字體大小，最小12px
          
          // 繪製主要數值
          ctx.font = `bold ${valueFontSize}px "Noto Sans TC", sans-serif`
          ctx.textBaseline = 'middle'
          ctx.textAlign = 'center'
          ctx.fillStyle = '#1f2937'
          
          const text = relatedCount + '件'
          const textX = Math.round(width / 2)
          const textY = height / 2 - (labelFontSize * 0.7)
          
          ctx.fillText(text, textX, textY)
          
          // 繪製標籤
          ctx.font = `normal ${labelFontSize}px "Noto Sans TC", sans-serif`
          ctx.fillStyle = '#6b7280'
          const labelY = textY + valueFontSize * 0.7
          ctx.fillText('相關', textX, labelY)
          
          ctx.restore()
        }
      }]
    })
  }

  // 關注反饋概況 (Doughnut Chart)
  if (feedbackDistributionChart.value) {
    // 模擬物流/配送相關的反饋數據
    const feedbackData = {
      logistics: 0,      // 物流/配送
      other: 0          // 相關
    }
    
    charts.feedbackDistribution = new Chart(feedbackDistributionChart.value, {
      type: 'doughnut',
      data: {
        labels: ['物流/配送', '相關'],
        datasets: [{
          data: [feedbackData.logistics, feedbackData.other],
          backgroundColor: [
            'rgb(168, 85, 247)',
            'rgb(251, 191, 36)'
          ],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '65%',
        animation: {
          animateRotate: true,
          animateScale: true,
          duration: 1200,
          easing: 'easeInOutQuart'
        },
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              label: function(context: any) {
                return context.label + ': ' + context.parsed + '件'
              }
            }
          }
        }
      },
      plugins: [{
        id: 'centerText',
        beforeDraw: function(chart: any) {
          const width = chart.width
          const height = chart.height
          const ctx = chart.ctx
          
          ctx.save()
          
          // 動態計算字體大小
          const baseSize = Math.min(width, height)
          const valueFontSize = Math.floor(baseSize * 0.18)
          const labelFontSize = Math.floor(baseSize * 0.08)
          
          // 繪製主要數值
          ctx.font = `bold ${valueFontSize}px "Noto Sans TC", sans-serif`
          ctx.textBaseline = 'middle'
          ctx.textAlign = 'center'
          ctx.fillStyle = '#1f2937'
          
          const text = feedbackData.logistics + '件'
          const textX = Math.round(width / 2)
          const textY = height / 2 - (labelFontSize * 0.7)
          
          ctx.fillText(text, textX, textY)
          
          // 繪製標籤（分兩行以避免文字過長）
          ctx.font = `normal ${labelFontSize}px "Noto Sans TC", sans-serif`
          ctx.fillStyle = '#6b7280'
          const labelY1 = textY + valueFontSize * 0.7
          const labelY2 = labelY1 + labelFontSize * 1.2
          
          ctx.fillText('物流/配送', textX, labelY1)
          ctx.fillText('相關', textX, labelY2)
          
          ctx.restore()
        }
      }]
    })
  }

  // 情緒指標比例 (Doughnut Chart)
  if (sentimentRatioChart.value) {
    // 生成模擬的情緒數據
    const sentimentData = {
      positive: 65,
      neutral: 25,
      negative: 10
    }
    
    charts.sentimentRatio = new Chart(sentimentRatioChart.value, {
      type: 'doughnut',
      data: {
        labels: ['正向', '中立', '負向'],
        datasets: [{
          data: [sentimentData.positive, sentimentData.neutral, sentimentData.negative],
          backgroundColor: [
            '#3333FF',
            '#FFC18F',
            '#FF7676'
          ],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '65%',
        animation: {
          animateRotate: true,
          animateScale: true,
          duration: 1200,
          easing: 'easeInOutQuart'
        },
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              label: function(context: any) {
                return context.label + ': ' + context.parsed + '%'
              }
            }
          }
        }
      },
      plugins: [{
        id: 'centerText',
        beforeDraw: function(chart: any) {
          const width = chart.width
          const height = chart.height
          const ctx = chart.ctx
          
          ctx.save()
          
          // 動態計算字體大小
          const baseSize = Math.min(width, height)
          const valueFontSize = Math.max(Math.floor(baseSize * 0.2), 24) // 稍大一點的比例，最小24px
          const labelFontSize = Math.max(Math.floor(baseSize * 0.09), 12) // 標籤字體大小，最小12px
          
          // 繪製主要數值
          ctx.font = `bold ${valueFontSize}px "Noto Sans TC", sans-serif`
          ctx.textBaseline = 'middle'
          ctx.textAlign = 'center'
          ctx.fillStyle = '#1f2937'
          
          const text = sentimentData.positive + '%'
          const textX = Math.round(width / 2)
          const textY = height / 2 - (labelFontSize * 0.7)
          
          ctx.fillText(text, textX, textY)
          
          // 繪製標籤
          ctx.font = `normal ${labelFontSize}px "Noto Sans TC", sans-serif`
          ctx.fillStyle = '#6b7280'
          const labelY = textY + valueFontSize * 0.7
          ctx.fillText('正向', textX, labelY)
          
          ctx.restore()
        }
      }]
    })
  }

  // 商品熱門度趨勢 (Line Chart)
  if (productTrendChart.value && dashboardData.value.trend_chart) {
    const trendChart = dashboardData.value.trend_chart
    charts.productTrend = new Chart(productTrendChart.value, {
      type: 'line',
      data: {
        labels: trendChart.data.map((item: any) => item.date),
        datasets: [{
          label: '分析數量',
          data: trendChart.data.map((item: any) => item.count),
          borderColor: 'rgb(139, 92, 246)',
          backgroundColor: 'rgba(139, 92, 246, 0.1)',
          tension: 0.2,
          borderWidth: 2,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 1500,
          easing: 'easeInOutQuart',
          delay: (context: any) => {
            return context.dataIndex * 100
          }
        },
        plugins: {
          legend: {
            position: 'bottom',
            labels: { usePointStyle: true, padding: 20, color: '#6b7280' }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: 'rgba(0, 0, 0, 0.1)' },
            ticks: { color: '#6b7280' }
          },
          x: {
            grid: { display: false },
            ticks: { color: '#6b7280' }
          }
        }
      }
    })
  }

  // 反饋次數趨勢 (Line Chart)
  if (feedbackTrendChart.value && dashboardData.value.feedback_trend_chart) {
    const feedbackTrendChartData = dashboardData.value.feedback_trend_chart
    charts.feedbackTrend = new Chart(feedbackTrendChart.value, {
      type: 'line',
      data: {
        labels: feedbackTrendChartData.data.map((item: any) => item.date),
        datasets: [{
          label: '反饋數量',
          data: feedbackTrendChartData.data.map((item: any) => item.count),
          borderColor: 'rgb(34, 197, 94)',
          backgroundColor: 'rgba(34, 197, 94, 0.1)',
          tension: 0.2,
          borderWidth: 2,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 1500,
          easing: 'easeInOutQuart',
          delay: (context: any) => {
            return context.dataIndex * 100
          }
        },
        plugins: {
          legend: {
            position: 'bottom',
            labels: { usePointStyle: true, padding: 20, color: '#6b7280' }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: 'rgba(0, 0, 0, 0.1)' },
            ticks: { color: '#6b7280' }
          },
          x: {
            grid: { display: false },
            ticks: { color: '#6b7280' }
          }
        }
      }
    })
  }

  // 情緒指標趨勢 (Line Chart) - 使用相同的趨勢數據但顏色不同
  if (sentimentTrendChart.value && dashboardData.value.trend_chart) {
    const sentimentTrendChartData = dashboardData.value.trend_chart
    charts.sentimentTrend = new Chart(sentimentTrendChart.value, {
      type: 'line',
      data: {
        labels: sentimentTrendChartData.data.map((item: any) => item.date),
        datasets: [{
          label: '情緒分析數量',
          data: sentimentTrendChartData.data.map((item: any) => item.count),
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.2,
          borderWidth: 2,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 1500,
          easing: 'easeInOutQuart',
          delay: (context: any) => {
            return context.dataIndex * 100
          }
        },
        plugins: {
          legend: {
            position: 'bottom',
            labels: { usePointStyle: true, padding: 20, color: '#6b7280' }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: 'rgba(0, 0, 0, 0.1)' },
            ticks: { color: '#6b7280' }
          },
          x: {
            grid: { display: false },
            ticks: { color: '#6b7280' }
          }
        }
      }
    })
  }
}

// 刷新數據
const refreshData = async () => {
  try {
    await loadDashboardData()
    // 清理舊圖表
    Object.values(charts).forEach(chart => chart.destroy())
    Object.keys(charts).forEach(key => delete charts[key])
    // 重新初始化圖表
    await nextTick()
    initCharts()
    ElMessage.success('數據已刷新')
  } catch (error) {
    ElMessage.error('刷新失敗')
  }
}


// 導航到分析頁面
const navigateToAnalysis = () => {
  router.push('/analysis')
}

// 組件掛載後加載數據並初始化圖表
onMounted(async () => {
  await loadDashboardData()
  await nextTick()
  // 添加延遲以實現漸進式載入效果
  setTimeout(() => {
    initCharts()
    chartsLoading.value = false
  }, 300)
})
</script>

<style scoped>
.dashboard-page {
  padding: 2rem;
  background: linear-gradient(to bottom, #f9fafb, #f3f4f6);
  min-height: 100vh;
}

.page-header {
  background: white;
  border-radius: 20px;
  padding: 2.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.08), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.04);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 2.5rem;
  font-weight: 800;
  color: #111827;
  margin: 0;
  letter-spacing: -0.025em;
}

.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}


.insights-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
}

.insight-card {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  background: white;
  border-radius: 16px;
  padding: 1.75rem;
  border-left: 5px solid;
  box-shadow: 0 2px 4px 0 rgba(0, 0, 0, 0.06);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: slideInUp 0.6s ease-out;
  animation-fill-mode: both;
}

.insight-card:nth-child(1) { animation-delay: 0.1s; }
.insight-card:nth-child(2) { animation-delay: 0.2s; }
.insight-card:nth-child(3) { animation-delay: 0.3s; }

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.insight-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px 0 rgba(0, 0, 0, 0.1);
}

.insight-card.insight-success {
  border-left-color: #10b981;
  background: #f0fdf4;
}

.insight-card.insight-warning {
  border-left-color: #f59e0b;
  background: #fffbeb;
}

.insight-card.insight-info {
  border-left-color: #3b82f6;
  background: #eff6ff;
}

.insight-icon {
  margin-top: 0.25rem;
  font-size: 1.5rem;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

.insight-content p {
  margin: 0;
  color: #374151;
  line-height: 1.7;
  font-size: 0.95rem;
}

.charts-section {
  margin-bottom: 2.5rem;
  position: relative;
}

/* 添加區域分隔線 */
.charts-section::after {
  content: '';
  position: absolute;
  bottom: -1.25rem;
  left: 50%;
  transform: translateX(-50%);
  width: 60px;
  height: 3px;
  background: linear-gradient(to right, transparent, #e5e7eb, transparent);
  border-radius: 2px;
}

.charts-section:last-child::after {
  display: none;
}

.top-charts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.circular-charts {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
}

.trend-charts {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.chart-container {
  background: white;
  border-radius: 20px;
  padding: 2rem;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.08), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(0, 0, 0, 0.04);
}

.chart-container {
  position: relative;
  overflow: hidden;
}

.chart-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  transition: left 0.5s;
}

.chart-container:hover::before {
  left: 100%;
}

.chart-container:hover {
  transform: translateY(-6px) scale(1.02);
  box-shadow: 0 12px 20px -5px rgba(0, 0, 0, 0.15), 0 8px 10px -5px rgba(0, 0, 0, 0.04);
  border-color: rgba(37, 99, 235, 0.2);
}

.chart-container.small {
  padding: 1.75rem;
  display: flex;
  flex-direction: column;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.chart-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
  margin: 0;
  letter-spacing: -0.025em;
}

.chart-top-label {
  font-size: 0.875rem;
  color: #10b981;
  font-weight: 600;
  padding: 0.25rem 0.75rem;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 12px;
  letter-spacing: 0.025em;
}

.clickable-hint {
  font-size: 0.875rem;
  color: #3b82f6;
  cursor: pointer;
  transition: all 0.2s;
  padding: 0.25rem 0.5rem;
  border-radius: 8px;
}

.clickable-hint:hover {
  color: #1d4ed8;
  background: rgba(59, 130, 246, 0.1);
  transform: translateX(2px);
}

.chart-wrapper {
  position: relative;
  height: 300px;
  width: 100%;
}

.chart-wrapper.small {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Loading Skeleton */
.chart-skeleton {
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, #f3f4f6 25%, #e5e7eb 50%, #f3f4f6 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
  border-radius: 8px;
}

.chart-skeleton.circular {
  border-radius: 50%;
  width: 150px;
  height: 150px;
  margin: 25px auto;
}

@keyframes loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

/* 響應式設計 */
@media (max-width: 1280px) {
  .circular-charts {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 1024px) {
  .top-charts {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .circular-charts {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .chart-container {
    padding: 1.5rem;
  }
  
  .chart-wrapper {
    height: 250px;
  }
}

@media (max-width: 768px) {
  .dashboard-page {
    padding: 1rem;
  }
  
  .page-header {
    padding: 1.5rem;
    border-radius: 16px;
  }
  
  .page-title {
    font-size: 1.875rem;
  }
  
  .header-content {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: center;
  }
  
  .circular-charts {
    grid-template-columns: 1fr;
  }
  
  .chart-container {
    padding: 1.25rem;
    border-radius: 16px;
  }
  
  .chart-title {
    font-size: 1.125rem;
  }
  
  .chart-wrapper {
    height: 200px;
  }
  
  .chart-wrapper.small {
    height: 180px;
  }
  
  .insights-section {
    gap: 0.75rem;
  }
  
  .insight-card {
    padding: 1.25rem;
    gap: 0.75rem;
  }
  
  .insight-content p {
    font-size: 0.875rem;
  }
}

@media (max-width: 480px) {
  .dashboard-page {
    padding: 0.75rem;
  }
  
  .page-title {
    font-size: 1.5rem;
  }
  
  .chart-container {
    padding: 1rem;
  }
  
  .chart-wrapper {
    height: 180px;
  }
  
  .chart-wrapper.small {
    height: 160px;
  }
}
</style>