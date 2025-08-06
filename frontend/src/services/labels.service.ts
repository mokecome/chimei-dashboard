import type { 
  ProductLabel, 
  FeedbackLabel,
  LabelOperation,
  LabelStats,
  BulkLabelOperation,
  ImportLabelData,
  ExportLabelOptions
} from '@/types/labels'
import api from './api'

class LabelsService {
  private baseURL = '/labels'

  // 获取商品标签列表
  async getProductLabels(): Promise<ProductLabel[]> {
    try {
      const response = await api.get(`${this.baseURL}/products`)
      return response.data
    } catch (error) {
      console.error('Failed to fetch product labels:', error)
      throw error
    }
  }

  // 获取反馈标签列表
  async getFeedbackLabels(): Promise<FeedbackLabel[]> {
    try {
      const response = await api.get(`${this.baseURL}/categories`)
      return response.data
    } catch (error) {
      console.error('Failed to fetch feedback labels:', error)
      throw error
    }
  }

  // 获取标签统计信息
  async getLabelStats(): Promise<LabelStats> {
    try {
      const response = await api.get(`${this.baseURL}/stats`)
      return response.data
    } catch (error) {
      console.error('Failed to fetch label stats:', error)
      throw error
    }
  }

  // 获取操作历史
  async getLabelOperations(limit: number = 50): Promise<LabelOperation[]> {
    try {
      const response = await api.get(`${this.baseURL}/operations`, {
        params: { limit }
      })
      return response.data
    } catch (error) {
      console.error('Failed to fetch label operations:', error)
      throw error
    }
  }

  // 创建商品标签
  async createProductLabel(data: { name: string, description?: string }): Promise<ProductLabel> {
    try {
      const response = await api.post(`${this.baseURL}/products`, data)
      return response.data
    } catch (error) {
      console.error('Failed to create product label:', error)
      throw error
    }
  }

  // 创建反馈标签
  async createFeedbackLabel(data: { 
    name: string, 
    category: string, 
    description?: string 
  }): Promise<FeedbackLabel> {
    try {
      const response = await api.post(`${this.baseURL}/categories`, data)
      return response.data
    } catch (error) {
      console.error('Failed to create feedback label:', error)
      throw error
    }
  }

  // 更新商品标签
  async updateProductLabel(id: string, data: Partial<ProductLabel>): Promise<ProductLabel> {
    try {
      const response = await api.put(`${this.baseURL}/products/${id}`, data)
      return response.data
    } catch (error) {
      console.error('Failed to update product label:', error)
      throw error
    }
  }

  // 更新反馈标签
  async updateFeedbackLabel(id: string, data: Partial<FeedbackLabel>): Promise<FeedbackLabel> {
    try {
      const response = await api.put(`${this.baseURL}/categories/${id}`, data)
      return response.data
    } catch (error) {
      console.error('Failed to update feedback label:', error)
      throw error
    }
  }

  // 删除商品标签
  async deleteProductLabel(id: string): Promise<void> {
    try {
      await api.delete(`${this.baseURL}/products/${id}`)
    } catch (error) {
      console.error('Failed to delete product label:', error)
      throw error
    }
  }

  // 删除反馈标签
  async deleteFeedbackLabel(id: string): Promise<void> {
    try {
      await api.delete(`${this.baseURL}/categories/${id}`)
    } catch (error) {
      console.error('Failed to delete feedback label:', error)
      throw error
    }
  }

  // 批量删除商品标签
  async deleteProductLabelsBatch(ids: number[]): Promise<{
    deleted_count: number
    failed_count: number
    failed_deletions: Array<{ id: number, reason: string }>
  }> {
    try {
      const response = await api.request({
        method: 'DELETE',
        url: `${this.baseURL}/products/batch`,
        data: ids,
        headers: {
          'Content-Type': 'application/json'
        }
      })
      return response.data
    } catch (error) {
      console.error('Failed to delete product labels batch:', error)
      throw error
    }
  }

  // 批量删除反馈标签
  async deleteFeedbackLabelsBatch(ids: number[]): Promise<{
    deleted_count: number
    failed_count: number
    failed_deletions: Array<{ id: number, reason: string }>
  }> {
    try {
      const response = await api.request({
        method: 'DELETE',
        url: `${this.baseURL}/categories/batch`,
        data: ids,
        headers: {
          'Content-Type': 'application/json'
        }
      })
      return response.data
    } catch (error) {
      console.error('Failed to delete feedback labels batch:', error)
      throw error
    }
  }

  // 切换标签状态
  async toggleLabelStatus(type: 'product' | 'feedback', id: string, isActive: boolean): Promise<ProductLabel | FeedbackLabel> {
    try {
      const endpoint = type === 'product' ? 'products' : 'categories'
      const response = await api.patch(`${this.baseURL}/${endpoint}/${id}/status`, { isActive })
      return response.data
    } catch (error) {
      console.error('Failed to toggle label status:', error)
      throw error
    }
  }

  // 批量操作
  async bulkOperation(operation: BulkLabelOperation): Promise<{
    successCount: number
    failCount: number
    errors: string[]
  }> {
    try {
      const response = await api.post(`${this.baseURL}/bulk`, operation)
      return response.data
    } catch (error) {
      console.error('Failed to perform bulk operation:', error)
      throw error
    }
  }

  // 导入标签
  async importLabels(data: ImportLabelData): Promise<{
    successCount: number
    failCount: number
    duplicateCount: number
    errors: string[]
  }> {
    try {
      const response = await api.post(`${this.baseURL}/import`, data)
      return response.data
    } catch (error) {
      console.error('Failed to import labels:', error)
      throw error
    }
  }

  // 导出标签
  async exportLabels(options: ExportLabelOptions): Promise<Blob> {
    try {
      const response = await api.post(`${this.baseURL}/export`, options, {
        responseType: 'blob'
      })
      return response.data
    } catch (error) {
      console.error('Failed to export labels:', error)
      throw error
    }
  }

  // 验证标签名称
  async validateLabelName(name: string, type: 'product' | 'feedback', excludeId?: string): Promise<{
    isValid: boolean
    isDuplicate: boolean
    errors: string[]
  }> {
    try {
      const response = await api.post(`${this.baseURL}/validate`, {
        name,
        type,
        excludeId
      })
      return response.data
    } catch (error) {
      console.error('Failed to validate label name:', error)
      throw error
    }
  }

  // 搜索标签
  async searchLabels(query: string, type?: 'product' | 'feedback'): Promise<{
    products: ProductLabel[]
    feedbacks: FeedbackLabel[]
  }> {
    try {
      const params: any = { query }
      if (type) params.type = type

      const response = await api.get(`${this.baseURL}/search`, { params })
      return response.data
    } catch (error) {
      console.error('Failed to search labels:', error)
      throw error
    }
  }

  // 获取标签使用统计
  async getLabelUsage(type: 'product' | 'feedback', id: string, timeRange?: {
    startDate: string
    endDate: string
  }): Promise<{
    totalUsage: number
    recentUsage: Array<{
      date: string
      count: number
    }>
    topFiles: Array<{
      id: string
      fileName: string
      usage: number
    }>
  }> {
    try {
      const endpoint = type === 'product' ? 'products' : 'categories'
      const response = await api.get(`${this.baseURL}/${endpoint}/${id}/usage`, {
        params: timeRange
      })
      return response.data
    } catch (error) {
      console.error('Failed to fetch label usage:', error)
      throw error
    }
  }

  // 获取推荐标签
  async getRecommendedLabels(content: string, type: 'product' | 'feedback'): Promise<Array<{
    name: string
    confidence: number
    reason: string
  }>> {
    try {
      const response = await api.post(`${this.baseURL}/recommend`, {
        content,
        type
      })
      return response.data
    } catch (error) {
      console.error('Failed to get recommended labels:', error)
      throw error
    }
  }

  // 获取默认反馈分类
  async getDefaultFeedbackCategories(): Promise<string[]> {
    try {
      const response = await api.get(`${this.baseURL}/categories/default`)
      return response.data
    } catch (error) {
      console.error('Failed to fetch default feedback categories:', error)
      throw error
    }
  }

  // 重新训练标签模型
  async retrainLabelModel(): Promise<{
    jobId: string
    estimatedTime: number
    message: string
  }> {
    try {
      const response = await api.post(`${this.baseURL}/retrain`)
      return response.data
    } catch (error) {
      console.error('Failed to retrain label model:', error)
      throw error
    }
  }
}

export const labelsService = new LabelsService()