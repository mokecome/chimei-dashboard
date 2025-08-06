import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { 
  AnalysisItem, 
  AnalysisFilter, 
  AnalysisStats,
  SortConfig,
  ColumnConfig,
  ChartDimension,
  AnalysisChartConfig
} from '@/types/analysis'
import { analysisService } from '@/services/analysis.service'
import { ElMessage } from 'element-plus'

export const useAnalysisStore = defineStore('analysis', () => {
  // 状态
  const items = ref<AnalysisItem[]>([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref('')
  
  // 筛选和分页
  const filters = ref<AnalysisFilter>({})
  const pagination = ref({
    page: 1,
    size: 20,
    total: 0,
    pages: 0
  })
  
  // 排序和列配置
  const sort = ref<SortConfig>({
    field: 'uploadTime',
    order: 'desc'
  })
  
  const columns = ref<ColumnConfig[]>([
    { field: 'fileName', label: '檔案名稱', visible: true, sortable: true },
    { field: 'uploadTime', label: '建立時間', visible: true, sortable: true },
    { field: 'feedbackLabels', label: '回饋分類', visible: true, sortable: false },
    { field: 'productLabels', label: '商品分類', visible: true, sortable: false },
    { field: 'sentiment', label: '評價傾向', visible: true, sortable: true },
    { field: 'summary', label: '摘要', visible: true, sortable: false },
    { field: 'uploaderName', label: '上傳者', visible: true, sortable: true },
    { field: 'actions', label: '詳細內容', visible: true, sortable: false }
  ])
  
  // 统计数据
  const stats = ref<AnalysisStats | null>(null)
  
  // 图表相关
  const chartDimensions = ref<ChartDimension[]>([
    {
      id: 'dimension1',
      name: '維度一',
      type: 'product',
      items: ['包子', '饅頭']
    },
    {
      id: 'dimension2', 
      name: '維度二',
      type: 'sentiment',
      items: ['正面', '負面']
    }
  ])
  
  const chartConfig = ref<AnalysisChartConfig>({
    type: 'line',
    dimensions: chartDimensions.value
  })
  
  const chartData = ref<any>(null)
  
  // 可选项数据
  const productLabels = ref<string[]>([])
  const feedbackLabels = ref<string[]>([])
  const uploaders = ref<Array<{ id: string, name: string }>>([])

  // 计算属性
  const hasData = computed(() => items.value.length > 0)
  const visibleColumns = computed(() => columns.value.filter(col => col.visible))
  
  const sentimentDistribution = computed(() => {
    if (!stats.value) return { positive: 0, negative: 0, neutral: 0 }
    return stats.value.sentimentDistribution
  })

  // 获取分析数据列表
  const fetchAnalysisData = async (refresh = false) => {
    if (loading.value && !refresh) return

    loading.value = true
    error.value = ''

    try {
      const response = await analysisService.getAnalysisList(
        pagination.value.page,
        pagination.value.size,
        filters.value,
        sort.value
      )

      items.value = response.items
      pagination.value = response.pagination
      total.value = response.pagination.total

    } catch (err: any) {
      error.value = err.message || '获取分析数据失败'
      ElMessage.error('獲取分析數據失敗')
    } finally {
      loading.value = false
    }
  }

  // 获取统计数据
  const fetchStats = async () => {
    try {
      stats.value = await analysisService.getAnalysisStats(filters.value)
    } catch (err: any) {
      console.error('Failed to fetch stats:', err)
    }
  }

  // 获取图表数据
  const fetchChartData = async () => {
    try {
      const dimensions = chartDimensions.value.flatMap(d => d.items)
      chartData.value = await analysisService.getChartData(
        dimensions,
        chartConfig.value.type,
        filters.value
      )
    } catch (err: any) {
      console.error('Failed to fetch chart data:', err)
    }
  }

  // 获取选项数据
  const fetchOptions = async () => {
    try {
      const [products, feedbacks, users] = await Promise.all([
        analysisService.getProductLabels(),
        analysisService.getFeedbackLabels(),
        analysisService.getUploaders()
      ])
      
      productLabels.value = products
      feedbackLabels.value = feedbacks
      uploaders.value = users
    } catch (err: any) {
      console.error('Failed to fetch options:', err)
    }
  }

  // 设置筛选条件
  const setFilters = (newFilters: Partial<AnalysisFilter>) => {
    filters.value = { ...filters.value, ...newFilters }
    pagination.value.page = 1 // 重置到第一页
    fetchAnalysisData()
    fetchStats()
    fetchChartData()
  }

  // 清除筛选条件
  const clearFilters = () => {
    filters.value = {}
    pagination.value.page = 1
    fetchAnalysisData()
    fetchStats()
    fetchChartData()
  }

  // 设置排序
  const setSort = (newSort: SortConfig) => {
    sort.value = newSort
    fetchAnalysisData()
  }

  // 设置分页
  const setPagination = (page: number, size?: number) => {
    pagination.value.page = page
    if (size) pagination.value.size = size
    fetchAnalysisData()
  }

  // 更新列配置
  const updateColumns = (newColumns: ColumnConfig[]) => {
    columns.value = newColumns
  }

  // 更新图表维度
  const updateChartDimensions = (dimensions: ChartDimension[]) => {
    chartDimensions.value = dimensions
    chartConfig.value.dimensions = dimensions
    fetchChartData()
  }

  // 更新图表类型
  const updateChartType = (type: string) => {
    chartConfig.value.type = type as any
    fetchChartData()
  }

  // 导出报表
  const exportReport = async (format: 'xlsx' | 'csv' = 'xlsx') => {
    try {
      const columnFields = visibleColumns.value
        .filter(col => col.field !== 'actions')
        .map(col => col.field)

      const blob = await analysisService.exportReport({
        format,
        includeColumns: columnFields,
        filters: filters.value,
        fileName: `分析報表_${new Date().toISOString().split('T')[0]}`
      })

      // 创建下载链接
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `分析報表_${new Date().toISOString().split('T')[0]}.${format}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      ElMessage.success('報表匯出成功')
    } catch (err: any) {
      ElMessage.error('報表匯出失敗')
    }
  }

  // 刷新数据
  const refreshData = () => {
    fetchAnalysisData(true)
    fetchStats()
    fetchChartData()
  }

  // 获取模拟数据
  const getMockData = () => {
    items.value = [
      {
        id: '1',
        fileName: '001.wav',
        fileType: 'wav',
        productLabels: ['包子', '饅頭'],
        feedbackLabels: ['物流/配送', '口味研發'],
        sentiment: 'positive',
        summary: '顧客對於冷凍湯包開口好的...',
        uploader: 'user1',
        uploaderName: '權限人員 01',
        uploadTime: '2025-07-04 12:47:28',
        confidence: 0.85
      },
      {
        id: '2',
        fileName: '002.wav',
        fileType: 'wav',
        productLabels: ['包子', '饅頭'],
        feedbackLabels: ['物流/配送', '口味研發'],
        sentiment: 'negative',
        summary: '顧客對於冷凍湯包開口好的...',
        uploader: 'user2',
        uploaderName: '權限人員 02',
        uploadTime: '2025-07-04 12:47:18',
        confidence: 0.92
      },
      {
        id: '3',
        fileName: '003.wav',
        fileType: 'wav',
        productLabels: ['包子', '饅頭'],
        feedbackLabels: ['物流/配送', '口味研發', '活動價惠'],
        sentiment: 'negative',
        summary: '顧客對於冷凍湯包開口好的...',
        uploader: 'user2',
        uploaderName: '權限人員 02',
        uploadTime: '2025-07-04 12:47:17',
        confidence: 0.78
      },
      {
        id: '4',
        fileName: '123.wav',
        fileType: 'wav',
        productLabels: ['包子'],
        feedbackLabels: ['物流/配送'],
        sentiment: 'positive',
        summary: '顧客對於冷凍湯包開口好的...',
        uploader: 'user3',
        uploaderName: '權限人員 03',
        uploadTime: '2025-06-30 10:30:00',
        confidence: 0.88
      },
      {
        id: '5',
        fileName: '234.wav',
        fileType: 'wav',
        productLabels: ['包子', '饅頭'],
        feedbackLabels: ['物流/配送', '口味研發'],
        sentiment: 'positive',
        summary: '顧客對於冷凍湯包開口好的...',
        uploader: 'user1',
        uploaderName: '權限人員 01',
        uploadTime: '2025-07-04 12:47:28',
        confidence: 0.95
      }
    ]

    pagination.value = {
      page: 1,
      size: 20,
      total: 5,
      pages: 1
    }

    stats.value = {
      totalCount: 5,
      sentimentDistribution: {
        positive: 3,
        negative: 2,
        neutral: 0
      },
      topProducts: [
        { name: '包子', count: 5 },
        { name: '饅頭', count: 4 }
      ],
      topFeedbacks: [
        { name: '物流/配送', count: 5 },
        { name: '口味研發', count: 4 },
        { name: '活動價惠', count: 1 }
      ],
      uploaderStats: [
        { name: '權限人員 01', count: 2 },
        { name: '權限人員 02', count: 2 },
        { name: '權限人員 03', count: 1 }
      ]
    }

    productLabels.value = ['包子', '饅頭', '水餃', '蒸餃']
    feedbackLabels.value = ['物流/配送', '口味研發', '活動價惠', '包裝設計', '客服態度']
    uploaders.value = [
      { id: 'user1', name: '權限人員 01' },
      { id: 'user2', name: '權限人員 02' },
      { id: 'user3', name: '權限人員 03' }
    ]

    // 模拟图表数据
    chartData.value = {
      labels: ['2025.06.30', '2025.07.01', '2025.07.02', '2025.07.03', '2025.07.04', '2025.07.05', '2025.07.06'],
      datasets: [{
        label: '包子',
        data: [75, 65, 55, 50, 45, 55, 50],
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        tension: 0.4
      }, {
        label: '饅頭',
        data: [50, 45, 95, 80, 75, 65, 45],
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        borderWidth: 2,
        tension: 0.4
      }, {
        label: '正面',
        data: [60, 70, 85, 75, 80, 105, 75],
        borderColor: '#8b5cf6',
        backgroundColor: 'rgba(139, 92, 246, 0.1)',
        borderWidth: 2,
        tension: 0.4
      }, {
        label: '負面',
        data: [85, 75, 70, 80, 85, 90, 80],
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        borderWidth: 2,
        tension: 0.4
      }]
    }

    loading.value = false
  }

  return {
    // 状态
    items: readonly(items),
    total: readonly(total),
    loading: readonly(loading),
    error: readonly(error),
    
    // 配置
    filters: readonly(filters),
    pagination: readonly(pagination),
    sort: readonly(sort),
    columns: readonly(columns),
    
    // 统计和图表
    stats: readonly(stats),
    chartDimensions: readonly(chartDimensions),
    chartConfig: readonly(chartConfig),
    chartData: readonly(chartData),
    
    // 选项数据
    productLabels: readonly(productLabels),
    feedbackLabels: readonly(feedbackLabels),
    uploaders: readonly(uploaders),
    
    // 计算属性
    hasData,
    visibleColumns,
    sentimentDistribution,
    
    // 方法
    fetchAnalysisData,
    fetchStats,
    fetchChartData,
    fetchOptions,
    setFilters,
    clearFilters,
    setSort,
    setPagination,
    updateColumns,
    updateChartDimensions,
    updateChartType,
    exportReport,
    refreshData,
    getMockData
  }
})