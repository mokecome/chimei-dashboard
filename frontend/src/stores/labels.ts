import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { 
  ProductLabel, 
  FeedbackLabel, 
  LabelOperation,
  LabelSettings,
  LabelStats,
  BulkLabelOperation,
  ImportLabelData,
  ExportLabelOptions
} from '@/types/labels'
import { labelsService } from '@/services/labels.service'
import { ElMessage } from 'element-plus'

export const useLabelsStore = defineStore('labels', () => {
  // 状态
  const productLabels = ref<ProductLabel[]>([])
  const feedbackLabels = ref<FeedbackLabel[]>([])
  const operations = ref<LabelOperation[]>([])
  const loading = ref(false)
  const error = ref('')
  
  // 设置和限制
  const settings = ref<LabelSettings>({
    productLabels: [],
    feedbackLabels: [],
    defaultFeedbackCategories: [
      '產品規格',
      '調理方式', 
      '通路物流',
      '客服態度',
      '價格促銷',
      '包裝設計',
      '營業資訊'
    ],
    limits: {
      maxProductLabels: 200,
      maxFeedbackLabels: 30,
      maxProductLabelLength: 20,
      maxFeedbackLabelLength: 15
    }
  })

  // 统计信息
  const stats = ref<LabelStats | null>(null)

  // 计算属性
  const activeProductLabels = computed(() => 
    productLabels.value.filter(label => label.isActive)
  )
  
  const activeFeedbackLabels = computed(() => 
    feedbackLabels.value.filter(label => label.isActive)
  )
  
  const productLabelCount = computed(() => productLabels.value.length)
  const feedbackLabelCount = computed(() => feedbackLabels.value.length)
  
  const canAddProductLabel = computed(() => 
    productLabelCount.value < settings.value.limits.maxProductLabels
  )
  
  const canAddFeedbackLabel = computed(() => 
    feedbackLabelCount.value < settings.value.limits.maxFeedbackLabels
  )

  const feedbackLabelsByCategory = computed(() => {
    const grouped: Record<string, FeedbackLabel[]> = {}
    feedbackLabels.value.forEach(label => {
      const category = label.category || '其他'
      if (!grouped[category]) {
        grouped[category] = []
      }
      grouped[category].push(label)
    })
    return grouped
  })

  // 获取所有标签数据
  const fetchLabels = async () => {
    loading.value = true
    error.value = ''

    try {
      const [products, feedbacks, labelsStats] = await Promise.all([
        labelsService.getProductLabels(),
        labelsService.getFeedbackLabels(),
        labelsService.getLabelStats()
      ])

      productLabels.value = products
      feedbackLabels.value = feedbacks
      stats.value = labelsStats

    } catch (err: any) {
      error.value = err.message || '获取标签数据失败'
      ElMessage.error('獲取標籤數據失敗')
    } finally {
      loading.value = false
    }
  }

  // 获取操作历史
  const fetchOperations = async (limit = 50) => {
    try {
      operations.value = await labelsService.getLabelOperations(limit)
    } catch (err: any) {
      console.error('Failed to fetch operations:', err)
    }
  }

  // 添加商品标签
  const addProductLabel = async (name: string, description?: string) => {
    try {
      // 验证
      if (!canAddProductLabel.value) {
        throw new Error(`商品標籤已達上限 ${settings.value.limits.maxProductLabels} 個`)
      }

      if (name.length > settings.value.limits.maxProductLabelLength) {
        throw new Error(`商品標籤長度不能超過 ${settings.value.limits.maxProductLabelLength} 個字`)
      }

      // 检查重复
      if (productLabels.value.some(label => label.name === name)) {
        throw new Error('標籤名稱已存在')
      }

      const newLabel = await labelsService.createProductLabel({ name, description })
      productLabels.value.push(newLabel)
      
      ElMessage.success('商品標籤新增成功')
      return newLabel

    } catch (err: any) {
      ElMessage.error(err.message || '新增商品標籤失敗')
      throw err
    }
  }

  // 添加反馈标签
  const addFeedbackLabel = async (name: string, category: string, description?: string) => {
    try {
      // 验证
      if (!canAddFeedbackLabel.value) {
        throw new Error(`反饋標籤已達上限 ${settings.value.limits.maxFeedbackLabels} 個`)
      }

      if (name.length > settings.value.limits.maxFeedbackLabelLength) {
        throw new Error(`反饋標籤長度不能超過 ${settings.value.limits.maxFeedbackLabelLength} 個字`)
      }

      // 检查重复
      if (feedbackLabels.value.some(label => label.name === name)) {
        throw new Error('標籤名稱已存在')
      }

      const newLabel = await labelsService.createFeedbackLabel({ name, category, description })
      feedbackLabels.value.push(newLabel)
      
      ElMessage.success('反饋標籤新增成功')
      return newLabel

    } catch (err: any) {
      ElMessage.error(err.message || '新增反饋標籤失敗')
      throw err
    }
  }

  // 更新商品标签
  const updateProductLabel = async (id: string, data: Partial<ProductLabel>) => {
    try {
      const updatedLabel = await labelsService.updateProductLabel(id, data)
      const index = productLabels.value.findIndex(label => label.id === id)
      if (index > -1) {
        productLabels.value[index] = updatedLabel
      }
      ElMessage.success('商品標籤更新成功')
      return updatedLabel
    } catch (err: any) {
      ElMessage.error(err.message || '更新商品標籤失敗')
      throw err
    }
  }

  // 更新反馈标签
  const updateFeedbackLabel = async (id: string, data: Partial<FeedbackLabel>) => {
    try {
      const updatedLabel = await labelsService.updateFeedbackLabel(id, data)
      const index = feedbackLabels.value.findIndex(label => label.id === id)
      if (index > -1) {
        feedbackLabels.value[index] = updatedLabel
      }
      ElMessage.success('反饋標籤更新成功')
      return updatedLabel
    } catch (err: any) {
      ElMessage.error(err.message || '更新反饋標籤失敗')
      throw err
    }
  }

  // 删除商品标签
  const deleteProductLabel = async (id: string) => {
    try {
      await labelsService.deleteProductLabel(id)
      productLabels.value = productLabels.value.filter(label => label.id !== id)
      ElMessage.success('商品標籤刪除成功')
    } catch (err: any) {
      ElMessage.error(err.message || '刪除商品標籤失敗')
      throw err
    }
  }

  // 删除反馈标签
  const deleteFeedbackLabel = async (id: string) => {
    try {
      await labelsService.deleteFeedbackLabel(id)
      feedbackLabels.value = feedbackLabels.value.filter(label => label.id !== id)
      ElMessage.success('反饋標籤刪除成功')
    } catch (err: any) {
      ElMessage.error(err.message || '刪除反饋標籤失敗')
      throw err
    }
  }

  // 批量操作
  const bulkOperation = async (operation: BulkLabelOperation) => {
    try {
      await labelsService.bulkOperation(operation)
      
      // 根据操作类型更新本地状态
      if (operation.targetType === 'product') {
        if (operation.type === 'delete') {
          productLabels.value = productLabels.value.filter(
            label => !operation.items.includes(label.id)
          )
        } else if (operation.type === 'activate' || operation.type === 'deactivate') {
          productLabels.value.forEach(label => {
            if (operation.items.includes(label.id)) {
              label.isActive = operation.type === 'activate'
            }
          })
        }
      } else {
        if (operation.type === 'delete') {
          feedbackLabels.value = feedbackLabels.value.filter(
            label => !operation.items.includes(label.id)
          )
        } else if (operation.type === 'activate' || operation.type === 'deactivate') {
          feedbackLabels.value.forEach(label => {
            if (operation.items.includes(label.id)) {
              label.isActive = operation.type === 'activate'
            }
          })
        }
      }

      ElMessage.success('批次操作完成')
    } catch (err: any) {
      ElMessage.error(err.message || '批次操作失敗')
      throw err
    }
  }

  // 导入标签
  const importLabels = async (data: ImportLabelData) => {
    try {
      const result = await labelsService.importLabels(data)
      await fetchLabels() // 重新获取数据
      ElMessage.success(`成功導入 ${result.successCount} 個標籤`)
      return result
    } catch (err: any) {
      ElMessage.error(err.message || '導入標籤失敗')
      throw err
    }
  }

  // 导出标签
  const exportLabels = async (options: ExportLabelOptions) => {
    try {
      const blob = await labelsService.exportLabels(options)
      
      // 创建下载链接
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `標籤設定_${new Date().toISOString().split('T')[0]}.${options.format}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      ElMessage.success('標籤數據匯出成功')
    } catch (err: any) {
      ElMessage.error(err.message || '匯出標籤失敗')
      throw err
    }
  }

  // 验证标签名称
  const validateLabelName = (name: string, type: 'product' | 'feedback') => {
    const errors: string[] = []
    
    if (!name.trim()) {
      errors.push('標籤名稱不能為空')
    }

    const maxLength = type === 'product' 
      ? settings.value.limits.maxProductLabelLength
      : settings.value.limits.maxFeedbackLabelLength

    if (name.length > maxLength) {
      errors.push(`標籤名稱長度不能超過 ${maxLength} 個字`)
    }

    // 检查重复
    const existingLabels = type === 'product' ? productLabels.value : feedbackLabels.value
    if (existingLabels.some(label => label.name === name)) {
      errors.push('標籤名稱已存在')
    }

    return {
      isValid: errors.length === 0,
      errors
    }
  }

  // 刷新数据
  const refreshData = () => {
    fetchLabels()
    fetchOperations()
  }

  // 获取模拟数据
  const getMockData = () => {
    productLabels.value = [
      {
        id: '1',
        name: '手福饅頭',
        isActive: true,
        createdAt: '2025-07-01 10:00:00',
        updatedAt: '2025-07-01 10:00:00',
        createdBy: 'user1',
        usage: 15
      },
      {
        id: '2',
        name: '包子',
        isActive: true,
        createdAt: '2025-07-01 10:05:00',
        updatedAt: '2025-07-01 10:05:00',
        createdBy: 'user1',
        usage: 12
      },
      {
        id: '3',
        name: '饅頭',
        isActive: true,
        createdAt: '2025-07-01 10:10:00',
        updatedAt: '2025-07-01 10:10:00',
        createdBy: 'user2',
        usage: 8
      },
      {
        id: '4',
        name: '水餃',
        isActive: false,
        createdAt: '2025-07-01 10:15:00',
        updatedAt: '2025-07-01 10:15:00',
        createdBy: 'user2',
        usage: 3
      }
    ]

    feedbackLabels.value = [
      {
        id: '1',
        name: '通路物流',
        category: '通路物流',
        isActive: true,
        isDefault: true,
        createdAt: '2025-07-01 10:00:00',
        updatedAt: '2025-07-01 10:00:00',
        createdBy: 'system',
        usage: 25
      },
      {
        id: '2',
        name: '食品口味',
        category: '產品規格',
        isActive: true,
        isDefault: true,
        createdAt: '2025-07-01 10:00:00',
        updatedAt: '2025-07-01 10:00:00',
        createdBy: 'system',
        usage: 18
      },
      {
        id: '3',
        name: '食品保存',
        category: '調理方式',
        isActive: true,
        isDefault: true,
        createdAt: '2025-07-01 10:00:00',
        updatedAt: '2025-07-01 10:00:00',
        createdBy: 'system',
        usage: 12
      },
      {
        id: '4',
        name: '營業時間',
        category: '營業資訊',
        isActive: true,
        isDefault: false,
        createdAt: '2025-07-01 10:30:00',
        updatedAt: '2025-07-01 10:30:00',
        createdBy: 'user1',
        usage: 7
      }
    ]

    operations.value = [
      {
        id: '1',
        type: 'create',
        targetType: 'product',
        targetId: '4',
        targetName: '水餃',
        operatorId: 'user2',
        operatorName: '權限人員 02',
        timestamp: '2025-07-01 10:15:00',
        description: '新增商品標籤'
      },
      {
        id: '2',
        type: 'create',
        targetType: 'feedback',
        targetId: '4',
        targetName: '營業時間',
        operatorId: 'user1',
        operatorName: '權限人員 01',
        timestamp: '2025-07-01 10:30:00',
        description: '新增反饋標籤'
      }
    ]

    stats.value = {
      totalProductLabels: 4,
      totalFeedbackLabels: 4,
      activeProductLabels: 3,
      activeFeedbackLabels: 4,
      recentOperations: operations.value,
      topUsedLabels: {
        products: [
          { name: '手福饅頭', usage: 15 },
          { name: '包子', usage: 12 },
          { name: '饅頭', usage: 8 }
        ],
        feedbacks: [
          { name: '通路物流', usage: 25 },
          { name: '食品口味', usage: 18 },
          { name: '食品保存', usage: 12 }
        ]
      }
    }

    loading.value = false
  }

  return {
    // 状态
    productLabels: readonly(productLabels),
    feedbackLabels: readonly(feedbackLabels),
    operations: readonly(operations),
    loading: readonly(loading),
    error: readonly(error),
    settings: readonly(settings),
    stats: readonly(stats),
    
    // 计算属性
    activeProductLabels,
    activeFeedbackLabels,
    productLabelCount,
    feedbackLabelCount,
    canAddProductLabel,
    canAddFeedbackLabel,
    feedbackLabelsByCategory,
    
    // 方法
    fetchLabels,
    fetchOperations,
    addProductLabel,
    addFeedbackLabel,
    updateProductLabel,
    updateFeedbackLabel,
    deleteProductLabel,
    deleteFeedbackLabel,
    bulkOperation,
    importLabels,
    exportLabels,
    validateLabelName,
    refreshData,
    getMockData
  }
})