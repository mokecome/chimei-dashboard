<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="emit('update:visible', $event)"
    title="上傳分析檔案"
    width="600px"
    :before-close="handleClose"
    class="upload-modal"
  >
    <div class="upload-content">
      <!-- 文件上传区域 -->
      <div class="upload-area">
        <el-upload
          ref="uploadRef"
          class="upload-dragger"
          drag
          action=""
          :http-request="handleUpload"
          :accept="acceptedTypes"
          :before-upload="beforeUpload"
          :on-success="onUploadSuccess"
          :on-error="onUploadError"
          :on-progress="onUploadProgress"
          :file-list="fileList"
          :auto-upload="false"
          multiple
        >
          <div class="upload-dragger-content">
            <el-icon class="upload-icon" size="48">
              <UploadFilled />
            </el-icon>
            <div class="upload-text">
              <p class="upload-hint">拖拽檔案到此處或<em>點擊選擇</em></p>
              <p class="upload-desc">支援 .wav、.mp3、.txt 格式，單檔最大 50MB</p>
            </div>
          </div>
        </el-upload>
      </div>

      <!-- 文件列表 -->
      <div v-if="fileList.length" class="file-list">
        <div class="file-list-header">
          <h4>待上傳檔案 ({{ fileList.length }})</h4>
          <el-button size="small" @click="clearFiles">清空列表</el-button>
        </div>
        
        <div class="file-items">
          <div 
            v-for="(file, index) in fileList" 
            :key="index"
            class="file-item"
          >
            <div class="file-info">
              <el-icon class="file-icon">
                <component :is="getFileIcon(file.name)" />
              </el-icon>
              <div class="file-details">
                <div class="file-name">{{ file.name }}</div>
                <div class="file-size">{{ formatFileSize(file.size) }}</div>
              </div>
            </div>
            
            <div class="file-status">
              <template v-if="file.status === 'ready'">
                <el-tag size="small" type="info">準備上傳</el-tag>
              </template>
              <template v-else-if="file.status === 'uploading'">
                <el-progress 
                  :percentage="file.percentage || 0" 
                  :show-text="false"
                  size="small"
                  style="width: 100px;"
                />
              </template>
              <template v-else-if="file.status === 'success'">
                <el-tag size="small" type="success">上傳成功</el-tag>
              </template>
              <template v-else-if="file.status === 'fail'">
                <el-tag size="small" type="danger">上傳失敗</el-tag>
              </template>
            </div>
            
            <div class="file-actions">
              <el-button
                v-if="file.status === 'ready' || file.status === 'fail'"
                size="small"
                link
                type="danger"
                @click="removeFile(index)"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 上传选项 -->
      <div class="upload-options">
        <div class="option-item">
          <el-checkbox v-model="uploadOptions.autoAnalyze">
            上傳後自動開始分析
          </el-checkbox>
        </div>
        
        <div class="option-item">
          <el-checkbox v-model="uploadOptions.notifyOnComplete">
            分析完成後發送通知
          </el-checkbox>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button 
          type="primary" 
          :loading="uploading"
          :disabled="!fileList.length || !hasReadyFiles"
          @click="startUpload"
        >
          <el-icon v-if="!uploading"><Upload /></el-icon>
          {{ uploading ? '上傳中...' : '開始上傳' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { 
  UploadFilled, 
  Upload, 
  Delete,
  Document,
  VideoPlay,
  Headphone
} from '@element-plus/icons-vue'
import { ElMessage, type UploadFile, type UploadRawFile, type UploadRequestOptions } from 'element-plus'
import { dataSourceService } from '@/services/datasource.service'

interface Props {
  visible: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:visible': [visible: boolean]
  'uploaded': []
}>()

// 状态
const uploadRef = ref()
const uploading = ref(false)
const fileList = ref<UploadFile[]>([])

// 上传选项
const uploadOptions = ref({
  autoAnalyze: true,
  notifyOnComplete: true
})

// 接受的文件类型
const acceptedTypes = '.wav,.mp3,.txt'
const maxFileSize = 50 * 1024 * 1024 // 50MB

// 计算属性
const hasReadyFiles = computed(() => 
  fileList.value.some(file => file.status === 'ready')
)

// 监听visible变化
watch(() => props.visible, (newVal) => {
  if (!newVal) {
    // 对话框关闭时重置状态
    setTimeout(() => {
      fileList.value = []
      uploading.value = false
      uploadOptions.value = {
        autoAnalyze: true,
        notifyOnComplete: true
      }
    }, 300)
  }
})

// 获取文件图标
const getFileIcon = (fileName: string) => {
  const ext = fileName.split('.').pop()?.toLowerCase()
  const icons = {
    wav: Headphone,
    mp3: VideoPlay,
    txt: Document
  }
  return icons[ext as keyof typeof icons] || Document
}

// 格式化文件大小
const formatFileSize = (size: number) => {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

// 上传前检查
const beforeUpload = (rawFile: UploadRawFile) => {
  // 检查文件类型
  const ext = rawFile.name.split('.').pop()?.toLowerCase()
  const allowedTypes = ['wav', 'mp3', 'txt']
  
  if (!ext || !allowedTypes.includes(ext)) {
    ElMessage.error('只支援 .wav、.mp3、.txt 格式的檔案')
    return false
  }

  // 检查文件大小
  if (rawFile.size > maxFileSize) {
    ElMessage.error('檔案大小不能超過 50MB')
    return false
  }

  // 检查重复文件
  const isDuplicate = fileList.value.some(file => 
    file.name === rawFile.name && file.size === rawFile.size
  )
  
  if (isDuplicate) {
    ElMessage.warning('檔案已存在於上傳列表中')
    return false
  }

  return true
}

// 自定义上传处理
const handleUpload = async (options: UploadRequestOptions) => {
  // 这里不实际上传，只是添加到列表中
  return Promise.resolve()
}

// 开始上传
const startUpload = async () => {
  const readyFiles = fileList.value.filter(file => file.status === 'ready')
  if (!readyFiles.length) return

  uploading.value = true

  try {
    // 如果只有一个文件，使用单文件上传
    if (readyFiles.length === 1) {
      const file = readyFiles[0]
      try {
        file.status = 'uploading'
        file.percentage = 0

        const formData = new FormData()
        formData.append('file', file.raw!)
        formData.append('autoAnalyze', uploadOptions.value.autoAnalyze.toString())
        formData.append('notifyOnComplete', uploadOptions.value.notifyOnComplete.toString())

        await dataSourceService.uploadFile(formData, (progress) => {
          file.percentage = progress
        })

        file.percentage = 100
        file.status = 'success'
        
      } catch (error) {
        file.status = 'fail'
        console.error('Single upload failed:', error)
        ElMessage.error(`${file.name} 上傳失敗: ${error.message || error}`)
      }
    } 
    // 如果有多个文件，使用批量上传
    else {
      try {
        // 设置所有文件为上传中状态
        readyFiles.forEach(file => {
          file.status = 'uploading'
          file.percentage = 0
        })

        // 准备批量上传的文件
        const rawFiles = readyFiles.map(file => file.raw!).filter(Boolean)
        
        // 调用批量上传API
        const result = await dataSourceService.uploadFiles(
          rawFiles,
          {
            autoAnalyze: uploadOptions.value.autoAnalyze,
            notifyOnComplete: uploadOptions.value.notifyOnComplete
          },
          (progress) => {
            // 为所有文件更新进度
            readyFiles.forEach(file => {
              file.percentage = progress
            })
          }
        )

        // 根据批量上传结果更新文件状态
        result.successful_uploads.forEach((success, index) => {
          if (index < readyFiles.length) {
            readyFiles[index].status = 'success'
            readyFiles[index].percentage = 100
          }
        })

        result.failed_uploads.forEach((failure, index) => {
          const failIndex = result.successful_uploads.length + index
          if (failIndex < readyFiles.length) {
            readyFiles[failIndex].status = 'fail'
            readyFiles[failIndex].percentage = 0
          }
        })

        if (result.failed_uploads.length > 0) {
          ElMessage.warning(`${result.failed_count} 個檔案上傳失敗`)
        }

      } catch (error) {
        // 批量上传失败，标记所有文件为失败
        readyFiles.forEach(file => {
          file.status = 'fail'
          file.percentage = 0
        })
        console.error('Batch upload failed:', error)
        ElMessage.error(`批量上傳失敗: ${error.message || error}`)
      }
    }

    // 检查是否所有文件都上传成功
    const successCount = fileList.value.filter(file => file.status === 'success').length
    const failCount = fileList.value.filter(file => file.status === 'fail').length

    if (successCount > 0) {
      ElMessage.success(`成功上傳 ${successCount} 個檔案`)
      emit('uploaded')
    }

    if (failCount > 0) {
      ElMessage.warning(`${failCount} 個檔案上傳失敗`)
    }

    // 上傳開始後立即關閉對話框
    setTimeout(() => {
      handleClose()
    }, 500) // 延遲 0.5 秒讓用戶看到上傳開始

  } finally {
    uploading.value = false
  }
}

// 上传成功回调
const onUploadSuccess = (response: any, file: UploadFile) => {
  file.status = 'success'
}

// 上传失败回调
const onUploadError = (error: any, file: UploadFile) => {
  file.status = 'fail'
  ElMessage.error(`${file.name} 上傳失敗`)
}

// 上传进度回调
const onUploadProgress = (event: any, file: UploadFile) => {
  file.percentage = Math.round((event.loaded / event.total) * 100)
}

// 移除文件
const removeFile = (index: number) => {
  fileList.value.splice(index, 1)
}

// 清空文件列表
const clearFiles = () => {
  fileList.value = []
  uploadRef.value?.clearFiles()
}

// 关闭对话框
const handleClose = () => {
  if (uploading.value) {
    ElMessage.warning('正在上傳中，請稍後再關閉')
    return
  }
  emit('update:visible', false)
}
</script>

<style scoped>
.upload-modal :deep(.el-dialog__header) {
  padding: 20px 24px 0;
}

.upload-modal :deep(.el-dialog__body) {
  padding: 20px 24px;
}

.upload-modal :deep(.el-dialog__footer) {
  padding: 0 24px 20px;
}

.upload-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.upload-area {
  width: 100%;
}

.upload-dragger {
  width: 100%;
}

.upload-dragger :deep(.el-upload-dragger) {
  width: 100%;
  height: 180px;
  border: 2px dashed #d1d5db;
  border-radius: 12px;
  background: #fafafa;
  transition: all 0.3s ease;
}

.upload-dragger :deep(.el-upload-dragger:hover) {
  border-color: #3b82f6;
  background: #f0f9ff;
}

.upload-dragger-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 20px;
}

.upload-icon {
  color: #9ca3af;
  margin-bottom: 16px;
}

.upload-text {
  text-align: center;
}

.upload-hint {
  font-size: 16px;
  color: #374151;
  margin: 0 0 8px 0;
}

.upload-hint em {
  color: #3b82f6;
  font-style: normal;
  text-decoration: underline;
}

.upload-desc {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.file-list {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.file-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.file-list-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.file-items {
  max-height: 200px;
  overflow-y: auto;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.file-item:last-child {
  border-bottom: none;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.file-icon {
  color: #6b7280;
  font-size: 18px;
}

.file-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.file-size {
  font-size: 12px;
  color: #6b7280;
}

.file-status {
  display: flex;
  align-items: center;
  min-width: 120px;
  justify-content: center;
}

.file-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 40px;
  justify-content: center;
}

.upload-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
}

.option-item {
  display: flex;
  align-items: center;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .upload-modal :deep(.el-dialog) {
    width: 95% !important;
    margin: 0 auto;
  }
  
  .file-item {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .file-info {
    justify-content: flex-start;
  }
  
  .file-status {
    justify-content: flex-start;
    min-width: auto;
  }
  
  .file-actions {
    justify-content: flex-end;
    min-width: auto;
  }
  
  .dialog-footer {
    flex-direction: column;
  }
  
  .dialog-footer .el-button {
    width: 100%;
    margin: 0;
  }
}
</style>