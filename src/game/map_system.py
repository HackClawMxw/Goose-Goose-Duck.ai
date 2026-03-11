"""
地图系统 - 定义游戏地图、房间和移动
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum
import random
import logging

logger = logging.getLogger(__name__)


class RoomType(Enum):
    """房间类型"""
    NORMAL = "normal"       # 普通房间
    SPAWN = "spawn"         # 出生点
    EMERGENCY = "emergency" # 紧急会议按钮位置
    TASK = "task"           # 任务房间
    VENT = "vent"           # 有通风管的房间（鸭子专用）


@dataclass
class Task:
    """任务"""
    task_id: str
    name: str
    room_id: str
    description: str = ""
    required_time: float = 3.0  # 完成所需秒数
    is_completed: bool = False
    completed_by: Optional[str] = None  # 完成者 agent_id

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "room_id": self.room_id,
            "description": self.description,
            "required_time": self.required_time,
            "is_completed": self.is_completed,
            "completed_by": self.completed_by
        }


@dataclass
class Room:
    """房间"""
    room_id: str
    name: str
    description: str = ""
    room_type: RoomType = RoomType.NORMAL
    tasks: List[Task] = field(default_factory=list)
    connected_rooms: List[str] = field(default_factory=list)
    has_vent: bool = False  # 是否有通风管（鸭子专用）
    has_emergency_button: bool = False  # 是否有紧急会议按钮

    def to_dict(self) -> dict:
        return {
            "room_id": self.room_id,
            "name": self.name,
            "description": self.description,
            "room_type": self.room_type.value,
            "tasks": [t.to_dict() for t in self.tasks],
            "connected_rooms": self.connected_rooms,
            "has_vent": self.has_vent,
            "has_emergency_button": self.has_emergency_button
        }


class GameMap:
    """
    游戏地图 - 管理房间、任务和移动
    """

    # 默认地图配置（太空飞船主题）
    DEFAULT_MAP_CONFIG = {
        "name": "太空飞船",
        "rooms": [
            {"id": "cafeteria", "name": "餐厅", "type": "spawn", "emergency": True},
            {"id": "weapons", "name": "武器室", "type": "task"},
            {"id": "navigation", "name": "导航室", "type": "task"},
            {"id": "o2", "name": "氧气室", "type": "task"},
            {"id": "shields", "name": "护盾室", "type": "task"},
            {"id": "communications", "name": "通讯室", "type": "task"},
            {"id": "storage", "name": "储藏室", "type": "task"},
            {"id": "electrical", "name": "电力室", "type": "task", "vent": True},
            {"id": "lower_engine", "name": "下引擎", "type": "task", "vent": True},
            {"id": "security", "name": "监控室", "type": "task"},
            {"id": "reactor", "name": "反应堆", "type": "task", "vent": True},
            {"id": "upper_engine", "name": "上引擎", "type": "task"},
            {"id": "medbay", "name": "医疗室", "type": "task"},
            {"id": "admin", "name": "管理室", "type": "task", "vent": True},
        ],
        "connections": {
            "cafeteria": ["weapons", "navigation", "o2", "medbay", "upper_engine", "storage"],
            "weapons": ["cafeteria", "navigation", "shields"],
            "navigation": ["cafeteria", "weapons", "o2", "shields"],
            "o2": ["cafeteria", "navigation", "shields"],
            "shields": ["weapons", "navigation", "o2", "communications", "storage"],
            "communications": ["shields", "storage"],
            "storage": ["cafeteria", "shields", "communications", "electrical", "admin", "lower_engine"],
            "electrical": ["storage", "lower_engine", "security"],
            "lower_engine": ["storage", "electrical", "security", "reactor"],
            "security": ["electrical", "lower_engine", "reactor", "upper_engine"],
            "reactor": ["lower_engine", "security", "upper_engine"],
            "upper_engine": ["cafeteria", "security", "reactor", "medbay"],
            "medbay": ["cafeteria", "upper_engine", "admin"],
            "admin": ["cafeteria", "medbay", "storage"],
        },
        "tasks": [
            {"id": "task_weapons_1", "name": "校准武器", "room": "weapons"},
            {"id": "task_navigation_1", "name": "设定航线", "room": "navigation"},
            {"id": "task_o2_1", "name": "清理过滤器", "room": "o2"},
            {"id": "task_o2_2", "name": "启动氧气", "room": "o2"},
            {"id": "task_shields_1", "name": "启动护盾", "room": "shields"},
            {"id": "task_communications_1", "name": "修复通讯", "room": "communications"},
            {"id": "task_storage_1", "name": "整理物资", "room": "storage"},
            {"id": "task_storage_2", "name": "加油", "room": "storage"},
            {"id": "task_electrical_1", "name": "修复电路", "room": "electrical"},
            {"id": "task_electrical_2", "name": "下载上传数据", "room": "electrical"},
            {"id": "task_lower_engine_1", "name": "校准引擎", "room": "lower_engine"},
            {"id": "task_security_1", "name": "查看监控", "room": "security"},
            {"id": "task_reactor_1", "name": "启动反应堆", "room": "reactor"},
            {"id": "task_upper_engine_1", "name": "校准引擎", "room": "upper_engine"},
            {"id": "task_medbay_1", "name": "提交扫描", "room": "medbay"},
            {"id": "task_medbay_2", "name": "整理药品", "room": "medbay"},
            {"id": "task_admin_1", "name": "刷卡", "room": "admin"},
            {"id": "task_admin_2", "name": "查看监控日志", "room": "admin"},
        ],
        # 通风管连接（鸭子专用快速移动）
        "vents": {
            "electrical": ["lower_engine", "security"],
            "lower_engine": ["electrical", "security", "reactor"],
            "security": ["electrical", "lower_engine", "reactor"],
            "reactor": ["lower_engine", "security"],
            "admin": ["cafeteria", "medbay"],
            "medbay": ["admin", "electrical"],
        }
    }

    def __init__(self, config: Optional[dict] = None):
        """
        初始化地图

        Args:
            config: 地图配置，如果为None则使用默认配置
        """
        self.config = config or self.DEFAULT_MAP_CONFIG
        self.rooms: Dict[str, Room] = {}
        self.tasks: Dict[str, Task] = {}
        self.vents: Dict[str, List[str]] = {}

        self._build_map()

        logger.info(f"地图初始化完成: {self.config.get('name', '未知地图')}")
        logger.info(f"房间数量: {len(self.rooms)}, 任务数量: {len(self.tasks)}")

    def _build_map(self):
        """构建地图"""
        # 创建房间
        for room_data in self.config.get("rooms", []):
            room_type = RoomType(room_data.get("type", "normal"))
            room = Room(
                room_id=room_data["id"],
                name=room_data["name"],
                description=room_data.get("description", ""),
                room_type=room_type,
                has_vent=room_data.get("vent", False),
                has_emergency_button=room_data.get("emergency", False)
            )
            self.rooms[room.room_id] = room

        # 设置房间连接
        for room_id, connections in self.config.get("connections", {}).items():
            if room_id in self.rooms:
                self.rooms[room_id].connected_rooms = connections

        # 创建任务
        for task_data in self.config.get("tasks", []):
            task = Task(
                task_id=task_data["id"],
                name=task_data["name"],
                room_id=task_data["room"],
                description=task_data.get("description", ""),
                required_time=task_data.get("time", 3.0)
            )
            self.tasks[task.task_id] = task

            # 将任务添加到对应房间
            if task.room_id in self.rooms:
                self.rooms[task.room_id].tasks.append(task)

        # 设置通风管连接
        self.vents = self.config.get("vents", {})

    def get_spawn_room(self) -> str:
        """获取出生点房间ID"""
        for room_id, room in self.rooms.items():
            if room.room_type == RoomType.SPAWN:
                return room_id
        return list(self.rooms.keys())[0]  # 默认返回第一个房间

    def get_adjacent_rooms(self, room_id: str) -> List[str]:
        """获取相邻房间列表"""
        if room_id in self.rooms:
            return self.rooms[room_id].connected_rooms
        return []

    def get_vent_connections(self, room_id: str) -> List[str]:
        """获取通风管连接的房间（鸭子专用）"""
        return self.vents.get(room_id, [])

    def can_move_to(self, from_room: str, to_room: str, use_vent: bool = False) -> bool:
        """
        检查是否可以从一个房间移动到另一个房间

        Args:
            from_room: 起始房间
            to_room: 目标房间
            use_vent: 是否使用通风管（鸭子专用）

        Returns:
            是否可以移动
        """
        if from_room not in self.rooms or to_room not in self.rooms:
            return False

        if use_vent:
            return to_room in self.get_vent_connections(from_room)
        else:
            return to_room in self.get_adjacent_rooms(from_room)

    def get_room_tasks(self, room_id: str, include_completed: bool = False) -> List[Task]:
        """获取房间内的任务"""
        if room_id not in self.rooms:
            return []

        tasks = self.rooms[room_id].tasks
        if include_completed:
            return tasks
        return [t for t in tasks if not t.is_completed]

    def get_total_task_progress(self) -> tuple:
        """
        获取总体任务进度

        Returns:
            (已完成数量, 总数量)
        """
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks.values() if t.is_completed)
        return completed, total

    def get_incomplete_tasks(self) -> List[Task]:
        """获取所有未完成的任务"""
        return [t for t in self.tasks.values() if not t.is_completed]

    def complete_task(self, task_id: str, agent_id: str) -> bool:
        """
        完成任务

        Args:
            task_id: 任务ID
            agent_id: 完成者ID

        Returns:
            是否成功完成
        """
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        if task.is_completed:
            return False

        task.is_completed = True
        task.completed_by = agent_id
        logger.info(f"任务完成: {task.name} by {agent_id}")
        return True

    def get_random_incomplete_task(self) -> Optional[Task]:
        """随机获取一个未完成的任务"""
        incomplete = self.get_incomplete_tasks()
        if incomplete:
            return random.choice(incomplete)
        return None

    def get_room_by_id(self, room_id: str) -> Optional[Room]:
        """获取房间"""
        return self.rooms.get(room_id)

    def get_room_name(self, room_id: str) -> str:
        """获取房间名称"""
        room = self.get_room_by_id(room_id)
        return room.name if room else room_id

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "name": self.config.get("name", "未知地图"),
            "rooms": {rid: room.to_dict() for rid, room in self.rooms.items()},
            "tasks": {tid: task.to_dict() for tid, task in self.tasks.items()},
            "vents": self.vents,
            "task_progress": self.get_total_task_progress()
        }
