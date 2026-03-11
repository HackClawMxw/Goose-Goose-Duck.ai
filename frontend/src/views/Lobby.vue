<template>
  <div class="lobby-container">
    <div class="lobby-content">
      <h1 class="title">🦆 Goose-Goose-Duck.ai</h1>
      <p class="subtitle">AI 鹅鸭杀游戏</p>

      <el-card class="create-card">
        <template #header>
          <div class="card-header">
            <span>创建新游戏</span>
          </div>
        </template>

        <el-form :model="form" label-width="100px">
          <el-form-item label="玩家数量">
            <el-input-number v-model="playerCount" :min="4" :max="12" />
          </el-form-item>

          <el-form-item label="游戏速度">
            <el-select v-model="gameSpeed" placeholder="选择游戏速度">
              <el-option label="快速 (0.5秒)" :value="0.5" />
              <el-option label="正常 (1秒)" :value="1.0" />
              <el-option label="慢速 (2秒)" :value="2.0" />
            </el-select>
          </el-form-item>
        </el-form>

        <div class="button-group">
          <el-button type="primary" size="large" @click="handleCreateGame" :loading="loading">
            创建游戏
          </el-button>
        </div>
      </el-card>

      <el-card v-if="error" class="error-card">
        <el-alert :title="error" type="error" show-icon />
      </el-card>

      <div class="description">
        <h3>游戏说明</h3>
        <ul>
          <li>🪿 鹅阵营：通过投票找出所有鸭子</li>
          <li>🦆 鸭阵营：隐藏身份，消灭鹅阵营</li>
          <li>🐦 呆呆鸟：被投票出局即可获胜</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useGameStore } from '@/stores/game'
import { ElMessage } from 'element-plus'

const router = useRouter()
const gameStore = useGameStore()

const playerCount = ref(6)
const gameSpeed = ref(1.0)
const loading = ref(false)
const error = ref<string | null>(null)

async function handleCreateGame() {
  loading.value = true
  error.value = null

  try {
    // 生成玩家名称
    const playerNames = Array.from(
      { length: playerCount.value },
      (_, i) => `玩家${i + 1}`
    )

    await gameStore.createGame(playerNames)
    ElMessage.success('游戏创建成功！')

    // 跳转到游戏页面
    if (gameStore.gameId) {
      router.push(`/game/${gameStore.gameId}`)
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '创建游戏失败'
    ElMessage.error(error.value)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.lobby-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

.lobby-content {
  max-width: 500px;
  width: 100%;
}

.title {
  text-align: center;
  font-size: 2.5rem;
  color: white;
  margin-bottom: 0.5rem;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.subtitle {
  text-align: center;
  font-size: 1.2rem;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 2rem;
}

.create-card {
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.card-header {
  font-size: 1.2rem;
  font-weight: bold;
}

.button-group {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.button-group .el-button {
  width: 100%;
}

.error-card {
  margin-top: 20px;
}

.description {
  margin-top: 30px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.description h3 {
  margin-bottom: 15px;
  color: #333;
}

.description ul {
  list-style: none;
  padding: 0;
}

.description li {
  padding: 8px 0;
  color: #666;
}
</style>
