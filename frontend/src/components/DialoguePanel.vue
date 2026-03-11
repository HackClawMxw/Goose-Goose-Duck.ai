<template>
  <div class="dialogue-panel-content" ref="scrollContainer">
    <div v-if="dialogues.length === 0" class="empty">
      暂无对话记录
    </div>
    <div
      v-for="(dialogue, index) in dialogues"
      :key="index"
      class="dialogue-item dialogue-bubble"
    >
      <div class="dialogue-header">
        <span class="speaker">{{ dialogue.speaker }}</span>
        <span class="phase-tag" :class="getPhaseClass(dialogue.phase)">
          {{ getPhaseText(dialogue.phase) }}
        </span>
      </div>
      <div class="dialogue-content">
        {{ dialogue.content }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import type { Dialogue } from '@/types'

const props = defineProps<{
  dialogues: Dialogue[]
}>()

const scrollContainer = ref<HTMLElement | null>(null)

// 自动滚动到底部
watch(
  () => props.dialogues.length,
  async () => {
    await nextTick()
    if (scrollContainer.value) {
      scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight
    }
  }
)

function getPhaseClass(phase: string) {
  const classMap: Record<string, string> = {
    discussion: 'phase-discussion',
    voting: 'phase-voting',
  }
  return classMap[phase] || ''
}

function getPhaseText(phase: string) {
  const textMap: Record<string, string> = {
    discussion: '讨论',
    voting: '投票',
  }
  return textMap[phase] || phase
}
</script>

<style scoped>
.dialogue-panel-content {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.empty {
  text-align: center;
  color: #909399;
  padding: 40px;
}

.dialogue-item {
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
  border-left: 3px solid #e0e0e0;
}

.dialogue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.speaker {
  font-weight: 500;
  color: #303133;
}

.phase-tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}

.phase-discussion {
  background: #e6f7ff;
  color: #1890ff;
}

.phase-voting {
  background: #fff7e6;
  color: #fa8c16;
}

.dialogue-content {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  word-break: break-word;
}
</style>
