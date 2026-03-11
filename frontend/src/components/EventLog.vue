<template>
  <div class="event-log-content">
    <div v-if="events.length === 0" class="empty">
      暂无事件
    </div>
    <div v-else class="events-list">
      <div
        v-for="(event, index) in reversedEvents"
        :key="index"
        class="event-item"
        :class="event.type"
      >
        <span class="event-icon">{{ getEventIcon(event.type) }}</span>
        <span class="event-text">{{ event.text }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Dialogue } from '@/types'

const props = defineProps<{
  dialogues: Dialogue[]
}>()

interface Event {
  type: 'discussion' | 'voting' | 'system'
  text: string
  round: number
}

// 将对话转换为事件
const events = computed<Event[]>(() => {
  const result: Event[] = []
  let lastPhase = ''
  let lastRound = 0

  props.dialogues.forEach((d) => {
    // 阶段变化时添加系统事件
    if (d.round !== lastRound) {
      result.push({
        type: 'system',
        text: `第 ${d.round} 轮开始`,
        round: d.round,
      })
      lastRound = d.round
    }

    if (d.phase !== lastPhase) {
      const phaseText = d.phase === 'discussion' ? '讨论阶段' : '投票阶段'
      result.push({
        type: 'system',
        text: phaseText,
        round: d.round,
      })
      lastPhase = d.phase
    }

    // 投票事件
    if (d.phase === 'voting' && d.content.includes('投票给')) {
      result.push({
        type: 'voting',
        text: d.content,
        round: d.round,
      })
    }
  })

  return result
})

// 反转显示（最新在上）
const reversedEvents = computed(() => [...events.value].reverse())

function getEventIcon(type: string) {
  const icons: Record<string, string> = {
    discussion: '💬',
    voting: '🗳️',
    system: '📢',
  }
  return icons[type] || '•'
}
</script>

<style scoped>
.event-log-content {
  flex: 1;
  overflow-y: auto;
  font-size: 13px;
}

.empty {
  text-align: center;
  color: #909399;
  padding: 20px;
}

.events-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.event-item {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 6px 8px;
  background: #f9fafb;
  border-radius: 4px;
}

.event-icon {
  flex-shrink: 0;
}

.event-text {
  color: #606266;
  line-height: 1.4;
}

.event-item.system {
  background: #e6f7ff;
}

.event-item.system .event-text {
  color: #1890ff;
  font-weight: 500;
}

.event-item.voting {
  background: #fff7e6;
}

.event-item.voting .event-text {
  color: #fa8c16;
}
</style>
