"""
响应模型
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class PlayerInfo(BaseModel):
    """玩家信息"""
    agent_id: str = Field(..., description="Agent ID")
    name: str = Field(..., description="玩家名称")
    role: Optional[str] = Field(default=None, description="角色名称（游戏中可能隐藏）")
    camp: Optional[str] = Field(default=None, description="阵营（游戏中可能隐藏）")
    is_alive: bool = Field(default=True, description="是否存活")


class GameStateResponse(BaseModel):
    """游戏状态响应"""
    game_id: str = Field(..., description="游戏 ID")
    phase: str = Field(..., description="当前阶段")
    round_num: int = Field(default=1, description="当前轮次")
    result: str = Field(default="游戏进行中", description="游戏结果")
    players: List[PlayerInfo] = Field(default_factory=list, description="玩家列表")
    current_dialogues: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="当前对话记录"
    )
    votes: Dict[str, str] = Field(default_factory=dict, description="投票记录")


class GameCreatedResponse(BaseModel):
    """游戏创建响应"""
    game_id: str = Field(..., description="游戏 ID")
    status: str = Field(default="created", description="游戏状态")
    players: List[PlayerInfo] = Field(default_factory=list, description="玩家列表")
    message: str = Field(default="游戏创建成功", description="消息")


class GameSummaryResponse(BaseModel):
    """游戏总结响应"""
    result: str = Field(..., description="游戏结果")
    rounds: int = Field(..., description="总轮次")
    players: List[Dict[str, Any]] = Field(default_factory=list, description="玩家信息")
    history: List[Dict[str, Any]] = Field(default_factory=list, description="游戏历史")


class WebSocketEventType(str, Enum):
    """WebSocket 事件类型"""
    # 游戏生命周期
    GAME_STARTED = "game_started"
    PHASE_CHANGED = "phase_changed"
    GAME_OVER = "game_over"

    # 玩家行为
    DIALOGUE = "dialogue"
    VOTE_CAST = "vote_cast"
    PLAYER_DIED = "player_died"

    # 系统事件
    ERROR = "error"
    PING = "ping"
    PONG = "pong"


class WebSocketEvent(BaseModel):
    """WebSocket 事件"""
    type: str = Field(..., description="事件类型")
    timestamp: float = Field(..., description="时间戳")

    # 根据事件类型，以下字段可能为空
    game_id: Optional[str] = Field(default=None, description="游戏 ID")
    phase: Optional[str] = Field(default=None, description="当前阶段")
    round: Optional[int] = Field(default=None, description="当前轮次")

    # 对话事件
    speaker: Optional[str] = Field(default=None, description="发言者")
    content: Optional[str] = Field(default=None, description="内容")

    # 投票事件
    voter: Optional[str] = Field(default=None, description="投票者")
    voted: Optional[str] = Field(default=None, description="被投票者")

    # 死亡事件
    player_name: Optional[str] = Field(default=None, description="玩家名称")
    role: Optional[str] = Field(default=None, description="角色")

    # 游戏结束
    result: Optional[str] = Field(default=None, description="游戏结果")
    summary: Optional[Dict[str, Any]] = Field(default=None, description="游戏总结")

    # 错误
    message: Optional[str] = Field(default=None, description="消息")
