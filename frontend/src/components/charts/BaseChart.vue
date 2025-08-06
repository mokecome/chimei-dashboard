<template>
  <div class="chart-container">
    <!-- 图表标题和操作区域 -->
    <div class="chart-header">
      <div class="chart-title">
        <h3>{{ title }}</h3>
        <span v-if="subtitle" class="chart-subtitle">{{ subtitle }}</span>
      </div>
      <div class="chart-actions">
        <slot name="actions">
          <el-button 
            v-if="showFullscreen"
            size="small" 
            circle 
            @click="toggleFullscreen"
          >
            <el-icon><FullScreen /></el-icon>
          </el-button>
          <el-button 
            v-if="showRefresh"
            size="small" 
            circle 
            @click="refresh"
          >
            <el-icon><Refresh /></el-icon>
          </el-button>
        </slot>
      </div>
    </div>

    <!-- 图表内容 -->
    <div 
      ref="chartContainer" 
      class="chart-wrapper"
      :style="{ height: `${height}px` }"
    >
      <div v-if="loading" class="chart-loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>載入中...</span>
      </div>
      
      <div v-else-if="error" class="chart-error">
        <el-icon><Warning /></el-icon>
        <span>{{ error }}</span>
        <el-button size="small" @click="refresh">重試</el-button>
      </div>
      
      <div v-else-if="!hasData" class="chart-empty">
        <el-icon><DataLine /></el-icon>
        <span>暫無數據</span>
      </div>
      
      <div v-else ref="chartElement" class="chart-element" />
    </div>

    <!-- 图表说明 -->
    <div v-if="description" class="chart-description">
      {{ description }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { FullScreen, Refresh, Loading, Warning, DataLine } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

interface Props {
  title: string
  subtitle?: string
  description?: string
  height?: number
  loading?: boolean
  error?: string
  hasData?: boolean
  options?: echarts.EChartsOption
  showFullscreen?: boolean
  showRefresh?: boolean
  clickable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  height: 300,
  loading: false,
  error: '',
  hasData: true,
  showFullscreen: true,
  showRefresh: true,
  clickable: false
})

const emit = defineEmits<{
  refresh: []
  chartClick: [params: any]
  chartReady: [chart: echarts.ECharts]
}>()

const chartContainer = ref<HTMLElement>()
const chartElement = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null
let resizeObserver: ResizeObserver | null = null

// 初始化图表
const initChart = async () => {
  if (!chartElement.value || !props.options || props.loading || props.error || !props.hasData) {
    return
  }

  await nextTick()

  try {
    // 销毁现有实例
    if (chartInstance) {
      chartInstance.dispose()
      chartInstance = null
    }

    // 创建新实例
    chartInstance = echarts.init(chartElement.value)
    
    // 设置配置项
    chartInstance.setOption(props.options)
    
    // 添加点击事件
    if (props.clickable) {
      chartInstance.on('click', (params) => {
        emit('chartClick', params)
      })
    }

    // 通知图表已准备就绪
    emit('chartReady', chartInstance)

    // 设置响应式
    setupResize()
  } catch (error) {
    console.error('Chart initialization failed:', error)
  }
}

// 设置响应式调整
const setupResize = () => {
  if (!chartInstance || !chartContainer.value) return

  // 立即调整大小
  chartInstance.resize()

  // 使用 ResizeObserver 监听容器大小变化
  if (resizeObserver) {
    resizeObserver.disconnect()
  }

  resizeObserver = new ResizeObserver(() => {
    if (chartInstance) {
      chartInstance.resize()
    }
  })

  resizeObserver.observe(chartContainer.value)
}

// 刷新图表
const refresh = () => {
  emit('refresh')
}

// 切换全屏
const toggleFullscreen = () => {
  if (!chartContainer.value) return

  if (document.fullscreenElement) {
    document.exitFullscreen()
  } else {
    chartContainer.value.requestFullscreen()
  }
}

// 监听配置变化
watch(
  () => props.options,
  () => {
    if (chartInstance && props.options) {
      chartInstance.setOption(props.options, true)
    }
  },
  { deep: true }
)

// 监听数据状态变化
watch(
  [() => props.loading, () => props.error, () => props.hasData],
  () => {
    nextTick(() => {
      initChart()
    })
  }
)

// 生命周期
onMounted(() => {
  initChart()
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
})

// 暴露方法
defineExpose({
  getChart: () => chartInstance,
  resize: () => chartInstance?.resize(),
  refresh
})
</script>

<style scoped>
.chart-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: box-shadow 0.3s ease;
}

.chart-container:hover {
  box-shadow: 0 4px 12px 0 rgba(0, 0, 0, 0.15);
}

.chart-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid #f3f4f6;
}

.chart-title h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.4;
}

.chart-subtitle {
  display: block;
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}

.chart-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.chart-wrapper {
  position: relative;
  padding: 16px 24px;
}

.chart-element {
  width: 100%;
  height: 100%;
}

.chart-loading,
.chart-error,
.chart-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #6b7280;
  gap: 12px;
}

.chart-loading .el-icon {
  font-size: 24px;
  color: var(--primary-color);
}

.chart-error .el-icon {
  font-size: 24px;
  color: var(--danger-color);
}

.chart-empty .el-icon {
  font-size: 24px;
  color: #9ca3af;
}

.chart-description {
  padding: 12px 24px 20px;
  font-size: 12px;
  color: #6b7280;
  border-top: 1px solid #f3f4f6;
  background: #fafafa;
}

/* 全屏模式下的样式调整 */
.chart-container:fullscreen {
  padding: 20px;
  background: white;
}

.chart-container:fullscreen .chart-wrapper {
  height: calc(100vh - 200px) !important;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chart-header {
    padding: 16px 16px 12px;
  }
  
  .chart-wrapper {
    padding: 12px 16px;
  }
  
  .chart-title h3 {
    font-size: 14px;
  }
  
  .chart-actions {
    gap: 4px;
  }
}
</style>