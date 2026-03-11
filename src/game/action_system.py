"""
动作系统 - 定义玩家可以执行的动作
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import logging
import random

from .vision_system import EventType, GameEvent

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """动作类型"""
    # 移动相关
    MOVE = "move"                   # 移动到相邻房间
    VENT_MOVE = "vent_move"         # 通过通风管移动（鸭子专用）

    # 任务相关
    DO_TASK = "do_task"             # 做任务（鹅专用）

    # 杀人相关
    KILL = "kill"                   # 杀人（鸭子专用）

    # 会议相关
    REPORT_BODY = "report_body"     # 报告尸体
    CALL_MEETING = "call_meeting"   # 召开紧急会议

    # 投票相关
    VOTE = "vote"                   # 投票


@dataclass
class GameAction:
    """游戏动作"""
    action_type: ActionType
    agent_id: str
    target_id: Optional[str] = None     # 目标 agent（如被杀者、被投票者）
    room_id: Optional[str] = None       # 相关房间
    task_id: Optional[str] = None       # 相关任务
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "action_type": self.action_type.value,
            "agent_id": self.agent_id,
            "target_id": self.target_id,
            "room_id": self.room_id,
            "task_id": self.task_id,
            "metadata": self.metadata
        }


class ActionValidator:
    """
    动作验证器 - 检查动作是否合法
    """

    def __init__(self, game_map, vision_system, game_state):
        """
        初始化验证器

        Args:
            game_map: GameMap 实例
            vision_system: VisionSystem 实例
            game_state: GameState 实例
        """
        self.game_map = game_map
        self.vision_system = vision_system
        self.game_state = game_state

    def validate(self, action: GameAction, agent) -> tuple:
        """
        验证动作是否合法

        Args:
            action: 游戏动作
            agent: 执行动作的 Agent

        Returns:
            (is_valid, error_message)
        """
        # 检查 Agent 是否存活
        if not agent.is_alive:
            return False, "你已死亡，无法执行动作"

        # 根据动作类型验证
        validators = {
            ActionType.MOVE: self._validate_move,
            ActionType.VENT_MOVE: self._validate_vent_move,
            ActionType.DO_TASK: self._validate_do_task,
            ActionType.KILL: self._validate_kill,
            ActionType.REPORT_BODY: self._validate_report_body,
            ActionType.CALL_MEETING: self._validate_call_meeting,
            ActionType.VOTE: self._validate_vote,
        }

        validator = validators.get(action.action_type)
        if validator:
            return validator(action, agent)

        return False, "未知动作类型"

    def _validate_move(self, action: GameAction, agent) -> tuple:
        """验证移动动作"""
        pos = self.vision_system.get_agent_position(action.agent_id)
        if not pos:
            return False, "找不到你的位置"

        to_room = action.room_id
        if not to_room:
            return False, "未指定目标房间"

        if not self.game_map.can_move_to(pos.room_id, to_room, use_vent=False):
            return False, f"无法从 {self.game_map.get_room_name(pos.room_id)} 移动到 {self.game_map.get_room_name(to_room)}"

        return True, ""

    def _validate_vent_move(self, action: GameAction, agent) -> tuple:
        """验证通风管移动（鸭子专用）"""
        # 检查是否是鸭子
        if agent.role.camp.value != "鸭阵营":
            return False, "只有鸭子可以使用通风管"

        pos = self.vision_system.get_agent_position(action.agent_id)
        if not pos:
            return False, "找不到你的位置"

        to_room = action.room_id
        if not to_room:
            return False, "未指定目标房间"

        if not self.game_map.can_move_to(pos.room_id, to_room, use_vent=True):
            return False, f"无法通过通风管到达 {self.game_map.get_room_name(to_room)}"

        return True, ""

    def _validate_do_task(self, action: GameAction, agent) -> tuple:
        """验证做任务动作"""
        # 检查是否是鹅阵营
        if agent.role.camp.value != "鹅阵营":
            return False, "只有鹅可以做任务"

        pos = self.vision_system.get_agent_position(action.agent_id)
        if not pos:
            return False, "找不到你的位置"

        task_id = action.task_id
        if not task_id:
            return False, "未指定任务"

        task = self.game_map.tasks.get(task_id)
        if not task:
            return False, "任务不存在"

        if task.room_id != pos.room_id:
            return False, f"任务不在当前房间"

        if task.is_completed:
            return False, "任务已完成"

        return True, ""

    def _validate_kill(self, action: GameAction, agent) -> tuple:
        """验证杀人动作（鸭子专用）"""
        # 检查是否是鸭子
        if agent.role.camp.value != "鸭阵营":
            return False, "只有鸭子可以杀人"

        target_id = action.target_id
        if not target_id:
            return False, "未指定目标"

        # 检查目标是否存在且存活
        # 这里需要从外部获取 target agent 信息
        # 暂时返回 True
        return True, ""

    def _validate_report_body(self, action: GameAction, agent) -> tuple:
        """验证报告尸体动作"""
        pos = self.vision_system.get_agent_position(action.agent_id)
        if not pos:
            return False, "找不到你的位置"

        # 检查当前房间是否有尸体
        unreported = self.vision_system.get_unreported_bodies()
        bodies_in_room = [e for e in unreported if e.room_id == pos.room_id]

        if not bodies_in_room:
            return False, "当前房间没有可报告的尸体"

        return True, ""

    def _validate_call_meeting(self, action: GameAction, agent) -> tuple:
        """验证召开紧急会议动作"""
        pos = self.vision_system.get_agent_position(action.agent_id)
        if not pos:
            return False, "找不到你的位置"

        room = self.game_map.get_room_by_id(pos.room_id)
        if not room or not room.has_emergency_button:
            return False, "当前房间没有紧急会议按钮"

        # 检查会议次数限制（如果有）
        meetings_called = self.game_state.events.get("meetings_called", 0)
        max_meetings = self.game_state.config.get("max_emergency_meetings", 1)

        if meetings_called >= max_meetings:
            return False, "紧急会议次数已用完"

        return True, ""

    def _validate_vote(self, action: GameAction, agent) -> tuple:
        """验证投票动作"""
        # 检查是否在投票阶段
        if self.game_state.phase.value != "voting":
            return False, "当前不是投票阶段"

        target_id = action.target_id
        if not target_id:
            return False, "未指定投票目标"

        return True, ""


class ActionExecutor:
    """
    动作执行器 - 执行游戏动作
    """

    def __init__(self, game_map, vision_system, game_state, event_callback=None):
        """
        初始化执行器

        Args:
            game_map: GameMap 实例
            vision_system: VisionSystem 实例
            game_state: GameState 实例
            event_callback: 事件回调函数（用于广播）
        """
        self.game_map = game_map
        self.vision_system = vision_system
        self.game_state = game_state
        self.event_callback = event_callback
        self.validator = ActionValidator(game_map, vision_system, game_state)

    def execute(self, action: GameAction, agent) -> tuple:
        """
        执行动作

        Args:
            action: 游戏动作
            agent: 执行动作的 Agent

        Returns:
            (success, message, result_data)
        """
        # 验证动作
        is_valid, error = self.validator.validate(action, agent)
        if not is_valid:
            return False, error, {}

        # 执行动作
        executors = {
            ActionType.MOVE: self._execute_move,
            ActionType.VENT_MOVE: self._execute_vent_move,
            ActionType.DO_TASK: self._execute_do_task,
            ActionType.KILL: self._execute_kill,
            ActionType.REPORT_BODY: self._execute_report_body,
            ActionType.CALL_MEETING: self._execute_call_meeting,
            ActionType.VOTE: self._execute_vote,
        }

        executor = executors.get(action.action_type)
        if executor:
            return executor(action, agent)

        return False, "未知动作类型", {}

    def _execute_move(self, action: GameAction, agent) -> tuple:
        """执行移动"""
        success = self.vision_system.move_agent(
            action.agent_id,
            action.room_id,
            use_vent=False
        )

        if success:
            room_name = self.game_map.get_room_name(action.room_id)
            return True, f"移动到 {room_name}", {"room_id": action.room_id}

        return False, "移动失败", {}

    def _execute_vent_move(self, action: GameAction, agent) -> tuple:
        """执行通风管移动"""
        success = self.vision_system.move_agent(
            action.agent_id,
            action.room_id,
            use_vent=True
        )

        if success:
            room_name = self.game_map.get_room_name(action.room_id)
            return True, f"通过通风管移动到 {room_name}", {"room_id": action.room_id}

        return False, "通风管移动失败", {}

    def _execute_do_task(self, action: GameAction, agent) -> tuple:
        """执行做任务"""
        task_id = action.task_id
        success = self.game_map.complete_task(task_id, action.agent_id)

        if success:
            task = self.game_map.tasks[task_id]
            # 记录事件
            event = self.vision_system.record_task(
                action.agent_id,
                task_id,
                task.room_id
            )

            # 检查任务进度
            completed, total = self.game_map.get_total_task_progress()

            return True, f"完成任务: {task.name}", {
                "task_id": task_id,
                "progress": (completed, total)
            }

        return False, "任务执行失败", {}

    def _execute_kill(self, action: GameAction, agent, target_agent=None) -> tuple:
        """执行杀人"""
        target_id = action.target_id
        pos = self.vision_system.get_agent_position(action.agent_id)

        if not pos:
            return False, "找不到你的位置", {}

        # 记录杀人事件
        event = self.vision_system.record_kill(
            action.agent_id,
            target_id,
            pos.room_id
        )

        # 更新游戏状态
        self.game_state.record_event({
            "type": "kill",
            "killer": action.agent_id,
            "victim": target_id,
            "room": pos.room_id,
            "witnesses": event.witnesses,
            "round": self.vision_system.current_round
        })

        room_name = self.game_map.get_room_name(pos.room_id)

        # 通知回调
        if self.event_callback:
            self.event_callback("player_killed", {
                "killer": agent.name,
                "victim": target_id,
                "room": room_name,
                "witnesses": event.witnesses
            })

        return True, f"你杀死了目标", {
            "room_id": pos.room_id,
            "witnesses": event.witnesses
        }

    def _execute_report_body(self, action: GameAction, agent) -> tuple:
        """执行报告尸体"""
        pos = self.vision_system.get_agent_position(action.agent_id)
        unreported = self.vision_system.get_unreported_bodies()
        bodies_in_room = [e for e in unreported if e.room_id == pos.room_id]

        if bodies_in_room:
            body = bodies_in_room[0]

            # 记录报告事件
            report_event = GameEvent(
                event_type=EventType.REPORT,
                room_id=pos.room_id,
                source_agent=action.agent_id,
                target_agent=body.target_agent,
                round_num=self.vision_system.current_round,
                metadata={"kill_room": body.room_id}
            )
            self.vision_system._record_event(report_event)

            room_name = self.game_map.get_room_name(pos.room_id)

            return True, f"发现了尸体！", {
                "body_found": body.target_agent,
                "room": room_name,
                "trigger_meeting": True
            }

        return False, "没有发现尸体", {}

    def _execute_call_meeting(self, action: GameAction, agent) -> tuple:
        """执行召开紧急会议"""
        # 记录会议次数
        meetings = self.game_state.events.get("meetings_called", 0)
        self.game_state.events["meetings_called"] = meetings + 1

        return True, "召开紧急会议！", {
            "trigger_meeting": True,
            "meeting_type": "emergency"
        }

    def _execute_vote(self, action: GameAction, agent) -> tuple:
        """执行投票"""
        target_id = action.target_id
        self.game_state.add_vote(action.agent_id, target_id)

        return True, "投票成功", {
            "voter": action.agent_id,
            "voted": target_id
        }


__all__ = [
    'ActionType', 'GameAction',
    'ActionValidator', 'ActionExecutor'
]
