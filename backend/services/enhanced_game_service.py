"""
增强版游戏服务 - 封装 EnhancedGameEngine，支持完整游戏循环
"""
import asyncio
import logging
import uuid
from typing import Dict, List, Any, Optional
from pathlib import Path

import sys
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.game.enhanced_game_engine import EnhancedGameEngine
from src.game.game_state import GamePhase, GameResult
from .event_manager import event_manager

logger = logging.getLogger(__name__)


class EnhancedGameService:
    """
    增强版游戏服务 - 封装 EnhancedGameEngine，提供完整的鹅鸭杀游戏
    """

    _instances: Dict[str, 'EnhancedGameService'] = {}

    def __init__(self, game_id: str, config: Optional[Dict[str, Any]] = None):
        self.game_id = game_id
        self.engine = EnhancedGameEngine(config)
        self._is_running = False
        self._is_paused = False
        self._task: Optional[asyncio.Task] = None
        self._delay_seconds = 1.0

        # 游戏事件缓存
        self._events: List[Dict[str, Any]] = []

    @classmethod
    def create_game(
        cls,
        player_names: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None,
        use_enhanced: bool = True
    ) -> 'EnhancedGameService':
        """创建新游戏"""
        game_id = str(uuid.uuid4())[:8]
        instance = cls(game_id, config)
        cls._instances[game_id] = instance

        # 设置游戏
        instance.engine.setup_game(player_names)

        logger.info(f"创建增强版游戏: {game_id}")
        return instance

    @classmethod
    def get_game(cls, game_id: str) -> Optional['EnhancedGameService']:
        """获取游戏实例"""
        return cls._instances.get(game_id)

    @classmethod
    def list_games(cls) -> List[str]:
        """列出所有游戏 ID"""
        return list(cls._instances.keys())

    @classmethod
    def remove_game(cls, game_id: str):
        """移除游戏实例"""
        if game_id in cls._instances:
            del cls._instances[game_id]
            event_manager.clear_history(game_id)

    async def start_game(self, delay_seconds: float = 1.0):
        """异步启动游戏"""
        if self._is_running:
            return

        self._is_running = True
        self._is_paused = False
        self._delay_seconds = delay_seconds

        # 设置事件回调
        self.engine.set_event_callback(self._broadcast_event)

        # 启动游戏任务
        self._task = asyncio.create_task(self._run_game_loop())

        logger.info(f"增强版游戏启动: {self.game_id}")

    async def _broadcast_event(self, event_type: str, data: Dict[str, Any]):
        """广播事件到前端"""
        # 缓存事件
        event_data = {
            "type": event_type,
            **data,
            "timestamp": asyncio.get_event_loop().time()
        }
        self._events.append(event_data)

        # 通过 event_manager 广播
        await event_manager.broadcast(self.game_id, event_type, data)

        # 添加延迟以便前端渲染
        await asyncio.sleep(self._delay_seconds * 0.5)

    async def _run_game_loop(self):
        """运行游戏主循环"""
        try:
            result = await self.engine.run_game_async()
            logger.info(f"游戏结束: {self.game_id}, 结果: {result.value}")
        except asyncio.CancelledError:
            logger.info(f"游戏任务被取消: {self.game_id}")
        except Exception as e:
            logger.error(f"游戏运行错误: {e}", exc_info=True)
            await self._broadcast_event("error", {"message": str(e)})
        finally:
            self._is_running = False

    async def pause_game(self):
        """暂停游戏"""
        self._is_paused = True
        logger.info(f"游戏暂停: {self.game_id}")

    async def resume_game(self):
        """恢复游戏"""
        self._is_paused = False
        logger.info(f"游戏恢复: {self.game_id}")

    def get_state(self, reveal_roles: bool = False) -> Dict[str, Any]:
        """获取当前游戏状态"""
        state = self.engine.get_state()
        state["game_id"] = self.game_id
        state["events"] = self._events[-50:]  # 最近50个事件

        if reveal_roles or self.engine.game_state.result != GameResult.ONGOING:
            state["players"] = self._get_players_info(reveal_roles=True)
        else:
            state["players"] = self._get_players_info(reveal_roles=False)

        return state

    def get_summary(self) -> Dict[str, Any]:
        """获取游戏总结"""
        return self.engine.get_game_summary()

    def _get_players_info(self, reveal_roles: bool = False) -> List[Dict[str, Any]]:
        """获取玩家信息"""
        players = []
        for agent_id, agent in self.engine.agents.items():
            info = {
                "agent_id": agent_id,
                "name": agent.name,
                "is_alive": agent.is_alive,
            }

            # 获取位置信息
            pos = self.engine.vision_system.get_agent_position(agent_id)
            if pos:
                room = self.engine.game_map.get_room_by_id(pos.room_id)
                info["room"] = room.name if room else pos.room_id
                info["room_id"] = pos.room_id

            if reveal_roles or self.engine.game_state.result != GameResult.ONGOING:
                info["role"] = agent.role.name
                info["camp"] = agent.role.camp.value

            players.append(info)

        return players

    def get_map_info(self) -> Dict[str, Any]:
        """获取地图信息（用于前端可视化）"""
        rooms = {}
        for room_id, room in self.engine.game_map.rooms.items():
            rooms[room_id] = {
                "id": room_id,
                "name": room.name,
                "type": room.room_type.value,
                "has_vent": room.has_vent,
                "has_emergency_button": room.has_emergency_button,
                "connected_rooms": room.connected_rooms,
                "tasks": [
                    {"id": t.task_id, "name": t.name, "completed": t.is_completed}
                    for t in room.tasks
                ]
            }

        # 任务进度
        completed, total = self.engine.game_map.get_total_task_progress()

        return {
            "rooms": rooms,
            "task_progress": {
                "completed": completed,
                "total": total,
                "percentage": round(completed / total * 100, 1) if total > 0 else 0
            }
        }

    def get_player_positions(self) -> Dict[str, Any]:
        """获取所有玩家位置（用于前端地图显示）"""
        positions = {}
        for agent_id in self.engine.agents:
            pos = self.engine.vision_system.get_agent_position(agent_id)
            if pos:
                agent = self.engine.agents[agent_id]
                positions[agent_id] = {
                    "name": agent.name,
                    "room_id": pos.room_id,
                    "is_alive": pos.is_alive,
                    "is_ghost": pos.is_ghost
                }
        return positions
