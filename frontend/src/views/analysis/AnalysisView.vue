<template>
  <div class="analysis-page">
    <!-- Page Header -->
    <header class="page-header">
      <div class="header-content">
        <div>
          <nav class="breadcrumb">
            <router-link to="/dashboard" class="breadcrumb-link">Dashboard</router-link>
            <span class="breadcrumb-separator">></span>
            <span class="breadcrumb-current">數據分析</span>
          </nav>
          <h1 class="page-title">數據分析</h1>
        </div>
        <div class="header-actions">
          <el-button type="primary" @click="saveReport">
            匯出報表
          </el-button>
        </div>
      </div>
    </header>

    <!-- Content -->
    <div class="analysis-content">
      <!-- Dimension Selection -->
      <div class="dimensions-section">
        <!-- 維度一 -->
        <div class="dimension-card">
          <div class="dimension-header">
            <h3 class="dimension-title">維度一</h3>
          </div>
          <div class="dimension-items">
            <span 
              v-for="item in dimension1.selected" 
              :key="item"
              class="dimension-item selected"
              @click="removeDimension1Item(item)"
            >
              {{ item }}
            </span>
            <span v-if="dimension1.selected.length > 1" class="dimension-connector">與</span>
            <el-dropdown @command="addDimension1Item" trigger="click">
              <button class="add-button">
                <el-icon><Plus /></el-icon>新增比較項目+
              </button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item 
                    v-for="item in availableDimension1Items" 
                    :key="item"
                    :command="item"
                  >
                    {{ item }}
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>

        <!-- 維度二 -->
        <div class="dimension-card">
          <div class="dimension-header">
            <h3 class="dimension-title">維度二</h3>
          </div>
          <div class="dimension-items">
            <span 
              v-for="item in dimension2.selected" 
              :key="item"
              class="dimension-item selected"
              @click="removeDimension2Item(item)"
            >
              {{ item }}
            </span>
            <span v-if="dimension2.selected.length > 1" class="dimension-connector">與</span>
            <el-dropdown @command="addDimension2Item" trigger="click">
              <button class="add-button">
                <el-icon><Plus /></el-icon>新增指標+
              </button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item 
                    v-for="item in availableDimension2Items" 
                    :key="item"
                    :command="item"
                  >
                    {{ item }}
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>

      <!-- Chart Section -->
      <div class="chart-section">
        <div class="chart-header">
          <div class="chart-filter">
            <el-icon><Filter /></el-icon>
            <span class="filter-count">({{ total }})</span>
          </div>
          <div class="chart-time-controls">
            <el-select v-model="timePeriod" class="time-select">
              <el-option label="週" value="week" />
              <el-option label="月" value="month" />
              <el-option label="年" value="year" />
            </el-select>
          </div>
        </div>
        
        <!-- Chart Container -->
        <div class="chart-container">
          <canvas ref="analysisChart" id="analysisChart"></canvas>
          <div v-if="!chartInstance" class="chart-placeholder">
            <div class="placeholder-content">
              <el-icon size="48" color="#d1d5db"><TrendCharts /></el-icon>
              <p>正在載入圖表...</p>
            </div>
          </div>
        </div>
        
        <!-- Legend -->
        <div class="chart-legend">
          <div 
            v-for="(dataset, index) in chartLegendItems" 
            :key="dataset.label"
            class="legend-item"
          >
            <div 
              class="legend-color" 
              :style="{ backgroundColor: dataset.color }"
            ></div>
            <span>{{ dataset.label }}</span>
          </div>
        </div>
      </div>

      <!-- Data Table -->
      <div class="data-table-section">
        <div class="table-container">
          <el-table 
            :data="tableData" 
            style="width: 100%"
            :header-cell-style="{ backgroundColor: '#f9fafb', fontWeight: '600' }"
            v-loading="loading"
          >
            <el-table-column prop="filename" label="檔案名稱" width="160" />
            <el-table-column label="建立時間" width="180">
              <template #default="scope">
                {{ formatDate(scope.row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="反饋分類" width="200">
              <template #default="scope">
                <el-tag 
                  v-for="category in parseFeedbackCategories(scope.row.feedback_category)" 
                  :key="category"
                  :class="`status-${category.replace(/[^\w\u4e00-\u9fa5]/g, '').replace(/\//g, '')}`"
                  class="category-tag"
                  size="small"
                >
                  {{ category }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="評價傾向" width="100">
              <template #default="scope">
                <span :class="`sentiment-${scope.row.sentiment?.toLowerCase()}`">
                  {{ scope.row.sentiment === 'POSITIVE' ? '正面' : scope.row.sentiment === 'NEGATIVE' ? '負面' : '中性' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="商品分類" width="180">
              <template #default="scope">
                <el-tag 
                  v-if="!scope.row.product_names || scope.row.product_names.length === 0"
                  class="product-tag product-unclassified"
                  size="small"
                >
                  未分類
                </el-tag>
                <el-tag 
                  v-else
                  v-for="product in scope.row.product_names" 
                  :key="product"
                  :class="`product-${product}`"
                  class="product-tag"
                  size="small"
                >
                  {{ product }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="feedback_summary" label="反饋原因" min-width="200" show-overflow-tooltip />
            <el-table-column prop="uploader_name" label="上傳者" width="120" />
            <el-table-column label="詳細內容" width="100" fixed="right">
              <template #default="scope">
                <el-button 
                  type="primary" 
                  link 
                  @click="viewDetails(scope.row)"
                >
                  檢視
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- Pagination -->
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="total"
            layout="total, sizes, prev, pager, next, jumper"
            style="margin-top: 20px; justify-content: center;"
            @size-change="fetchData"
            @current-change="fetchData"
          />
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, computed, watch } from 'vue'
import { ElMessage, ElLoading } from 'element-plus'
import { Filter, Plus, TrendCharts } from '@element-plus/icons-vue'
import Chart from 'chart.js/auto'
import { analysisService, type AnalysisResponse, type TimeSeriesData } from '@/services/analysis'
import { labelsService } from '@/services/labels.service'
import { useRouter } from 'vue-router'

// Router
const router = useRouter()

// Reactive data
const timePeriod = ref<'week' | 'month' | 'year'>('week')
const analysisChart = ref<HTMLCanvasElement>()
let chartInstance: Chart | null = null
const loading = ref(false)

// Dimension data - will be populated from database
const dimension1 = ref({
  selected: [] as string[],
  available: [] as string[]
})

const dimension2 = ref({
  selected: ['中性'], // 改為預設選擇中性，因為數據庫中的記錄都是NEUTRAL
  available: ['正面', '負面', '中性']
})

// Available items for dropdown (excluding already selected) - 保留但不再使用
const availableDimension1Items = computed(() => 
  dimension1.value.available.filter(item => !dimension1.value.selected.includes(item))
)

const availableDimension2Items = computed(() => 
  dimension2.value.available.filter(item => !dimension2.value.selected.includes(item))
)

// Chart legend items - 顯示維度組合
const chartLegendItems = computed(() => {
  const items: Array<{ label: string; color: string }> = []
  const colors = [
    '#3b82f6', // 藍色
    '#10b981', // 綠色
    '#8b5cf6', // 紫色
    '#f59e0b', // 橙色
    '#ef4444', // 紅色
    '#6366f1', // 靛藍色
    '#14b8a6', // 青色
    '#ec4899', // 粉色
    '#84cc16', // 萊姆色
    '#f97316'  // 深橙色
  ]
  let colorIndex = 0
  
  // 創建維度組合的圖例項目
  dimension1.value.selected.forEach(product => {
    dimension2.value.selected.forEach(sentiment => {
      const label = `${product} - ${sentiment}`
      items.push({ 
        label: label, 
        color: colors[colorIndex % colors.length] 
      })
      colorIndex++
    })
  })
  
  return items
})

// Table data
const tableData = ref<AnalysisResponse[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// Watch dimension changes
watch([dimension1, dimension2, timePeriod], () => {
  fetchData()
}, { deep: true })

// Fetch analysis data
const fetchData = async () => {
  // Don't fetch data if no product labels are selected
  if (dimension1.value.selected.length === 0) {
    console.warn('No product labels selected, skipping data fetch')
    return
  }
  
  loading.value = true
  const loadingInstance = ElLoading.service({
    target: '.analysis-content',
    text: '載入數據中...'
  })
  
  try {
    // Process selected products - backend now handles "未分類" correctly
    let productParams: string[] = dimension1.value.selected
    
    // Fetch time series data for chart
    // Handle "未分類" correctly for time series API
    let timeSeriesProducts: string[] | undefined = undefined
    if (dimension1.value.selected.includes('未分類') && dimension1.value.selected.length > 1) {
      // Include both unclassified and specific products - pass all selected
      timeSeriesProducts = dimension1.value.selected
    } else if (dimension1.value.selected.includes('未分類')) {
      // Only unclassified - pass undefined to get unclassified data
      timeSeriesProducts = undefined
    } else {
      // Only specific products
      timeSeriesProducts = dimension1.value.selected
    }
    
    console.log('Fetching time series data with products:', timeSeriesProducts, 'sentiments:', dimension2.value.selected)
    console.log('AnalysisView calling analysisService.getTimeSeriesData with:', {
      products: timeSeriesProducts,
      sentiments: dimension2.value.selected,
      timePeriod: timePeriod.value
    })
    
    try {
      const timeSeriesData = await analysisService.getTimeSeriesData(
        timeSeriesProducts,
        dimension2.value.selected,
        timePeriod.value
      )
      console.log('Received time series data:', timeSeriesData)
      updateChartData(timeSeriesData)
    } catch (chartError) {
      console.error('Failed to fetch chart data:', chartError)
      // Update chart with empty data to ensure it's visible even without data
      updateChartData({ labels: [], datasets: [] })
    }
    
    // Fetch table data
    const response = await analysisService.getAnalysisList({
      product_names: productParams.length > 0 ? productParams : undefined, // Don't send empty array, send undefined
      sentiments: dimension2.value.selected.map(item => {
        if (item === '正面') return 'POSITIVE' as const
        if (item === '負面') return 'NEGATIVE' as const
        return 'NEUTRAL' as const
      }),
      page: currentPage.value,
      page_size: pageSize.value
    })
    
    // Backend now handles filtering correctly, no need for client-side filtering
    tableData.value = response.items
    total.value = response.total
    
  } catch (error) {
    console.error('Failed to fetch data:', error)
    ElMessage.error('載入數據失敗')
  } finally {
    loading.value = false
    loadingInstance.close()
  }
}

// Dimension management functions
const addDimension1Item = (item: string) => {
  if (!dimension1.value.selected.includes(item)) {
    dimension1.value.selected.push(item)
  }
}

const removeDimension1Item = (item: string) => {
  if (dimension1.value.selected.length > 1) {
    dimension1.value.selected = dimension1.value.selected.filter(i => i !== item)
  } else {
    ElMessage.warning('請至少保留一個商品分類')
  }
}

const addDimension2Item = (item: string) => {
  if (!dimension2.value.selected.includes(item)) {
    dimension2.value.selected.push(item)
  }
}

const removeDimension2Item = (item: string) => {
  if (dimension2.value.selected.length > 1) {
    dimension2.value.selected = dimension2.value.selected.filter(i => i !== item)
  }
}

// Chart initialization
const initChart = () => {
  console.log('initChart called, canvas ref:', analysisChart.value)
  
  if (!analysisChart.value) {
    console.warn('Canvas element not found for chart initialization')
    return
  }

  // Destroy existing chart instance if it exists
  if (chartInstance) {
    console.log('Destroying existing chart instance')
    chartInstance.destroy()
    chartInstance = null
  }

  const ctx = analysisChart.value.getContext('2d')
  if (!ctx) {
    console.error('Failed to get 2D context from canvas')
    return
  }

  console.log('Initializing chart with canvas:', analysisChart.value)
  console.log('Canvas dimensions:', analysisChart.value.offsetWidth, 'x', analysisChart.value.offsetHeight)

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: []
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            color: '#6b7280'
          },
          grid: {
            color: 'rgba(0, 0, 0, 0.1)'
          }
        },
        x: {
          grid: {
            display: false
          },
          ticks: {
            color: '#6b7280'
          }
        }
      },
      elements: {
        point: {
          radius: 4,
          hoverRadius: 6
        },
        line: {
          tension: 0  // This makes the lines straight instead of curved
        }
      }
    }
  })

  console.log('Chart initialized successfully:', chartInstance)
}

// Update chart with real data
const updateChartData = (data: TimeSeriesData) => {
  if (!chartInstance) {
    console.warn('Chart instance not available for data update, attempting to reinitialize')
    initChart()
    if (!chartInstance) {
      console.error('Failed to initialize chart instance')
      return
    }
  }
  
  console.log('Updating chart with data:', data)
  console.log('Chart instance available:', !!chartInstance)
  console.log('Chart canvas element:', analysisChart.value)
  
  // Handle empty data
  if (!data || !data.labels || !data.datasets) {
    console.warn('Empty or invalid chart data received')
    chartInstance.data.labels = []
    chartInstance.data.datasets = []
    chartInstance.update()
    return
  }
  
  // Additional data validation
  if (data.datasets.length === 0) {
    console.warn('No datasets in chart data')
    return
  }
  
  console.log('Chart data validation passed:', {
    labels: data.labels.length,
    datasets: data.datasets.length,
    firstDataset: data.datasets[0]?.label,
    dataPoints: data.datasets[0]?.data?.length
  })
  
  // Format labels to show only date
  const formattedLabels = data.labels.map(label => {
    const date = new Date(label)
    return `${date.getFullYear()}.${String(date.getMonth() + 1).padStart(2, '0')}.${String(date.getDate()).padStart(2, '0')}`
  })
  
  // Define colors for datasets
  const colors = [
    '#3b82f6', // 藍色
    '#10b981', // 綠色
    '#8b5cf6', // 紫色
    '#f59e0b', // 橙色
    '#ef4444', // 紅色
    '#6366f1', // 靛藍色
    '#14b8a6', // 青色
    '#ec4899', // 粉色
    '#84cc16', // 萊姆色
    '#f97316'  // 深橙色
  ]
  
  // Ensure all datasets have proper styling and colors
  const datasetsWithStyling = data.datasets.map((dataset, index) => ({
    ...dataset,
    tension: 0,
    borderColor: colors[index % colors.length],
    backgroundColor: colors[index % colors.length] + '20', // 20% opacity for fill
    borderWidth: 2,
    fill: false,
    pointBackgroundColor: colors[index % colors.length],
    pointBorderColor: '#ffffff',
    pointBorderWidth: 2,
    pointRadius: 4,
    pointHoverRadius: 6
  }))
  
  console.log('Setting chart labels:', formattedLabels)
  console.log('Setting chart datasets:', datasetsWithStyling)
  
  chartInstance.data.labels = formattedLabels
  chartInstance.data.datasets = datasetsWithStyling
  
  console.log('Chart update starting...')
  chartInstance.update()
  console.log('Chart update completed')
  
  console.log('Final chart state:', {
    labels: chartInstance.data.labels,
    datasetCount: chartInstance.data.datasets.length,
    chartType: chartInstance.config.type
  })
}

// Parse feedback categories (handle multiple categories separated by various delimiters)
const parseFeedbackCategories = (feedbackCategory: string | null | undefined): string[] => {
  if (!feedbackCategory) return []
  
  // Split by common delimiters: space, comma, Chinese comma, slash, semicolon
  // Handle the case where categories are like "物流/配送 口味研發"
  const categories = feedbackCategory
    .split(/[\s,，\/;；]+/)
    .map(cat => cat.trim())
    .filter(cat => cat.length > 0 && cat !== '無' && cat !== 'null')
  
  return categories.length > 0 ? categories : []
}

// Format date for display
const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// Action handlers
const saveReport = async () => {
  try {
    // TODO: Implement report saving functionality
    ElMessage.success('報表已匯出')
  } catch (error) {
    ElMessage.error('匯出報表失敗')
  }
}

const viewDetails = (row: AnalysisResponse) => {
  router.push({
    name: 'AnalysisDetail',
    params: { id: row.file_id }
  })
}

// Load product labels from database
const loadProductLabels = async () => {
  try {
    const productLabels = await labelsService.getProductLabels()
    // Only use active labels
    const activeLabels = productLabels.filter(label => label.is_active)
    const labelNames = activeLabels.map(label => label.name)
    
    // Add a special option for records without product classification
    const newAvailable = ['未分類', ...labelNames]
    
    // Preserve current selections that are still valid
    const validSelections = dimension1.value.selected.filter(item => newAvailable.includes(item))
    
    dimension1.value.available = newAvailable
    
    // Set default selected items - start with "未分類" to show existing records
    if (validSelections.length > 0) {
      dimension1.value.selected = validSelections
    } else {
      dimension1.value.selected = ['未分類'] // 預設選擇未分類，這樣可以顯示現有的分析記錄
    }
    
    // Explicitly trigger data fetch after setting selections
    await nextTick() // Ensure reactivity updates complete
    await fetchData()
  } catch (error) {
    console.error('Failed to load product labels:', error)
    ElMessage.error('載入商品分類失敗')
    // Fallback to hardcoded values
    dimension1.value.available = ['未分類', '包子', '饅頭', '湯包', '燒餅', '餡餅', '水餃']
    dimension1.value.selected = ['未分類']
    
    // Also trigger data fetch for fallback data
    await nextTick()
    await fetchData()
  }
}



// Lifecycle
onMounted(async () => {
  console.log('Analysis page mounted')
  await nextTick()
  
  // Ensure DOM is fully ready before initializing chart
  await new Promise(resolve => {
    setTimeout(() => {
      console.log('Initializing chart after DOM ready')
      initChart()
      resolve(true)
    }, 100)
  })
  
  await loadProductLabels()
  // fetchData() is now called within loadProductLabels() after setting default selections
})
</script>

<style scoped>
.analysis-page {
  min-height: 100vh;
  background-color: #f3f4f6;
}

.page-header {
  background: white;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  padding: 2rem;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.breadcrumb {
  font-size: 0.875rem;
  color: #6b7280;
  margin-bottom: 0.5rem;
}

.breadcrumb-link {
  color: #6b7280;
  text-decoration: none;
}

.breadcrumb-link:hover {
  color: #3b82f6;
}

.breadcrumb-separator {
  margin: 0 0.5rem;
}

.breadcrumb-current {
  color: #1f2937;
}

.page-title {
  font-size: 2rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.time-select {
  width: 120px;
}

.analysis-content {
  padding: 2rem;
}

.dimensions-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.dimension-card {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  border: 1px solid #e5e7eb;
}

.dimension-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.dimension-title {
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.dimension-items {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.25rem;
}

.dimension-item {
  display: inline-block;
  padding: 0.5rem 1rem;
  background-color: #f3f4f6;
  border-radius: 6px;
  color: #374151;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.dimension-item.selected {
  background-color: #3b82f6;
  color: white;
}

.dimension-item:hover {
  opacity: 0.8;
}

.dimension-connector {
  color: #6b7280;
  margin: 0 0.5rem;
  font-size: 0.875rem;
}

.add-button {
  color: #6b7280;
  border: 1px dashed #d1d5db;
  background: transparent;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
}

.add-button:hover {
  border-color: #3b82f6;
  color: #3b82f6;
}

.chart-section {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.chart-time-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.chart-filter {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #6b7280;
}

.filter-count {
  font-size: 0.875rem;
}

.chart-container {
  position: relative;
  height: 400px;
  width: 100%;
  margin: 1.25rem 0;
}

.chart-container canvas {
  width: 100% !important;
  height: 100% !important;
}

.chart-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f9fafb;
  border-radius: 8px;
}

.placeholder-content {
  text-align: center;
  color: #6b7280;
}

.placeholder-content p {
  margin-top: 1rem;
  font-size: 0.875rem;
}

.chart-legend {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
  margin-top: 1rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.75rem;
}

.legend-color {
  width: 12px;
  height: 3px;
  border-radius: 2px;
}

.data-table-section {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}

.table-container {
  padding: 1.5rem;
}

.category-tag {
  margin-right: 0.25rem;
  margin-bottom: 0.25rem;
}

.status-物流配送 {
  background-color: #dbeafe;
  color: #1d4ed8;
  border: none;
}

.status-口味研發 {
  background-color: #dcfce7;
  color: #16a34a;
  border: none;
}

.status-活動價惠 {
  background-color: #fef3c7;
  color: #d97706;
  border: none;
}

.status-包裝設計 {
  background-color: #e0e7ff;
  color: #4338ca;
  border: none;
}

.status-客服態度 {
  background-color: #fee2e2;
  color: #dc2626;
  border: none;
}

.status-品質問題 {
  background-color: #fecaca;
  color: #b91c1c;
  border: none;
}

.status-價格反饋 {
  background-color: #fed7aa;
  color: #c2410c;
  border: none;
}

.product-tag {
  margin-right: 0.25rem;
  margin-bottom: 0.25rem;
}

.product-包子 {
  background-color: #dbeafe;
  color: #1d4ed8;
  border: none;
}

.product-饅頭 {
  background-color: #fce7f3;
  color: #be185d;
  border: none;
}

.product-unclassified {
  background-color: #f3f4f6;
  color: #6b7280;
  border: none;
}

.sentiment-positive {
  color: #3333FF;
  font-weight: 500;
}

.sentiment-negative {
  color: #FF7676;
  font-weight: 500;
}

.sentiment-neutral {
  color: #FFC18F;
  font-weight: 500;
}

/* Responsive design */
@media (max-width: 1024px) {
  .dimensions-section {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .analysis-content {
    padding: 1rem;
  }
  
  .header-content {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: center;
  }
  
  .chart-legend {
    flex-wrap: wrap;
    gap: 1rem;
  }
}
</style>