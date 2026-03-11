"""
事件广播管理器
"""
import json
import logging
import time
from typing import Dict, List, Any, Optional, Set
from fastapi import WebSocket
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class EventManager:
    """
    事件广播管理器
    负责管理 WebSocket 连接并广播游戏事件
    """

    def __init__(self):
        # game_id -> set of websocket connections
        self._connections: Dict[str, Set[WebSocket]] = {}
        # 事件历史记录（用于新连接的同步）
        self._event_history: Dict[str, List[Dict[str, Any]]] = {}

    async def subscribe(self, game_id: str, websocket: WebSocket):
        """
        订阅游戏事件

        Args:
            game_id: 游戏 ID
            websocket: WebSocket 连接
        """
        await websocket.accept()

        if game_id not in self._connections:
            self._connections[game_id] = set()

        self._connections[game_id].add(websocket)
        logger.info(f"WebSocket 订阅游戏: {game_id}, 当前连接数: {len(self._connections[game_id])}")

        # 发送历史事件（用于页面刷新后恢复状态）
        if game_id in self._event_history:
            for event in self._event_history[game_id]:
                try:
                    await websocket.send_text(json.dumps(event, ensure_ascii=False))
                except Exception as e:
                    logger.warning(f"发送历史事件失败: {e}")

    def unsubscribe(self, game_id: str, websocket: WebSocket):
        """
        取消订阅

        Args:
            game_id: 游戏 ID
            websocket: WebSocket 连接
        """
        if game_id in self._connections:
            self._connections[game_id].discard(websocket)
            logger.info(f"WebSocket 取消订阅游戏: {game_id}, 剩余连接数: {len(self._connections[game_id])}")

            # 如果没有连接了，清理资源
            if not self._connections[game_id]:
                del self._connections[game_id]
                # 保留历史记录一段时间（用于页面刷新）

    async def broadcast(self, game_id: str, event_type: str, data: Dict[str, Any],
                       store_history: bool = True):
        """
        广播事件到所有订阅者

        Args:
            game_id: 游戏 ID
            event_type: 事件类型
            data: 事件数据
            store_history: 是否存储到历史记录
        """
        message = {
            "type": event_type,
            "timestamp": time.time(),
            "game_id": game_id,
            **data
        }

        # 存储到历史记录
        if store_history:
            if game_id not in self._event_history:
                self._event_history[game_id] = []
            self._event_history[game_id].append(message)

            # 限制历史记录大小
            if len(self._event_history[game_id]) > 1000:
                self._event_history[game_id] = self._event_history[game_id][-500:]

        # 广播到所有连接
        if game_id in self._connections:
            dead_connections = []
            message_str = json.dumps(message, ensure_ascii=False)

            for websocket in self._connections[game_id]:
                try:
                    await websocket.send_text(message_str)
                except Exception as e:
                    logger.warning(f"广播事件失败: {e}")
                    dead_connections.append(websocket)

            # 清理断开的连接
            for ws in dead_connections:
                self._connections[game_id].discard(ws)

        logger.debug(f"广播事件: {event_type} -> {game_id}")

    def clear_history(self, game_id: str):
        """
        清除游戏历史记录

        Args:
            game_id: 游戏 ID
        """
        if game_id in self._event_history:
            del self._event_history[game_id]
        if game_id in self._connections:
            del self._connections[game_id]
        logger.info(f"清理游戏资源: {game_id}")

    def get_connection_count(self, game_id: str) -> int:
        """获取游戏连接数"""
        return len(self._connections.get(game_id, set()))


# 全局事件管理器实例
event_manager = EventManager()
