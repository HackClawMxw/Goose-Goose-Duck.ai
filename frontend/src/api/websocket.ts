/**
 * WebSocket 客户端
 */

export type WebSocketEventType =
  | 'game_started'
  | 'phase_changed'
  | 'dialogue'
  | 'vote_cast'
  | 'player_died'
  | 'player_killed'
  | 'game_over'
  | 'error'
  | 'subscribed'
  | 'position_update'
  | 'map_update'
  | 'body_discovered'
  | 'meeting_called'
  | 'task_completed'
  | 'vote_tie'

export interface WebSocketEvent {
  type: WebSocketEventType
  timestamp: number
  game_id?: string
  phase?: string
  round?: number
  speaker?: string
  content?: string
  voter?: string
  voted?: string
  player_name?: string
  role?: string
  camp?: string
  result?: string
  summary?: Record<string, unknown>
  players?: Array<{ agent_id: string; name: string; is_alive: boolean; role?: string; camp?: string }>
  message?: string
}

export type WebSocketEventHandler = (event: WebSocketEvent) => void

export class GameWebSocket {
  private ws: WebSocket | null = null
  private gameId: string
  private handlers: Map<WebSocketEventType, Set<WebSocketEventHandler>> = new Map()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  constructor(gameId: string) {
    this.gameId = gameId
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = window.location.host
      const url = `${protocol}//${host}/ws/${this.gameId}`

      this.ws = new WebSocket(url)

      this.ws.onopen = () => {
        console.log(`WebSocket connected to game ${this.gameId}`)
        this.reconnectAttempts = 0
        // 发送订阅消息
        this.send({ type: 'subscribe', game_id: this.gameId })
        resolve()
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WebSocketEvent
          this.handleEvent(data)
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        reject(error)
      }

      this.ws.onclose = () => {
        console.log('WebSocket closed')
        this.attemptReconnect()
      }
    })
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`Attempting reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
      setTimeout(() => {
        this.connect().catch(console.error)
      }, this.reconnectDelay * this.reconnectAttempts)
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  send(data: unknown) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  on(eventType: WebSocketEventType, handler: WebSocketEventHandler) {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, new Set())
    }
    this.handlers.get(eventType)!.add(handler)
  }

  off(eventType: WebSocketEventType, handler: WebSocketEventHandler) {
    const handlers = this.handlers.get(eventType)
    if (handlers) {
      handlers.delete(handler)
    }
  }

  private handleEvent(event: WebSocketEvent) {
    const handlers = this.handlers.get(event.type)
    if (handlers) {
      handlers.forEach((handler) => handler(event))
    }
    // 也触发通配符处理器
    const allHandlers = this.handlers.get('*' as WebSocketEventType)
    if (allHandlers) {
      allHandlers.forEach((handler) => handler(event))
    }
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

export function createGameWebSocket(gameId: string): GameWebSocket {
  return new GameWebSocket(gameId)
}
