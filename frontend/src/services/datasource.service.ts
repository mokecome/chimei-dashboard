import type { 
  DataSourceItem, 
  DataSourceFilter, 
  DataSourceListResponse,
  SortConfig,
  FileAnalysisResult 
} from '@/types/datasource'
import api from './api'

class DataSourceService {
  private baseURL = '/files'

  // 获取数据源列表
  async getDataSourceList(
    page: number = 1,
    size: number = 20,
    filters: DataSourceFilter = {},
    sort: SortConfig = { field: 'uploadTime', order: 'desc' }
  ): Promise<DataSourceListResponse> {
    try {
      const params: any = {
        page,
        page_size: size
      }

      // 添加筛选条件
      if (filters.fileName) params.fileName = filters.fileName
      if (filters.fileType) params.fileType = filters.fileType
      if (filters.status) params.status = filters.status
      if (filters.uploader) params.uploader = filters.uploader
      if (filters.keyword) params.keyword = filters.keyword
      if (filters.dateRange && filters.dateRange.length === 2) {
        params.startDate = filters.dateRange[0]
        params.endDate = filters.dateRange[1]
      }

      const response = await api.get(`${this.baseURL}/`, { params })
      
      // 轉換後端響應格式為前端期望格式
      const backendData = response.data
      
      // Debug for ni_hao_ma_offline
      if (backendData.items) {
        const niHaoFile = backendData.items.find((item: any) => 
          item.original_filename?.includes('ni_hao_ma_offline')
        )
        if (niHaoFile) {
          console.log('=== SERVICE LAYER DEBUG ===')
          console.log('Raw backend data:', niHaoFile)
          console.log('analysis_result:', niHaoFile.analysis_result)
          if (niHaoFile.analysis_result) {
            console.log('sentiment from backend:', niHaoFile.analysis_result.sentiment)
          }
        }
      }
      
      return {
        items: backendData.items.map((item: any) => {
          const mappedItem = {
            id: item.id,
            fileName: item.filename,
            original_filename: item.original_filename,
            fileType: item.file_format,
            file_format: item.file_format,
            fileSize: item.file_size,
            uploadTime: item.created_at,
            created_at: item.created_at,
            updated_at: item.updated_at,
            uploader: item.uploaded_by,
            uploader_name: item.uploader_name,
            uploaderName: item.uploader_name,
            status: item.status,
            analysis_result: item.analysis_result || null,
            analysisResult: item.analysis_result || null  // Keep backwards compatibility
          }
          
          return mappedItem
        }),
        pagination: {
          page: backendData.page,
          size: backendData.page_size,
          total: backendData.total,
          pages: backendData.total_pages
        }
      }
    } catch (error) {
      console.error('Failed to fetch datasource list:', error)
      throw error
    }
  }

  // 获取数据源详情
  async getDataSourceDetail(id: string): Promise<DataSourceItem> {
    try {
      const response = await api.get(`${this.baseURL}/${id}`)
      return response.data
    } catch (error) {
      console.error('Failed to fetch datasource detail:', error)
      throw error
    }
  }

  // 上传文件
  async uploadFile(
    formData: FormData, 
    onProgress?: (progress: number) => void
  ): Promise<{ id: string, message: string }> {
    try {
      const response = await api.post(`${this.baseURL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        timeout: 300000, // 5 分鐘超時
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded / progressEvent.total) * 100)
            onProgress(progress)
          }
        }
      })
      return response.data
    } catch (error) {
      console.error('Failed to upload file:', error)
      throw error
    }
  }

  // 批量上传文件
  async uploadFiles(
    files: File[], 
    options: { autoAnalyze: boolean, notifyOnComplete: boolean },
    onProgress?: (progress: number) => void
  ): Promise<{ 
    successful_uploads: any[], 
    failed_uploads: any[], 
    total_files: number,
    successful_count: number, 
    failed_count: number 
  }> {
    try {
      const formData = new FormData()
      
      files.forEach((file, index) => {
        formData.append(`files`, file)
      })
      
      formData.append('autoAnalyze', options.autoAnalyze.toString())
      formData.append('notifyOnComplete', options.notifyOnComplete.toString())

      const response = await api.post(`${this.baseURL}/batch-upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        timeout: 600000, // 10 分鐘超時（批量上傳）
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded / progressEvent.total) * 100)
            onProgress(progress)
          }
        }
      })
      return response.data
    } catch (error) {
      console.error('Failed to upload files:', error)
      throw error
    }
  }

  // 删除数据源
  async deleteDataSource(id: string): Promise<void> {
    try {
      await api.delete(`${this.baseURL}/${id}`)
    } catch (error) {
      console.error('Failed to delete datasource:', error)
      throw error
    }
  }

  // 批量删除数据源
  async batchDelete(ids: string[]): Promise<void> {
    try {
      await api.delete(`${this.baseURL}/batch`, { data: { ids } })
    } catch (error) {
      console.error('Failed to batch delete datasources:', error)
      throw error
    }
  }

  // 重试分析
  async retryAnalysis(id: string): Promise<void> {
    try {
      console.log('=== SERVICE RETRY ANALYSIS ===')
      console.log('File ID:', id)
      console.log('API URL:', `${this.baseURL}/${id}/reprocess`)
      
      const response = await api.post(`${this.baseURL}/${id}/reprocess`)
      console.log('API response:', response.data)
      
    } catch (error: any) {
      console.error('Failed to retry analysis:', error)
      console.error('Error status:', error.response?.status)
      console.error('Error data:', error.response?.data)
      console.error('Error config:', error.config)
      throw error
    }
  }

  // 批量分析
  async batchAnalyze(ids: string[]): Promise<void> {
    try {
      await api.post(`${this.baseURL}/batch/process`, { ids })
    } catch (error) {
      console.error('Failed to batch analyze:', error)
      throw error
    }
  }

  // 更新数据源
  async updateDataSource(id: string, data: Partial<DataSourceItem>): Promise<DataSourceItem> {
    try {
      const response = await api.put(`${this.baseURL}/${id}`, data)
      return response.data
    } catch (error) {
      console.error('Failed to update datasource:', error)
      throw error
    }
  }

  // 获取分析结果
  async getAnalysisResult(id: string): Promise<any> {
    try {
      const response = await api.get(`/analysis/result/${id}`)
      return response.data
    } catch (error) {
      console.error('Failed to fetch analysis result:', error)
      throw error
    }
  }

  // 下载文件
  async downloadFile(id: string): Promise<Blob> {
    try {
      const response = await api.get(`${this.baseURL}/${id}/download`, {
        responseType: 'blob'
      })
      return response.data
    } catch (error) {
      console.error('Failed to download file:', error)
      throw error
    }
  }

  // 导出数据源列表
  async exportList(
    filters: DataSourceFilter = {},
    format: 'xlsx' | 'csv' = 'xlsx'
  ): Promise<Blob> {
    try {
      const params: any = { format }
      
      // 添加筛选条件
      if (filters.fileName) params.fileName = filters.fileName
      if (filters.fileType) params.fileType = filters.fileType
      if (filters.status) params.status = filters.status
      if (filters.uploader) params.uploader = filters.uploader
      if (filters.keyword) params.keyword = filters.keyword
      if (filters.dateRange && filters.dateRange.length === 2) {
        params.startDate = filters.dateRange[0]
        params.endDate = filters.dateRange[1]
      }

      const response = await api.get(`${this.baseURL}/export`, {
        params,
        responseType: 'blob'
      })
      return response.data
    } catch (error) {
      console.error('Failed to export datasource list:', error)
      throw error
    }
  }

  // 获取上传统计
  async getUploadStats(): Promise<{
    totalFiles: number
    totalSize: number
    statusDistribution: Record<string, number>
    typeDistribution: Record<string, number>
  }> {
    try {
      const response = await api.get(`${this.baseURL}/stats`)
      return response.data
    } catch (error) {
      console.error('Failed to fetch upload stats:', error)
      throw error
    }
  }
}

export const dataSourceService = new DataSourceService()