"""
请求模型
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CreateGameRequest(BaseModel):
    """创建游戏请求"""
    player_names: Optional[List[str]] = Field(
        default=None,
        description="玩家名称列表（可选，默认自动生成）"
    )
    config_override: Optional[Dict[str, Any]] = Field(
        default=None,
        description="配置覆盖（可选）"
    )


class StartGameRequest(BaseModel):
    """开始游戏请求"""
    auto_play: bool = Field(
        default=True,
        description="是否自动进行游戏"
    )
    step_by_step: bool = Field(
        default=False,
        description="是否逐步执行（用于调试）"
    )
    delay_seconds: float = Field(
        default=1.0,
        description="事件之间的延迟秒数（用于观看）"
    )


class WebSocketSubscribe(BaseModel):
    """WebSocket 订阅请求"""
    type: str = Field(default="subscribe", description="消息类型")
    game_id: str = Field(..., description="要订阅的游戏 ID")
