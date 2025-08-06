import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { 
  DataSourceItem, 
  DataSourceFilter, 
  SortConfig,
  Pagination,
  UploadOptions,
  BatchOperation 
} from '@/types/datasource'
import { dataSourceService } from '@/services/datasource.service'
import { ElMessage } from 'element-plus'

export const useDataSourceStore = defineStore('datasource', () => {
  // 状态
  const items = ref<DataSourceItem[]>([])
  const loading = ref(false)
  const error = ref('')
  
  // 筛选和分页
  const filters = ref<DataSourceFilter>({})
  const pagination = ref<Pagination>({
    page: 1,
    size: 20,
    total: 0,
    pages: 0
  })
  
  // 排序
  const sort = ref<SortConfig>({
    field: 'uploadTime',
    order: 'desc'
  })

  // 计算属性
  const hasData = computed(() => items.value.length > 0)
  const processingCount = computed(() => 
    items.value.filter(item => item.status === 'analyzing' || item.status === 'pending').length
  )
  const completedCount = computed(() => 
    items.value.filter(item => item.status === 'completed').length
  )
  const failedCount = computed(() => 
    items.value.filter(item => item.status === 'failed').length
  )
  
  // 自動重試相關狀態
  const autoRetryEnabled = ref(true)
  
  // 獲取失敗的檔案ID列表
  const getFailedFileIds = computed(() => 
    items.value.filter(item => item.status === 'failed').map(item => item.id)
  )

  // 获取数据源列表
  const fetchDataSourceList = async (refresh = false) => {
    if (loading.value && !refresh) return

    loading.value = true
    error.value = ''

    try {
      const response = await dataSourceService.getDataSourceList(
        pagination.value.page,
        pagination.value.size,
        filters.value,
        sort.value
      )

      items.value = response.items
      pagination.value = response.pagination

    } catch (err: any) {
      error.value = err.message || '獲取數據源列表失敗'
      ElMessage.error('獲取檔案列表失敗')
    } finally {
      loading.value = false
    }
  }

  // 上传文件
  const uploadFile = async (file: File, options: UploadOptions, onProgress?: (progress: number) => void) => {
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('autoAnalyze', options.autoAnalyze.toString())
      formData.append('notifyOnComplete', options.notifyOnComplete.toString())

      const response = await dataSourceService.uploadFile(formData, onProgress)
      
      // 刷新列表
      await fetchDataSourceList()
      
      return response
    } catch (err: any) {
      throw new Error(err.message || '檔案上傳失敗')
    }
  }

  // 删除数据源
  const deleteDataSource = async (id: string) => {
    try {
      await dataSourceService.deleteDataSource(id)
      
      // 从列表中移除
      const index = items.value.findIndex(item => item.id === id)
      if (index > -1) {
        items.value.splice(index, 1)
        pagination.value.total--
      }
    } catch (err: any) {
      throw new Error(err.message || '刪除檔案失敗')
    }
  }

  // 批量删除数据源
  const batchDeleteDataSource = async (ids: string[]) => {
    try {
      await dataSourceService.batchDelete(ids)
      
      // 从列表中移除
      items.value = items.value.filter(item => !ids.includes(item.id))
      pagination.value.total -= ids.length
    } catch (err: any) {
      throw new Error(err.message || '批次刪除失敗')
    }
  }

  // 重试分析
  const retryAnalysis = async (id: string) => {
    try {
      const item = items.value.find(item => item.id === id)
      
      console.log('Store: Starting retry analysis for file:', id)
      console.log('Store: Current item status before retry:', item?.status)
      
      await dataSourceService.retryAnalysis(id)
      
      // 更新状态為 pending（待分析）
      if (item) {
        item.status = 'pending'
        item.errorMessage = undefined
        console.log('Store: Updated item status to pending')
      }
      
      // 立即刷新數據以獲取最新狀態
      await fetchDataSourceList(true)
      
    } catch (err: any) {
      console.error('Store: Retry analysis failed:', err)
      throw new Error(err.message || '重試分析失敗')
    }
  }

  // 批量分析
  const batchAnalyze = async (ids: string[]) => {
    try {
      await dataSourceService.batchAnalyze(ids)
      
      // 更新状态
      items.value.forEach(item => {
        if (ids.includes(item.id)) {
          item.status = 'pending'
          item.errorMessage = undefined
        }
      })
    } catch (err: any) {
      throw new Error(err.message || '批次分析提交失敗')
    }
  }

  // 获取文件详情
  const getDataSourceDetail = async (id: string) => {
    try {
      return await dataSourceService.getDataSourceDetail(id)
    } catch (err: any) {
      throw new Error(err.message || '獲取檔案詳情失敗')
    }
  }

  // 设置筛选条件
  const setFilters = (newFilters: Partial<DataSourceFilter>) => {
    filters.value = { ...filters.value, ...newFilters }
    pagination.value.page = 1 // 重置到第一页
    fetchDataSourceList()
  }

  // 清除筛选条件
  const clearFilters = () => {
    filters.value = {}
    pagination.value.page = 1
    fetchDataSourceList()
  }

  // 设置排序
  const setSort = (newSort: SortConfig) => {
    sort.value = newSort
    fetchDataSourceList()
  }

  // 设置分页
  const setPagination = (page: number, size?: number) => {
    pagination.value.page = page
    if (size) pagination.value.size = size
    fetchDataSourceList()
  }

  // 刷新数据
  const refreshData = () => {
    fetchDataSourceList(true)
  }

  // 自動重試失敗的檔案（簡化版）
  const autoRetryFailedFiles = async () => {
    if (!autoRetryEnabled.value || failedCount.value === 0) {
      return
    }

    try {
      const failedIds = getFailedFileIds.value
      if (failedIds.length > 0) {
        console.log(`自動重試 ${failedIds.length} 個失敗的檔案:`, failedIds)
        
        // 逐個重試失敗的檔案
        for (const id of failedIds) {
          try {
            await retryAnalysis(id)
          } catch (error) {
            console.error(`自動重試檔案 ${id} 失敗:`, error)
          }
        }
        
        ElMessage.info(`已自動重試 ${failedIds.length} 個失敗的檔案`)
        
        // 重試後開始輪詢檢查
        startPolling()
      }
    } catch (error) {
      console.error('自動重試過程中發生錯誤:', error)
    }
  }

  // 輪詢檢查處理狀態（簡化版）
  const startPolling = () => {
    const poll = () => {
      if (processingCount.value > 0) {
        // 還有檔案在處理中，繼續輪詢
        fetchDataSourceList(true)
        setTimeout(poll, 5000) // 每5秒检查一次
      } else {
        // 所有處理任務完成，檢查是否需要自動重試
        if (failedCount.value > 0 && autoRetryEnabled.value) {
          console.log('所有分析完成，發現失敗檔案，啟動自動重試')
          autoRetryFailedFiles()
        }
      }
    }
    
    if (processingCount.value > 0) {
      setTimeout(poll, 5000)
    }
  }

  // 获取模拟数据
  const getMockData = () => {
    items.value = [
      {
        id: '1',
        fileName: '001.wav',
        fileType: 'wav',
        fileSize: 2543234,
        uploadTime: '2025-07-04 12:47:28',
        uploader: 'user1',
        uploaderName: '權限人員 01',
        status: 'analyzing',
        progress: 65,
        analysisResult: {
          productLabels: ['包子', '饅頭'],
          feedbackLabels: ['物流/配送'],
          sentiment: 'positive',
          summary: '分析中...',
          confidence: 0
        }
      },
      {
        id: '2',
        fileName: '002.wav',
        fileType: 'wav',
        fileSize: 1823456,
        uploadTime: '2025-07-04 12:47:18',
        uploader: 'user2',
        uploaderName: '權限人員 02',
        status: 'completed',
        analysisResult: {
          productLabels: ['包子', '饅頭'],
          feedbackLabels: ['物流/配送', '口味研發'],
          sentiment: 'negative',
          summary: '顧客對於冷凍湯包開口好的設計表示讚賞...',
          confidence: 0.92
        }
      },
      {
        id: '3',
        fileName: '003.wav',
        fileType: 'wav',
        fileSize: 3456789,
        uploadTime: '2025-07-04 12:47:17',
        uploader: 'user2',
        uploaderName: '權限人員 02',
        status: 'pending'
      },
      {
        id: '4',
        fileName: '客戶回饋_20250630.txt',
        fileType: 'txt',
        fileSize: 12543,
        uploadTime: '2025-06-30 10:30:00',
        uploader: 'user3',
        uploaderName: '權限人員 03',
        status: 'completed',
        analysisResult: {
          productLabels: ['水餃'],
          feedbackLabels: ['包裝設計'],
          sentiment: 'positive',
          summary: '顧客對新包裝設計表示滿意...',
          confidence: 0.88
        }
      },
      {
        id: '5',
        fileName: '語音留言_001.mp3',
        fileType: 'mp3',
        fileSize: 892345,
        uploadTime: '2025-07-01 15:20:30',
        uploader: 'user1',
        uploaderName: '權限人員 01',
        status: 'failed',
        errorMessage: '音檔格式不支援，請使用標準 MP3 格式'
      },
      {
        id: '6',
        fileName: '客服對話_20250702.wav',
        fileType: 'wav',
        fileSize: 4567890,
        uploadTime: '2025-07-02 09:15:45',
        uploader: 'user1',
        uploaderName: '權限人員 01',
        status: 'completed',
        analysisResult: {
          productLabels: ['饅頭', '包子'],
          feedbackLabels: ['客服態度', '物流/配送'],
          sentiment: 'neutral',
          summary: '客戶詢問物流配送問題，客服人員給予適當回應...',
          confidence: 0.76
        }
      }
    ]

    pagination.value = {
      page: 1,
      size: 20,
      total: 6,
      pages: 1
    }

    loading.value = false
  }

  return {
    // 状态
    items: readonly(items),
    loading: readonly(loading),
    error: readonly(error),
    
    // 配置
    filters: readonly(filters),
    pagination: readonly(pagination),
    sort: readonly(sort),
    
    // 计算属性
    hasData,
    processingCount,
    completedCount,
    failedCount,
    getFailedFileIds,
    
    // 自動重試狀態
    autoRetryEnabled: readonly(autoRetryEnabled),
    
    // 方法
    fetchDataSourceList,
    uploadFile,
    deleteDataSource,
    batchDeleteDataSource,
    retryAnalysis,
    batchAnalyze,
    getDataSourceDetail,
    setFilters,
    clearFilters,
    setSort,
    setPagination,
    refreshData,
    startPolling,
    getMockData,
    
    // 自動重試方法（簡化版）
    autoRetryFailedFiles
  }
})