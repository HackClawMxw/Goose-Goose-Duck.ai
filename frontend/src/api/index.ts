/**
 * HTTP API 客户端
 */
import type { PlayerInfo, GameStateResponse, GameSummaryResponse, GameCreatedResponse } from '@/types'

const API_BASE = '/api'

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

export const api = {
  // 游戏管理
  async createGame(playerNames?: string[], configOverride?: Record<string, unknown>): Promise<GameCreatedResponse> {
    return fetchAPI('/games', {
      method: 'POST',
      body: JSON.stringify({ player_names: playerNames, config_override: configOverride }),
    })
  },

  async getGameState(gameId: string): Promise<GameStateResponse> {
    return fetchAPI(`/games/${gameId}`)
  },

  async startGame(gameId: string, delaySeconds = 1.0): Promise<{ status: string; message: string }> {
    return fetchAPI(`/games/${gameId}/start`, {
      method: 'POST',
      body: JSON.stringify({ auto_play: true, delay_seconds: delaySeconds }),
    })
  },

  async pauseGame(gameId: string): Promise<{ status: string }> {
    return fetchAPI(`/games/${gameId}/pause`, { method: 'POST' })
  },

  async resumeGame(gameId: string): Promise<{ status: string }> {
    return fetchAPI(`/games/${gameId}/resume`, { method: 'POST' })
  },

  async getGameSummary(gameId: string): Promise<GameSummaryResponse> {
    return fetchAPI(`/games/${gameId}/summary`)
  },

  async listGames(): Promise<{ games: Array<{ game_id: string; status: string; round: number; phase: string; player_count: number }> }> {
    return fetchAPI('/games')
  },

  async deleteGame(gameId: string): Promise<{ status: string }> {
    return fetchAPI(`/games/${gameId}`, { method: 'DELETE' })
  },

  async healthCheck(): Promise<{ status: string; message: string }> {
    return fetchAPI('/health')
  },
}

export default api
