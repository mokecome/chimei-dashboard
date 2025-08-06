import api from './api'
import type { 
  AnalysisItem, 
  AnalysisFilter, 
  AnalysisListResponse,
  AnalysisStats,
  DimensionAnalysis,
  ExportConfig,
  SortConfig
} from '@/types/analysis'

export const analysisService = {
  // 获取分析列表
  async getAnalysisList(
    page = 1, 
    size = 20, 
    filters?: AnalysisFilter,
    sort?: SortConfig
  ): Promise<AnalysisListResponse> {
    const response = await api.get<AnalysisListResponse>('/data/analysis', {
      params: {
        page,
        size,
        ...filters,
        sort_field: sort?.field,
        sort_order: sort?.order
      }
    })
    return response.data
  },

  // 获取分析详情
  async getAnalysisDetail(id: string): Promise<AnalysisItem> {
    const response = await api.get<AnalysisItem>(`/analysis/result/${id}`)
    return response.data
  },

  // 获取分析统计数据
  async getAnalysisStats(filters?: AnalysisFilter): Promise<AnalysisStats> {
    const response = await api.get<AnalysisStats>('/analysis/statistics', {
      params: filters
    })
    return response.data
  },

  // 获取维度分析数据
  async getDimensionAnalysis(
    dimension: string, 
    filters?: AnalysisFilter
  ): Promise<DimensionAnalysis> {
    const response = await api.get<DimensionAnalysis>(`/analysis/dimension/${dimension}`, {
      params: filters
    })
    return response.data
  },

  // 获取图表数据
  async getChartData(
    dimensions: string[], 
    chartType: string,
    filters?: AnalysisFilter
  ): Promise<any> {
    const response = await api.post('/analysis/chart', {
      dimensions,
      chart_type: chartType,
      filters
    })
    return response.data
  },

  // 导出分析报表
  async exportReport(config: ExportConfig): Promise<Blob> {
    const response = await api.post('/data/export', config, {
      responseType: 'blob'
    })
    return response.data
  },

  // 获取产品标签列表
  async getProductLabels(): Promise<string[]> {
    const response = await api.get<string[]>('/labels/products')
    return response.data
  },

  // 获取反馈标签列表
  async getFeedbackLabels(): Promise<string[]> {
    const response = await api.get<string[]>('/labels/categories')
    return response.data
  },

  // 获取上传者列表
  async getUploaders(): Promise<Array<{ id: string, name: string }>> {
    const response = await api.get('/users')
    return response.data
  },

  // 批量删除分析数据
  async deleteAnalyses(ids: string[]): Promise<void> {
    await api.delete('/analysis/batch', {
      data: { ids }
    })
  },

  // 重新分析文件
  async reAnalyze(id: string): Promise<void> {
    await api.post(`/analysis/start/${id}`)
  }
}