<template>
  <div class="game-map">
    <div class="map-header">
      <h3>🚀 太空飞船</h3>
      <div class="task-progress">
        <span>任务进度</span>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: taskPercentage + '%' }"></div>
        </div>
        <span class="progress-text">{{ taskCompleted }}/{{ taskTotal }}</span>
      </div>
    </div>

    <div class="map-container">
      <div class="room-grid">
        <div
          v-for="room in rooms"
          :key="room.id"
          class="room"
          :class="{
            'has-emergency': room.has_emergency_button,
            'has-vent': room.has_vent,
            'current-room': room.id === currentRoomId
          }"
          @click="selectRoom(room.id)"
        >
          <div class="room-name">{{ room.name }}</div>

          <!-- 房间内的玩家 -->
          <div class="room-players">
            <div
              v-for="player in getPlayersInRoom(room.id)"
              :key="player.agent_id"
              class="player-dot"
              :class="{ dead: !player.is_alive, ghost: player.is_ghost }"
              :title="player.name"
            >
              {{ player.name.slice(0, 2) }}
            </div>
          </div>

          <!-- 房间任务 -->
          <div class="room-tasks" v-if="room.tasks.length > 0">
            <span
              v-for="task in room.tasks"
              :key="task.id"
              class="task-indicator"
              :class="{ completed: task.completed }"
            >
              {{ task.completed ? '✓' : '○' }}
            </span>
          </div>

          <!-- 房间图标 -->
          <div class="room-icons">
            <span v-if="room.has_vent" class="icon-vent" title="通风管">🕳️</span>
            <span v-if="room.has_emergency_button" class="icon-emergency" title="紧急会议">🚨</span>
          </div>
        </div>
      </div>

      <!-- 连接线（简化版） -->
      <svg class="connections" viewBox="0 0 800 600">
        <line
          v-for="(conn, idx) in connections"
          :key="idx"
          :x1="conn.x1"
          :y1="conn.y1"
          :x2="conn.x2"
          :y2="conn.y2"
          class="connection-line"
        />
      </svg>
    </div>

    <!-- 图例 -->
    <div class="map-legend">
      <span><span class="legend-dot current"></span> 当前位置</span>
      <span><span class="legend-dot vent"></span> 通风管</span>
      <span><span class="legend-dot emergency"></span> 紧急会议</span>
      <span><span class="legend-task">○</span> 未完成任务</span>
      <span><span class="legend-task completed">✓</span> 已完成任务</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  rooms: Record<string, any>
  players: Record<string, any>
  taskCompleted: number
  taskTotal: number
  currentRoomId?: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'selectRoom', roomId: string): void
}>()

const rooms = computed(() => {
  return Object.values(props.rooms || {})
})

const taskPercentage = computed(() => {
  if (props.taskTotal === 0) return 0
  return Math.round((props.taskCompleted / props.taskTotal) * 100)
})

const connections = computed(() => {
  // 简化的连接线坐标（实际应用中需要根据布局计算）
  const coords: any[] = []
  // 这里可以添加实际的房间连接坐标
  return coords
})

function getPlayersInRoom(roomId: string) {
  return Object.values(props.players || {}).filter(
    (p: any) => p.room_id === roomId
  )
}

function selectRoom(roomId: string) {
  emit('selectRoom', roomId)
}
</script>

<style scoped>
.game-map {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 12px;
  padding: 16px;
  color: #fff;
}

.map-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.map-header h3 {
  margin: 0;
  font-size: 18px;
}

.task-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.progress-bar {
  width: 120px;
  height: 8px;
  background: #2a2a4a;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4ade80, #22c55e);
  transition: width 0.3s ease;
}

.progress-text {
  font-weight: bold;
  color: #4ade80;
}

.map-container {
  position: relative;
  min-height: 400px;
}

.room-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}

.room {
  background: #2a2a4a;
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  min-height: 80px;
}

.room:hover {
  background: #3a3a5a;
  transform: translateY(-2px);
}

.room.current-room {
  border: 2px solid #60a5fa;
  box-shadow: 0 0 10px rgba(96, 165, 250, 0.3);
}

.room.has-vent {
  border-left: 3px solid #f97316;
}

.room.has-emergency {
  border-right: 3px solid #ef4444;
}

.room-name {
  font-size: 12px;
  font-weight: bold;
  margin-bottom: 8px;
}

.room-players {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.player-dot {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #4ade80;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: bold;
  color: #000;
}

.player-dot.dead {
  background: #6b7280;
  text-decoration: line-through;
}

.player-dot.ghost {
  opacity: 0.5;
}

.room-tasks {
  display: flex;
  gap: 4px;
  margin-top: 8px;
}

.task-indicator {
  font-size: 12px;
  color: #6b7280;
}

.task-indicator.completed {
  color: #4ade80;
}

.room-icons {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  gap: 4px;
  font-size: 12px;
}

.connections {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.connection-line {
  stroke: #4a4a6a;
  stroke-width: 2;
  stroke-dasharray: 4;
}

.map-legend {
  display: flex;
  gap: 16px;
  margin-top: 16px;
  font-size: 12px;
  color: #9ca3af;
}

.legend-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 4px;
}

.legend-dot.current {
  background: #60a5fa;
}

.legend-dot.vent {
  background: #f97316;
}

.legend-dot.emergency {
  background: #ef4444;
}
</style>
