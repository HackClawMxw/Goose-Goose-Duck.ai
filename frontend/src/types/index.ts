/**
 * 类型定义
 */

export interface PlayerInfo {
  agent_id: string
  name: string
  role?: string
  camp?: string
  is_alive: boolean
}

export interface Dialogue {
  speaker: string
  content: string
  phase: string
  round: number
  timestamp?: number
}

export interface GameState {
  game_id: string
  phase: string
  round_num: number
  result: string
  players: PlayerInfo[]
  current_dialogues: Dialogue[]
  votes: Record<string, string>
}

export interface GameStateResponse extends GameState {}

export interface GameCreatedResponse {
  game_id: string
  status: string
  players: PlayerInfo[]
  message: string
}

export interface GameSummaryResponse {
  result: string
  rounds: number
  players: Array<{
    name: string
    role: string
    camp: string
    status: string
  }>
  history: Array<Record<string, unknown>>
}
