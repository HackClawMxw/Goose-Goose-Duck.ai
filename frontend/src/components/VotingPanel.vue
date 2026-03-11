<template>
  <div class="voting-panel-content">
    <div v-if="Object.keys(votes).length === 0" class="empty">
      暂无投票
    </div>
    <div v-else class="votes-list">
      <div v-for="(voted, voter) in votes" :key="voter" class="vote-item">
        <span class="voter">{{ voter }}</span>
        <span class="arrow">→</span>
        <span class="voted">{{ voted }}</span>
      </div>
    </div>

    <!-- 投票统计 -->
    <div v-if="voteStats.length > 0" class="vote-stats">
      <h4>得票统计</h4>
      <div v-for="stat in voteStats" :key="stat.name" class="stat-item">
        <span class="stat-name">{{ stat.name }}</span>
        <div class="stat-bar-container">
          <div class="stat-bar" :style="{ width: stat.percentage + '%' }"></div>
        </div>
        <span class="stat-count">{{ stat.count }} 票</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PlayerInfo } from '@/types'

const props = defineProps<{
  votes: Record<string, string>
  players: PlayerInfo[]
}>()

// 计算投票统计
const voteStats = computed(() => {
  const counts: Record<string, number> = {}

  // 统计每个玩家被投票数
  Object.values(props.votes).forEach((voted) => {
    counts[voted] = (counts[voted] || 0) + 1
  })

  // 转换为数组并排序
  const stats = Object.entries(counts)
    .map(([name, count]) => ({
      name,
      count,
      percentage: Object.keys(props.votes).length > 0
        ? (count / Object.keys(props.votes).length) * 100
        : 0,
    }))
    .sort((a, b) => b.count - a.count)

  return stats
})
</script>

<style scoped>
.voting-panel-content {
  overflow-y: auto;
}

.empty {
  text-align: center;
  color: #909399;
  padding: 20px;
}

.votes-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.vote-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f9fafb;
  border-radius: 6px;
  font-size: 14px;
}

.voter {
  font-weight: 500;
  color: #303133;
}

.arrow {
  color: #909399;
}

.voted {
  color: #606266;
}

.vote-stats {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.vote-stats h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #303133;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 13px;
}

.stat-name {
  width: 60px;
  color: #606266;
}

.stat-bar-container {
  flex: 1;
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.stat-bar {
  height: 100%;
  background: linear-gradient(90deg, #fa8c16 0%, #fa541c 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.stat-count {
  width: 40px;
  text-align: right;
  color: #909399;
  font-size: 12px;
}
</style>
