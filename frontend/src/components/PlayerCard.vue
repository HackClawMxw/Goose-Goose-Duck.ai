<template>
  <div class="player-card" :class="cardClass">
    <div class="avatar">
      {{ player.name.charAt(0) }}
    </div>
    <div class="info">
      <div class="name">
        <span class="status-indicator" :class="player.is_alive ? 'alive' : 'dead'"></span>
        {{ player.name }}
      </div>
      <div v-if="showRole && player.role" class="role">
        <span class="role-tag" :class="campClass">{{ player.role }}</span>
      </div>
      <div v-else class="status">
        {{ player.is_alive ? '存活' : '已出局' }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PlayerInfo } from '@/types'

const props = defineProps<{
  player: PlayerInfo
  showRole?: boolean
}>()

const cardClass = computed(() => ({
  dead: !props.player.is_alive,
}))

const campClass = computed(() => {
  if (!props.player.camp) return ''
  const camp = props.player.camp.toLowerCase()
  if (camp.includes('鹅')) return 'camp-goose'
  if (camp.includes('鸭')) return 'camp-duck'
  if (camp.includes('中立') || camp.includes('呆呆鸟')) return 'camp-dodo'
  return ''
})
</script>

<style scoped>
.player-card {
  display: flex;
  align-items: center;
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.player-card:hover {
  background: #f0f0f0;
}

.player-card.dead {
  opacity: 0.6;
  background: #f5f5f5;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
  margin-right: 12px;
}

.info {
  flex: 1;
}

.name {
  font-weight: 500;
  font-size: 14px;
  color: #303133;
  display: flex;
  align-items: center;
}

.status-indicator {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 8px;
}

.status-indicator.alive {
  background-color: #52c41a;
}

.status-indicator.dead {
  background-color: #d9d9d9;
}

.role {
  margin-top: 4px;
}

.role-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.camp-goose {
  background: #f6ffed;
  color: #52c41a;
}

.camp-duck {
  background: #fff7e6;
  color: #fa8c16;
}

.camp-dodo {
  background: #f9f0ff;
  color: #722ed1;
}

.status {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
