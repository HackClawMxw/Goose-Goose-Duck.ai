/**
 * 游戏状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { PlayerInfo, Dialogue, GameState } from '@/types'
import { api } from '@/api'
import { GameWebSocket, type WebSocketEvent } from '@/api/websocket'

export const useGameStore = defineStore('game', () => {
  // 状态
  const gameId = ref<string | null>(null)
  const phase = ref('init')
  const round = ref(1)
  const result = ref<string | null>(null)
  const players = ref<PlayerInfo[]>([])
  const dialogues = ref<Dialogue[]>([])
  const votes = ref<Record<string, string>>({})
  const isRunning = ref(false)
  const isPaused = ref(false)
  const isConnected = ref(false)
  const error = ref<string | null>(null)

  // WebSocket 实例
  let ws: GameWebSocket | null = null

  // 计算属性
  const alivePlayers = computed(() => players.value.filter((p) => p.is_alive))
  const deadPlayers = computed(() => players.value.filter((p) => !p.is_alive))
  const isGameOver = computed(() => result.value !== null && result.value !== '游戏进行中')

  // Actions
  async function createGame(playerNames?: string[]) {
    try {
      error.value = null
      const response = await api.createGame(playerNames)
      gameId.value = response.game_id
      players.value = response.players
      phase.value = 'init'
      round.value = 1
      result.value = null
      dialogues.value = []
      votes.value = {}
      isRunning.value = false
      isPaused.value = false

      // 连接 WebSocket
      await connectWebSocket()

      return response
    } catch (e) {
      error.value = e instanceof Error ? e.message : '创建游戏失败'
      throw e
    }
  }

  async function startGame(delaySeconds = 1.0) {
    if (!gameId.value) return

    try {
      error.value = null
      await api.startGame(gameId.value, delaySeconds)
      isRunning.value = true
    } catch (e) {
      error.value = e instanceof Error ? e.message : '启动游戏失败'
      throw e
    }
  }

  async function pauseGame() {
    if (!gameId.value) return

    try {
      await api.pauseGame(gameId.value)
      isPaused.value = true
    } catch (e) {
      error.value = e instanceof Error ? e.message : '暂停游戏失败'
      throw e
    }
  }

  async function resumeGame() {
    if (!gameId.value) return

    try {
      await api.resumeGame(gameId.value)
      isPaused.value = false
    } catch (e) {
      error.value = e instanceof Error ? e.message : '恢复游戏失败'
      throw e
    }
  }

  async function connectWebSocket() {
    if (!gameId.value) return

    if (ws) {
      ws.disconnect()
    }

    ws = new GameWebSocket(gameId.value)

    // 注册事件处理器
    ws.on('game_started', handleGameStarted)
    ws.on('phase_changed', handlePhaseChanged)
    ws.on('dialogue', handleDialogue)
    ws.on('vote_cast', handleVoteCast)
    ws.on('player_died', handlePlayerDied)
    ws.on('game_over', handleGameOver)
    ws.on('error', handleError)

    await ws.connect()
    isConnected.value = true
  }

  function disconnectWebSocket() {
    if (ws) {
      ws.disconnect()
      ws = null
    }
    isConnected.value = false
  }

  // WebSocket 事件处理器
  function handleGameStarted(event: WebSocketEvent) {
    console.log('Game started:', event)
    if (event.players) {
      players.value = event.players
    }
    isRunning.value = true
  }

  function handlePhaseChanged(event: WebSocketEvent) {
    console.log('Phase changed:', event)
    if (event.phase) {
      phase.value = event.phase
    }
    if (event.round) {
      round.value = event.round
    }
  }

  function handleDialogue(event: WebSocketEvent) {
    console.log('Dialogue:', event)
    if (event.speaker && event.content) {
      dialogues.value.push({
        speaker: event.speaker,
        content: event.content,
        phase: event.phase || 'discussion',
        round: event.round || round.value,
        timestamp: event.timestamp,
      })
    }
  }

  function handleVoteCast(event: WebSocketEvent) {
    console.log('Vote cast:', event)
    if (event.voter && event.voted) {
      votes.value[event.voter] = event.voted
    }
  }

  function handlePlayerDied(event: WebSocketEvent) {
    console.log('Player died:', event)
    if (event.player_name) {
      const player = players.value.find((p) => p.name === event.player_name)
      if (player) {
        player.is_alive = false
        if (event.role) {
          player.role = event.role
        }
        if (event.camp) {
          player.camp = event.camp
        }
      }
    }
  }

  function handleGameOver(event: WebSocketEvent) {
    console.log('Game over:', event)
    if (event.result) {
      result.value = event.result
    }
    isRunning.value = false

    // 游戏结束后显示所有角色
    if (event.players) {
      players.value = event.players
    }
  }

  function handleError(event: WebSocketEvent) {
    console.error('WebSocket error:', event)
    error.value = event.message || '未知错误'
  }

  function reset() {
    disconnectWebSocket()
    gameId.value = null
    phase.value = 'init'
    round.value = 1
    result.value = null
    players.value = []
    dialogues.value = []
    votes.value = {}
    isRunning.value = false
    isPaused.value = false
    error.value = null
  }

  return {
    // 状态
    gameId,
    phase,
    round,
    result,
    players,
    dialogues,
    votes,
    isRunning,
    isPaused,
    isConnected,
    error,

    // 计算属性
    alivePlayers,
    deadPlayers,
    isGameOver,

    // Actions
    createGame,
    startGame,
    pauseGame,
    resumeGame,
    connectWebSocket,
    disconnectWebSocket,
    reset,
  }
})
