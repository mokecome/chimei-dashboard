import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { 
  DashboardMetrics, 
  ChartData, 
  DashboardFilter,
  AIInsight,
  HotProduct,
  FeedbackCategory 
} from '@/types/dashboard'
import { dashboardService } from '@/services/dashboard.service'
import { ElMessage } from 'element-plus'

export const useDashboardStore = defineStore('dashboard', () => {
  // 状态
  const metrics = ref<DashboardMetrics | null>(null)
  const charts = ref<ChartData[]>([])
  const insights = ref<AIInsight[]>([])
  const loading = ref(false)
  const error = ref('')
  const filters = ref<DashboardFilter>({})
  const lastUpdateTime = ref<string>('')

  // 计算属性
  const hasData = computed(() => !!metrics.value)
  
  const sentimentDistribution = computed(() => {
    if (!metrics.value) return null
    return {
      positive: metrics.value.positiveRatio,
      negative: metrics.value.negativeRatio,
      neutral: metrics.value.neutralRatio
    }
  })

  // 获取仪表板数据
  const fetchDashboardData = async (forceRefresh = false) => {
    if (loading.value && !forceRefresh) return

    loading.value = true
    error.value = ''

    try {
      // 獲取 metrics 和 charts 數據
      const [metricsData, chartsData] = await Promise.all([
        dashboardService.getMetrics(filters.value),
        dashboardService.getChartData(filters.value)
      ])

      metrics.value = metricsData
      charts.value = chartsData
      
      // 嘗試獲取 AI insights，如果失敗則使用模擬數據
      try {
        const insightsData = await dashboardService.getAIInsights(filters.value)
        insights.value = insightsData
      } catch (insightError) {
        console.warn('AI insights API not available, using mock data')
        // 使用模擬數據
        insights.value = [
          {
            id: '1',
            type: 'success',
            title: '客訴量改善',
            content: '客訴量較上週下降2.3%，主要歸因於配送效率提升。建議持續優化物流系統。',
            priority: 1
          },
          {
            id: '2',
            type: 'warning',
            title: '商品反饋關注',
            content: '偵測到產品質量相關反饋增加，建議加強品質控制。',
            priority: 2
          },
          {
            id: '3',
            type: 'info',
            title: '趨勢分析',
            content: '本月整體客戶滿意度呈上升趨勢，持續保持良好服務品質。',
            priority: 3
          }
        ]
      }
      
      lastUpdateTime.value = new Date().toLocaleString('zh-TW')

    } catch (err: any) {
      error.value = err.message || '获取数据失败'
      ElMessage.error('獲取儀表板數據失敗')
    } finally {
      loading.value = false
    }
  }

  // 设置过滤条件
  const setFilters = (newFilters: Partial<DashboardFilter>) => {
    filters.value = { ...filters.value, ...newFilters }
    fetchDashboardData()
  }

  // 清除过滤条件
  const clearFilters = () => {
    filters.value = {}
    fetchDashboardData()
  }

  // 刷新数据
  const refreshData = () => {
    fetchDashboardData(true)
  }

  // 处理图表点击事件
  const handleChartClick = (chartId: string, params: any) => {
    console.log('Chart clicked:', chartId, params)
    
    // 根据图表类型和点击的数据构建跳转参数
    const filters: any = {}
    
    switch (chartId) {
      case 'hotProducts':
        filters.productLabels = [params.name]
        break
      case 'feedbackRanking':
        filters.feedbackLabels = [params.name]
        break
      case 'sentimentRatio':
        filters.sentiment = params.name === '正面' ? 'positive' : 
                          params.name === '負面' ? 'negative' : 'neutral'
        break
      default:
        console.log('Unknown chart:', chartId)
        return
    }

    // 这里应该跳转到分析页面并应用过滤条件
    // 由于我们在 store 中，无法直接使用 router
    // 可以通过事件总线或者在组件中处理
    return { route: '/analysis', filters }
  }

  // 获取模拟数据
  const getMockData = () => {
    metrics.value = {
      totalFiles: 2456,
      totalAnalyses: 2180,
      positiveRatio: 65,
      negativeRatio: 20,
      neutralRatio: 15,
      todayUploads: 45,
      weeklyGrowth: 12.5
    }

    insights.value = [
      {
        id: '1',
        type: 'success',
        title: '客訴量改善',
        content: '客訴量較上週下降2.3%，主要歸因於配送效率提升。建議持續優化物流系統，預計可進一步降低15%客訴率。',
        priority: 1
      },
      {
        id: '2',
        type: 'warning',
        title: '商品反饋關注',
        content: '偵測到1.2個月，月增5%，鑑觀主要業主通道改革，建議持續提升營運效率並加強供應鏈整合性。',
        priority: 2
      },
      {
        id: '3',
        type: 'info',
        title: '趨勢分析',
        content: '統計顯示1.2個月，月增5%，鑑觀主要業主通道改革建議持續提升營運效率並加強供應鏈結之基礎設施將持續支援開發運行推動投資能力。',
        priority: 3
      }
    ]

    lastUpdateTime.value = new Date().toLocaleString('zh-TW')
    loading.value = false
  }

  return {
    // 状态
    metrics: readonly(metrics),
    charts: readonly(charts),
    insights: readonly(insights),
    loading: readonly(loading),
    error: readonly(error),
    filters: readonly(filters),
    lastUpdateTime: readonly(lastUpdateTime),
    
    // 计算属性
    hasData,
    sentimentDistribution,
    
    // 方法
    fetchDashboardData,
    setFilters,
    clearFilters,
    refreshData,
    handleChartClick,
    getMockData
  }
})