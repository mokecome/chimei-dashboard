<template>
  <div class="dimension-selector">
    <div class="dimension-grid">
      <!-- 维度一 -->
      <div class="dimension-card">
        <div class="dimension-header">
          <h3 class="dimension-title">維度一</h3>
          <el-dropdown @command="handleDimensionTypeChange">
            <el-button size="small" text>
              {{ getDimensionTypeName(dimensions[0]?.type) }}
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="product,0">商品分類</el-dropdown-item>
                <el-dropdown-item command="feedback,0">反饋分類</el-dropdown-item>
                <el-dropdown-item command="sentiment,0">評價傾向</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        
        <div class="dimension-content">
          <div class="selected-items">
            <el-tag
              v-for="item in dimensions[0]?.items || []"
              :key="item"
              closable
              @close="removeDimensionItem(0, item)"
              class="dimension-tag"
            >
              {{ item }}
            </el-tag>
            
            <el-dropdown @command="(item) => addDimensionItem(0, item)" trigger="click">
              <el-button size="small" class="add-button">
                <el-icon><Plus /></el-icon>
                新增比較項目+
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item
                    v-for="option in getAvailableOptions(0)"
                    :key="option"
                    :command="option"
                  >
                    {{ option }}
                  </el-dropdown-item>
                  <el-dropdown-item v-if="getAvailableOptions(0).length === 0" disabled>
                    無可用選項
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>

      <!-- 维度二 -->
      <div class="dimension-card">
        <div class="dimension-header">
          <h3 class="dimension-title">維度二</h3>
          <el-dropdown @command="handleDimensionTypeChange">
            <el-button size="small" text>
              {{ getDimensionTypeName(dimensions[1]?.type) }}
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="product,1">商品分類</el-dropdown-item>
                <el-dropdown-item command="feedback,1">反饋分類</el-dropdown-item>
                <el-dropdown-item command="sentiment,1">評價傾向</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        
        <div class="dimension-content">
          <div class="selected-items">
            <el-tag
              v-for="item in dimensions[1]?.items || []"
              :key="item"
              type="success"
              closable
              @close="removeDimensionItem(1, item)"
              class="dimension-tag"
            >
              {{ item }}
            </el-tag>
            
            <el-dropdown @command="(item) => addDimensionItem(1, item)" trigger="click">
              <el-button size="small" class="add-button">
                <el-icon><Plus /></el-icon>
                新增指標+
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item
                    v-for="option in getAvailableOptions(1)"
                    :key="option"
                    :command="option"
                  >
                    {{ option }}
                  </el-dropdown-item>
                  <el-dropdown-item v-if="getAvailableOptions(1).length === 0" disabled>
                    無可用選項
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
    </div>

    <!-- 图表类型选择 -->
    <div class="chart-type-selector">
      <div class="chart-type-label">圖表類型：</div>
      <el-radio-group v-model="chartType" @change="handleChartTypeChange">
        <el-radio-button label="line">折線圖</el-radio-button>
        <el-radio-button label="bar">長條圖</el-radio-button>
        <el-radio-button label="pie">圓餅圖</el-radio-button>
      </el-radio-group>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ArrowDown, Plus } from '@element-plus/icons-vue'
import type { ChartDimension } from '@/types/analysis'

interface Props {
  dimensions: ChartDimension[]
  chartType: string
  productLabels: string[]
  feedbackLabels: string[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:dimensions': [dimensions: ChartDimension[]]
  'update:chartType': [type: string]
}>()

const chartType = ref(props.chartType)

// 维度类型名称映射
const getDimensionTypeName = (type?: string) => {
  const names = {
    product: '商品分類',
    feedback: '反饋分類',
    sentiment: '評價傾向',
    time: '時間'
  }
  return names[type as keyof typeof names] || '請選擇'
}

// 获取可用选项
const getAvailableOptions = (dimensionIndex: number) => {
  const dimension = props.dimensions[dimensionIndex]
  if (!dimension) return []

  let allOptions: string[] = []
  
  switch (dimension.type) {
    case 'product':
      allOptions = props.productLabels
      break
    case 'feedback':
      allOptions = props.feedbackLabels
      break
    case 'sentiment':
      allOptions = ['正面', '負面', '中立']
      break
    default:
      return []
  }

  // 排除已选择的项目
  return allOptions.filter(option => !dimension.items.includes(option))
}

// 处理维度类型变化
const handleDimensionTypeChange = (command: string) => {
  const [type, indexStr] = command.split(',')
  const index = parseInt(indexStr)
  
  const newDimensions = [...props.dimensions]
  if (newDimensions[index]) {
    newDimensions[index] = {
      ...newDimensions[index],
      type: type as any,
      items: [] // 重置选择的项目
    }
  }
  
  emit('update:dimensions', newDimensions)
}

// 添加维度项目
const addDimensionItem = (dimensionIndex: number, item: string) => {
  const newDimensions = [...props.dimensions]
  if (newDimensions[dimensionIndex]) {
    const dimension = newDimensions[dimensionIndex]
    if (!dimension.items.includes(item)) {
      dimension.items = [...dimension.items, item]
    }
  }
  
  emit('update:dimensions', newDimensions)
}

// 移除维度项目
const removeDimensionItem = (dimensionIndex: number, item: string) => {
  const newDimensions = [...props.dimensions]
  if (newDimensions[dimensionIndex]) {
    const dimension = newDimensions[dimensionIndex]
    dimension.items = dimension.items.filter(i => i !== item)
  }
  
  emit('update:dimensions', newDimensions)
}

// 处理图表类型变化
const handleChartTypeChange = (type: string) => {
  emit('update:chartType', type)
}
</script>

<style scoped>
.dimension-selector {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  padding: 20px;
}

.dimension-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.dimension-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  background: #fafafa;
}

.dimension-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.dimension-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.dimension-content {
  display: flex;
  flex-direction: column;
}

.selected-items {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.dimension-tag {
  margin: 0;
}

.add-button {
  color: #6b7280;
  border: 1px dashed #d1d5db;
  background: transparent;
  font-size: 12px;
}

.add-button:hover {
  border-color: #3b82f6;
  color: #3b82f6;
}

.chart-type-selector {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}

.chart-type-label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .dimension-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .chart-type-selector {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .selected-items {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>