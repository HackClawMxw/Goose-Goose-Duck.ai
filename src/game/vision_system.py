"""
视野系统 - 管理玩家目击和可见性
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum
import logging
import time

logger = logging.getLogger(__name__)


class EventType(Enum):
    """事件类型"""
    KILL = "kill"               # 杀人
    TASK = "task"               # 做任务
    VENT_ENTER = "vent_enter"   # 进入通风管
    VENT_EXIT = "vent_exit"     # 离开通风管
    REPORT = "report"           # 报告尸体
    MEETING = "meeting"         # 紧急会议


@dataclass
class GameEvent:
    """游戏事件"""
    event_type: EventType
    room_id: str
    source_agent: str           # 事件发起者
    target_agent: Optional[str] = None  # 事件目标（如被杀者）
    timestamp: float = field(default_factory=time.time)
    round_num: int = 1
    witnesses: List[str] = field(default_factory=list)  # 目击者列表
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type.value,
            "room_id": self.room_id,
            "source_agent": self.source_agent,
            "target_agent": self.target_agent,
            "timestamp": self.timestamp,
            "round_num": self.round_num,
            "witnesses": self.witnesses,
            "metadata": self.metadata
        }


@dataclass
class AgentPosition:
    """Agent位置信息"""
    agent_id: str
    room_id: str
    is_alive: bool = True
    is_ghost: bool = False      # 是否是幽灵（死后可以看全图）
    last_move_time: float = 0
    current_action: Optional[str] = None  # 当前正在做的动作


class VisionSystem:
    """
    视野系统 - 管理可见性和目击
    """

    def __init__(self, game_map):
        """
        初始化视野系统

        Args:
            game_map: GameMap 实例
        """
        self.game_map = game_map
        self.positions: Dict[str, AgentPosition] = {}
        self.event_history: List[GameEvent] = []
        self.current_round = 1

        # 可见性配置
        self.visibility_range = 1  # 可见范围（房间数，目前只支持同房间）
        self.ghost_can_see_all = True  # 幽灵是否可以看全图

        logger.info("视野系统初始化完成")

    def initialize_agent(self, agent_id: str, spawn_room: str):
        """初始化Agent位置"""
        self.positions[agent_id] = AgentPosition(
            agent_id=agent_id,
            room_id=spawn_room,
            is_alive=True,
            is_ghost=False,
            last_move_time=time.time()
        )
        logger.debug(f"Agent {agent_id} 初始化在 {spawn_room}")

    def move_agent(self, agent_id: str, to_room: str, use_vent: bool = False) -> bool:
        """
        移动Agent到新房间

        Args:
            agent_id: Agent ID
            to_room: 目标房间
            use_vent: 是否使用通风管

        Returns:
            是否成功移动
        """
        if agent_id not in self.positions:
            logger.warning(f"Agent {agent_id} 不存在于位置系统中")
            return False

        pos = self.positions[agent_id]
        if not pos.is_alive:
            logger.debug(f"Agent {agent_id} 已死亡，无法移动")
            return False

        from_room = pos.room_id

        # 检查是否可以移动
        if not self.game_map.can_move_to(from_room, to_room, use_vent):
            logger.warning(f"无法从 {from_room} 移动到 {to_room}")
            return False

        # 记录通风管事件
        if use_vent:
            event = GameEvent(
                event_type=EventType.VENT_ENTER,
                room_id=from_room,
                source_agent=agent_id,
                round_num=self.current_round
            )
            self._record_event(event)

        # 更新位置
        pos.room_id = to_room
        pos.last_move_time = time.time()
        pos.current_action = None

        logger.info(f"Agent {agent_id} 移动到 {to_room}")
        return True

    def get_agent_position(self, agent_id: str) -> Optional[AgentPosition]:
        """获取Agent位置"""
        return self.positions.get(agent_id)

    def get_agents_in_room(self, room_id: str, exclude_dead: bool = True) -> List[str]:
        """
        获取房间内的所有Agent

        Args:
            room_id: 房间ID
            exclude_dead: 是否排除死者

        Returns:
            Agent ID 列表
        """
        agents = []
        for agent_id, pos in self.positions.items():
            if pos.room_id == room_id:
                if exclude_dead and not pos.is_alive:
                    continue
                agents.append(agent_id)
        return agents

    def get_visible_agents(self, observer_id: str) -> List[str]:
        """
        获取观察者可见的所有Agent

        Args:
            observer_id: 观察者ID

        Returns:
            可见的Agent ID列表
        """
        if observer_id not in self.positions:
            return []

        pos = self.positions[observer_id]

        # 幽灵可以看到所有人
        if pos.is_ghost and self.ghost_can_see_all:
            return [aid for aid, p in self.positions.items() if aid != observer_id]

        # 活人只能看到同房间的人
        visible = []
        for agent_id, other_pos in self.positions.items():
            if agent_id == observer_id:
                continue
            if other_pos.room_id == pos.room_id and other_pos.is_alive:
                visible.append(agent_id)

        return visible

    def record_kill(self, killer_id: str, victim_id: str, room_id: str) -> GameEvent:
        """
        记录杀人事件

        Args:
            killer_id: 杀手ID
            victim_id: 受害者ID
            room_id: 发生房间

        Returns:
            杀人事件
        """
        # 找出目击者（同房间的其他活人）
        witnesses = []
        for agent_id in self.get_agents_in_room(room_id, exclude_dead=True):
            if agent_id != killer_id and agent_id != victim_id:
                witnesses.append(agent_id)

        event = GameEvent(
            event_type=EventType.KILL,
            room_id=room_id,
            source_agent=killer_id,
            target_agent=victim_id,
            round_num=self.current_round,
            witnesses=witnesses
        )

        self._record_event(event)

        # 更新受害者状态
        if victim_id in self.positions:
            self.positions[victim_id].is_alive = False
            self.positions[victim_id].is_ghost = True

        logger.info(f"杀人事件: {killer_id} 杀了 {victim_id} 在 {room_id}, 目击者: {witnesses}")

        return event

    def record_task(self, agent_id: str, task_id: str, room_id: str) -> GameEvent:
        """
        记录做任务事件

        Args:
            agent_id: Agent ID
            task_id: 任务ID
            room_id: 房间ID

        Returns:
            任务事件
        """
        # 找出目击者
        witnesses = []
        for other_id in self.get_agents_in_room(room_id, exclude_dead=True):
            if other_id != agent_id:
                witnesses.append(other_id)

        event = GameEvent(
            event_type=EventType.TASK,
            room_id=room_id,
            source_agent=agent_id,
            round_num=self.current_round,
            witnesses=witnesses,
            metadata={"task_id": task_id}
        )

        self._record_event(event)
        return event

    def _record_event(self, event: GameEvent):
        """记录事件到历史"""
        self.event_history.append(event)

    def get_events_for_agent(self, agent_id: str, event_type: Optional[EventType] = None) -> List[GameEvent]:
        """
        获取Agent可见的事件

        Args:
            agent_id: Agent ID
            event_type: 可选的事件类型过滤

        Returns:
            事件列表
        """
        pos = self.positions.get(agent_id)
        if not pos:
            return []

        events = []
        for event in self.event_history:
            # 幽灵可以看到所有事件
            if pos.is_ghost and self.ghost_can_see_all:
                events.append(event)
                continue

            # 活人只能看到自己目击的事件
            if agent_id in event.witnesses:
                events.append(event)
            elif event.source_agent == agent_id:
                events.append(event)
            elif event.target_agent == agent_id:
                events.append(event)

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        return events

    def get_kill_events(self) -> List[GameEvent]:
        """获取所有杀人事件"""
        return [e for e in self.event_history if e.event_type == EventType.KILL]

    def get_unreported_bodies(self) -> List[GameEvent]:
        """获取未报告的尸体（杀人事件）"""
        unreported = []
        reported_rooms = set()

        for event in reversed(self.event_history):
            if event.event_type == EventType.REPORT:
                reported_rooms.add(event.metadata.get("kill_room", ""))
            elif event.event_type == EventType.KILL:
                if event.room_id not in reported_rooms:
                    unreported.append(event)

        return unreported

    def set_agent_dead(self, agent_id: str):
        """设置Agent死亡"""
        if agent_id in self.positions:
            self.positions[agent_id].is_alive = False
            self.positions[agent_id].is_ghost = True
            logger.info(f"Agent {agent_id} 已死亡")

    def revive_agent(self, agent_id: str):
        """复活Agent（用于测试）"""
        if agent_id in self.positions:
            self.positions[agent_id].is_alive = True
            self.positions[agent_id].is_ghost = False

    def new_round(self):
        """开始新回合"""
        self.current_round += 1
        logger.info(f"进入第 {self.current_round} 回合")

    def get_room_info_for_agent(self, agent_id: str) -> dict:
        """
        获取Agent所在房间的信息

        Returns:
            房间信息字典
        """
        pos = self.positions.get(agent_id)
        if not pos:
            return {}

        room = self.game_map.get_room_by_id(pos.room_id)
        if not room:
            return {}

        # 获取房间内的其他玩家
        other_agents = []
        for other_id in self.get_agents_in_room(pos.room_id, exclude_dead=True):
            if other_id != agent_id:
                other_agents.append(other_id)

        return {
            "room_id": pos.room_id,
            "room_name": room.name,
            "connected_rooms": room.connected_rooms,
            "has_vent": room.has_vent,
            "has_emergency_button": room.has_emergency_button,
            "tasks": [t.to_dict() for t in room.tasks],
            "other_agents": other_agents,
            "can_use_vent": room.has_vent and pos.room_id in self.game_map.vents
        }

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "positions": {
                aid: {
                    "room_id": pos.room_id,
                    "is_alive": pos.is_alive,
                    "is_ghost": pos.is_ghost,
                    "current_action": pos.current_action
                }
                for aid, pos in self.positions.items()
            },
            "event_count": len(self.event_history),
            "current_round": self.current_round
        }
