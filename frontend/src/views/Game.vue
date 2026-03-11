<template>
  <div class="game-container">
    <!-- 顶部状态栏 -->
    <div class="header">
      <div class="game-info">
        <span class="game-id">游戏 ID: {{ gameId }}</span>
        <span class="phase" :class="phaseClass">{{ phaseText }}</span>
        <span class="round">第 {{ round }} 轮</span>
        <span class="task-progress" v-if="taskProgress">
          任务: {{ taskProgress.completed }}/{{ taskProgress.total }}
        </span>
      </div>
      <div class="controls">
        <el-button v-if="!isRunning && !isGameOver" type="success" @click="handleStart">
          开始游戏
        </el-button>
        <el-button v-if="isRunning && !isPaused" type="warning" @click="handlePause">
          暂停
        </el-button>
        <el-button v-if="isRunning && isPaused" type="success" @click="handleResume">
          继续
        </el-button>
        <el-button type="info" @click="handleBack">返回大厅</el-button>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 左侧：玩家列表 -->
      <div class="players-panel">
        <h3>玩家 ({{ alivePlayers.length }}/{{ players.length }} 存活)</h3>
        <div class="players-grid">
          <PlayerCard
            v-for="player in players"
            :key="player.agent_id"
            :player="player"
            :show-role="isGameOver"
          />
        </div>
      </div>

      <!-- 中间：对话/地图区域 -->
      <div class="center-panel">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="💬 对话记录" name="dialogue">
            <DialoguePanel :dialogues="dialogues" />
          </el-tab-pane>
          <el-tab-pane label="🗺️ 地图" name="map">
            <GameMap
              :rooms="mapRooms"
              :players="mapPlayers"
              :task-completed="taskProgress?.completed || 0"
              :task-total="taskProgress?.total || 0"
            />
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- 右侧：投票/事件 -->
      <div class="side-panel">
        <h3>投票情况</h3>
        <VotingPanel :votes="votes" :players="players" />

        <h3 style="margin-top: 20px">游戏日志</h3>
        <EventLog :dialogues="dialogues" />
      </div>
    </div>

    <!-- 游戏结束弹窗 -->
    <el-dialog
      v-model="showGameOverDialog"
      title="游戏结束"
      width="400px"
      :close-on-click-modal="false"
    >
      <div class="game-over-content">
        <div class="result" :class="resultClass">
          {{ result }}
        </div>
        <el-button type="primary" @click="handleBack">返回大厅</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGameStore } from '@/stores/game'
import { ElMessage } from 'element-plus'
import PlayerCard from '@/components/PlayerCard.vue'
import DialoguePanel from '@/components/DialoguePanel.vue'
import VotingPanel from '@/components/VotingPanel.vue'
import EventLog from '@/components/EventLog.vue'
import GameMap from '@/components/GameMap.vue'

const route = useRoute()
const router = useRouter()
const gameStore = useGameStore()

const showGameOverDialog = ref(false)
const activeTab = ref('dialogue')

// 从路由获取游戏 ID
const gameId = computed(() => route.params.id as string || gameStore.gameId)
const phase = computed(() => gameStore.phase)
const round = computed(() => gameStore.round)
const players = computed(() => gameStore.players)
const alivePlayers = computed(() => gameStore.alivePlayers)
const dialogues = computed(() => gameStore.dialogues)
const votes = computed(() => gameStore.votes)
const isRunning = computed(() => gameStore.isRunning)
const isPaused = computed(() => gameStore.isPaused)
const result = computed(() => gameStore.result)
const isGameOver = computed(() => gameStore.isGameOver)

// 地图相关
const mapRooms = computed(() => gameStore.mapInfo?.rooms || {})
const mapPlayers = computed(() => {
  const pos: Record<string, any> = {}
  for (const p of players.value) {
    if (p.room_id) {
      pos[p.agent_id] = p
    }
  }
  return pos
})
const taskProgress = computed(() => gameStore.mapInfo?.task_progress || null)

// 阶段显示
const phaseText = computed(() => {
  const phaseMap: Record<string, string> = {
    init: '准备中',
    discussion: '讨论阶段',
    voting: '投票阶段',
    execution: '处决阶段',
    game_over: '游戏结束',
  }
  return phaseMap[phase.value] || phase.value
})

const phaseClass = computed(() => {
  const classMap: Record<string, string> = {
    discussion: 'phase-discussion',
    voting: 'phase-voting',
    execution: 'phase-execution',
  }
  return classMap[phase.value] || ''
})

const resultClass = computed(() => {
  if (!result.value) return ''
  if (result.value.includes('鹅')) return 'result-goose'
  if (result.value.includes('鸭')) return 'result-duck'
  if (result.value.includes('呆呆鸟')) return 'result-dodo'
  return ''
})

// 监听游戏结束
watch(isGameOver, (value) => {
  if (value) {
    showGameOverDialog.value = true
  }
})

// 开始游戏
async function handleStart() {
  try {
    await gameStore.startGame(1.0)
    ElMessage.success('游戏开始！')
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '启动游戏失败')
  }
}

// 暂停游戏
async function handlePause() {
  try {
    await gameStore.pauseGame()
    ElMessage.info('游戏已暂停')
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '暂停失败')
  }
}

// 继续游戏
async function handleResume() {
  try {
    await gameStore.resumeGame()
    ElMessage.success('游戏继续')
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '继续失败')
  }
}

// 返回大厅
function handleBack() {
  gameStore.reset()
  router.push('/')
}

// 初始化
onMounted(async () => {
  // 如果 URL 中有游戏 ID 但 store 中没有，尝试连接
  const id = route.params.id as string
  if (id && !gameStore.gameId) {
    gameStore.gameId = id
    try {
      await gameStore.connectWebSocket()
    } catch (e) {
      ElMessage.error('连接游戏失败')
      router.push('/')
    }
  }
})

onUnmounted(() => {
  // 不在这里断开 WebSocket，允许用户返回继续观看
})
</script>

<style scoped>
.game-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.game-info {
  display: flex;
  gap: 20px;
  align-items: center;
}

.game-id {
  color: #909399;
  font-size: 14px;
}

.phase {
  padding: 4px 12px;
  border-radius: 4px;
  font-weight: bold;
  font-size: 14px;
}

.phase-discussion {
  background: #e6f7ff;
  color: #1890ff;
}

.phase-voting {
  background: #fff7e6;
  color: #fa8c16;
}

.phase-execution {
  background: #fff1f0;
  color: #f5222d;
}

.round {
  font-size: 14px;
  color: #606266;
}

.controls {
  display: flex;
  gap: 10px;
}

.main-content {
  flex: 1;
  display: grid;
  grid-template-columns: 280px 1fr 280px;
  gap: 20px;
  padding: 20px;
  overflow: hidden;
}

.players-panel,
.center-panel,
.side-panel {
  background: white;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
}

.center-panel {
  overflow: hidden;
}

.center-panel :deep(.el-tabs) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.center-panel :deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
}

.center-panel :deep(.el-tab-pane) {
  height: 100%;
}

.task-progress {
  background: #f0f9eb;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 14px;
  color: #67c23a;
}

.players-panel h3,
.dialogue-panel h3,
.side-panel h3 {
  margin: 0 0 15px 0;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
  font-size: 16px;
  color: #303133;
}

.players-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
}

.dialogue-panel {
  overflow: hidden;
}

.game-over-content {
  text-align: center;
  padding: 20px;
}

.result {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 20px;
  padding: 20px;
  border-radius: 8px;
}

.result-goose {
  background: #f6ffed;
  color: #52c41a;
}

.result-duck {
  background: #fff7e6;
  color: #fa8c16;
}

.result-dodo {
  background: #f9f0ff;
  color: #722ed1;
}

@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr;
  }

  .players-panel,
  .side-panel {
    max-height: 300px;
  }
}
</style>
