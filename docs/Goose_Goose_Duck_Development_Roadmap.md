# Goose-Goose-Duck.ai 开发路线建议

> 基于 MiroFish 项目架构经验，为 AI 鹅鸭杀项目提供后续开发指导

---

## 一、项目现状分析

### 1.1 已完成功能 (Phase 1: MiniMVP) ✅

```
┌─────────────────────────────────────────────────────────────┐
│                    当前项目架构                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  src/                                                        │
│  ├── agents/          # Agent系统 ✅                         │
│  │   ├── agent.py     # Agent核心类                          │
│  │   └── memory.py    # 短期记忆                             │
│  │                                                          │
│  ├── game/            # 游戏逻辑 ✅                           │
│  │   ├── game_engine.py    # 游戏引擎                        │
│  │   ├── game_state.py     # 状态管理                        │
│  │   ├── dialogue_manager.py # 对话管理                      │
│  │   └── information_isolation.py # 信息隔离                 │
│  │                                                          │
│  ├── llm/             # LLM接口 ✅                            │
│  │   └── factory.py   # 多模型支持                           │
│  │                                                          │
│  ├── roles/           # 角色系统 ✅                           │
│  │   └── role.py      # 角色/阵营定义                        │
│  │                                                          │
│  └── utils/           # 工具函数 ✅                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**核心能力**：
- ✅ 多Agent对话系统
- ✅ 信息隔离机制（鸭阵营互相认识）
- ✅ 角色扮演与身份隐藏
- ✅ 基础投票机制
- ✅ LLM多模型支持（GLM/OpenAI/DeepSeek）
- ✅ 短期记忆系统
- ✅ 游戏流程自动化

### 1.2 待开发功能

| 阶段 | 功能 | 优先级 | 复杂度 |
|-----|------|-------|-------|
| Phase 2 | 地图与移动系统 | 🔴 高 | ⭐⭐⭐ |
| Phase 2 | 视野与目击机制 | 🔴 高 | ⭐⭐⭐⭐ |
| Phase 2 | 完整游戏规则 | 🟡 中 | ⭐⭐⭐ |
| Phase 2 | 回合制调度 | 🟡 中 | ⭐⭐ |
| Phase 3 | 长期记忆 + RAG | 🟡 中 | ⭐⭐⭐⭐ |
| Phase 3 | 知识图谱 | 🟢 低 | ⭐⭐⭐⭐⭐ |
| Phase 3 | 可视化界面 | 🟡 中 | ⭐⭐⭐ |
| Phase 4 | 评测系统 | 🟢 低 | ⭐⭐⭐ |

---

## 二、MiroFish 可借鉴的核心设计

### 2.1 架构对比

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         架构对比分析                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  MiroFish                              Goose-Goose-Duck.ai                  │
│  (社交舆论模拟)                         (游戏推理模拟)                       │
│                                                                              │
│  ┌─────────────────┐                  ┌─────────────────┐                   │
│  │ 知识图谱层      │                  │ (待开发)        │                   │
│  │ Zep + GraphRAG  │  ─────────────>  │ 知识图谱        │                   │
│  └─────────────────┘                  └─────────────────┘                   │
│                                                                              │
│  ┌─────────────────┐                  ┌─────────────────┐                   │
│  │ Agent层         │                  │ Agent层 ✅      │                   │
│  │ Profile生成器   │  ─────────────>  │ 记忆+决策       │                   │
│  │ OASIS引擎       │                  │ 需增强          │                   │
│  └─────────────────┘                  └─────────────────┘                   │
│                                                                              │
│  ┌─────────────────┐                  ┌─────────────────┐                   │
│  │ 模拟层          │                  │ 游戏引擎 ✅     │                   │
│  │ SimulationMgr   │  ─────────────>  │ GameEngine      │                   │
│  │ IPC通信         │                  │ 需增加空间模拟  │                   │
│  └─────────────────┘                  └─────────────────┘                   │
│                                                                              │
│  ┌─────────────────┐                  ┌─────────────────┐                   │
│  │ 交互层          │                  │ (待开发)        │                   │
│  │ Report Agent    │  ─────────────>  │ 可视化界面      │                   │
│  │ Interview       │                  │ 人类玩家接入    │                   │
│  └─────────────────┘                  └─────────────────┘                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 可直接借鉴的设计模式

#### 2.2.1 记忆系统升级

**MiroFish 的多层记忆架构**：

```python
# 你当前的短期记忆
class Memory:
    messages: List[Dict]  # 简单的消息列表

# 建议升级为多层记忆
class EnhancedMemory:
    # Level 1: 工作记忆（当前轮次）
    working_memory: List[Dict]
    working_memory_limit: int = 10

    # Level 2: 情景记忆（游戏事件）
    episodic_memory: List[GameEvent]

    # Level 3: 推理记忆（身份推断）
    inference_memory: Dict[str, BeliefState]
    # 例如: {"agent_1": {"suspected_role": "鸭子", "confidence": 0.7}}

    # Level 4: 行为记忆（玩家行为模式）
    behavior_memory: Dict[str, List[Action]]
    # 例如: {"agent_2": [{"type": "accuse", "target": "agent_3", "round": 2}]}
```

**实现建议**：

```python
# src/agents/enhanced_memory.py

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum

class EventType(Enum):
    DISCUSSION = "discussion"
    VOTE = "vote"
    DEATH = "death"
    ACCUSATION = "accusation"
    DEFENSE = "defense"

@dataclass
class GameEvent:
    """游戏事件"""
    round_num: int
    event_type: EventType
    source_agent: str
    target_agent: Optional[str]
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BeliefState:
    """对某玩家的信念状态"""
    agent_id: str
    suspected_camp: str  # "goose" / "duck" / "neutral"
    confidence: float    # 0.0 - 1.0
    evidence: List[str]  # 支持证据
    updated_at: int      # 更新轮次

class EnhancedMemory:
    """增强记忆系统"""

    def __init__(self, max_working: int = 10):
        self.working_memory: List[Dict] = []
        self.episodic_memory: List[GameEvent] = []
        self.belief_states: Dict[str, BeliefState] = {}
        self.behavior_log: Dict[str, List[Dict]] = {}

    def observe_event(self, event: GameEvent):
        """观察并记录事件"""
        self.episodic_memory.append(event)

        # 更新行为日志
        target = event.target_agent or event.source_agent
        if target not in self.behavior_log:
            self.behavior_log[target] = []
        self.behavior_log[target].append({
            "type": event.event_type.value,
            "round": event.round_num,
            "content": event.content[:100]
        })

    def update_belief(self, agent_id: str, camp: str,
                      confidence: float, evidence: str):
        """更新对某玩家的信念"""
        if agent_id in self.belief_states:
            old = self.belief_states[agent_id]
            # 信念更新逻辑（可以更复杂）
            self.belief_states[agent_id] = BeliefState(
                agent_id=agent_id,
                suspected_camp=camp,
                confidence=max(old.confidence, confidence),
                evidence=old.evidence + [evidence],
                updated_at=old.updated_at
            )
        else:
            self.belief_states[agent_id] = BeliefState(
                agent_id=agent_id,
                suspected_camp=camp,
                confidence=confidence,
                evidence=[evidence],
                updated_at=0
            )

    def get_suspicious_players(self, threshold: float = 0.5
                               ) -> List[BeliefState]:
        """获取可疑玩家列表"""
        return [
            b for b in self.belief_states.values()
            if b.suspected_camp == "duck" and b.confidence >= threshold
        ]

    def format_for_prompt(self) -> str:
        """格式化为LLM提示"""
        parts = []

        # 信念状态
        if self.belief_states:
            parts.append("## 你的推断")
            for agent_id, belief in self.belief_states.items():
                parts.append(
                    f"- 玩家{agent_id}: 可能是{belief.suspected_camp}, "
                    f"置信度{belief.confidence:.0%}"
                )

        # 最近事件
        if self.episodic_memory:
            parts.append("\n## 最近发生的事件")
            for event in self.episodic_memory[-5:]:
                parts.append(
                    f"- 第{event.round_num}轮: {event.event_type.value} - "
                    f"{event.content[:50]}"
                )

        return "\n".join(parts)
```

#### 2.2.2 Agent Profile 生成器

**借鉴 MiroFish 的人设生成思路**：

```python
# src/agents/profile_generator.py

PERSONA_TEMPLATES = {
    "aggressive_accuser": {
        "name": "激进指控者",
        "traits": ["冲动", "直接", "善于施压"],
        "behavior": {
            "accuse_frequency": 0.8,  # 高频指控
            "defense_frequency": 0.3,
            "trust_threshold": 0.3    # 低信任阈值
        },
        "prompt_style": "你的发言风格直接、犀利，喜欢质疑他人。"
    },

    "careful_analyst": {
        "name": "谨慎分析者",
        "traits": ["理性", "善于观察", "保守"],
        "behavior": {
            "accuse_frequency": 0.3,
            "defense_frequency": 0.5,
            "trust_threshold": 0.7
        },
        "prompt_style": "你的发言风格谨慎、理性，喜欢分析证据后再下结论。"
    },

    "social_butterfly": {
        "name": "社交达人",
        "traits": ["友善", "善于交际", "中立"],
        "behavior": {
            "accuse_frequency": 0.4,
            "defense_frequency": 0.6,
            "trust_threshold": 0.5
        },
        "prompt_style": "你的发言风格友善、亲和，喜欢调解矛盾。"
    },

    "silent_observer": {
        "name": "沉默观察者",
        "traits": ["安静", "善于倾听", "神秘"],
        "behavior": {
            "accuse_frequency": 0.2,
            "defense_frequency": 0.4,
            "trust_threshold": 0.6
        },
        "prompt_style": "你的发言简洁、谨慎，更喜欢观察而非主动发言。"
    }
}

class AgentProfileGenerator:
    """Agent Profile 生成器"""

    @staticmethod
    def generate_persona_prompt(
        role_type: str,
        camp: str,
        personality_type: str = None
    ) -> str:
        """生成角色人设提示"""

        # 选择性格模板
        if personality_type is None:
            personality_type = random.choice(list(PERSONA_TEMPLATES.keys()))

        template = PERSONA_TEMPLATES[personality_type]

        # 基础身份
        if camp == "goose":
            base_identity = """
你是鹅阵营的一员，目标是找出并投票淘汰所有鸭子。
你需要通过观察和推理，找出那些行为可疑的玩家。
"""
        elif camp == "duck":
            base_identity = """
你是鸭阵营的一员，目标是隐藏身份并消灭鹅阵营。
你需要伪装成好人，同时暗中配合你的鸭同伴。
注意：你和你的鸭同伴互相认识，可以利用这一点进行配合。
"""
        else:  # neutral (dodo)
            base_identity = """
你是呆呆鸟，中立阵营。
你的特殊目标是：被投票出局才能获胜。
你需要表现得足够可疑，让其他人投票给你，但又不能太明显。
"""

        # 组合提示
        return f"""
{base_identity}

## 你的性格特征
{template['prompt_style']}

## 行为倾向
- 指控倾向: {template['behavior']['accuse_frequency']:.0%}
- 辩护倾向: {template['behavior']['defense_frequency']:.0%}
- 信任阈值: {template['behavior']['trust_threshold']:.0%}

## 行为准则
1. 始终保持角色一致性
2. 根据你的性格特征决定发言风格
3. 记住你观察到的所有信息
4. 根据游戏进程调整策略
"""
```

---

## 三、Phase 2 开发建议：空间模拟系统

### 3.1 地图与移动系统设计

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         空间模拟系统架构                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                          Map Layer                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │                      GameMap                                     │  │  │
│  │  │  ┌─────────────────────────────────────────────────────────┐    │  │  │
│  │  │  │  Rooms: [大厅, 厨房, 机房, 医疗室, 仓库, ...]           │    │  │  │
│  │  │  │  Corridors: 连接各房间的通道                             │    │  │  │
│  │  │  │  Tasks: 各房间内的任务点                                 │    │  │  │
│  │  │  └─────────────────────────────────────────────────────────┘    │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                       │                                      │
│                                       v                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        Spatial Index Layer                             │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐       │  │
│  │  │ Grid Index      │  │ QuadTree        │  │ Room-based      │       │  │
│  │  │ (快速邻域查询)  │  │ (动态视野)      │  │ (房间级索引)    │       │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                       │                                      │
│                                       v                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        Visibility Layer                                │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │  VisionSystem                                                    │  │  │
│  │  │  - 视野范围计算 (锥形/圆形)                                      │  │  │
│  │  │  - 遮挡关系处理 (墙壁遮挡)                                       │  │  │
│  │  │  - 目击事件生成 (看到某人杀人)                                   │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 核心代码实现建议

```python
# src/game/spatial/map_system.py

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
from enum import Enum

class RoomType(Enum):
    HALL = "大厅"
    KITCHEN = "厨房"
    ENGINE = "机房"
    MEDBAY = "医疗室"
    STORAGE = "仓库"
    ELECTRICAL = "电力室"
    ADMIN = "管理室"
    CAFETERIA = "餐厅"

@dataclass
class Position:
    """2D坐标"""
    x: float
    y: float

    def distance_to(self, other: 'Position') -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

@dataclass
class Room:
    """房间"""
    room_id: str
    room_type: RoomType
    bounds: Tuple[float, float, float, float]  # (x1, y1, x2, y2)
    connected_rooms: Set[str] = field(default_factory=set)
    task_positions: List[Position] = field(default_factory=list)

    def contains(self, pos: Position) -> bool:
        x1, y1, x2, y2 = self.bounds
        return x1 <= pos.x <= x2 and y1 <= pos.y <= y2

@dataclass
class Corridor:
    """走廊（连接房间）"""
    corridor_id: str
    room1_id: str
    room2_id: str
    path: List[Position]  # 走廊路径点

@dataclass
class GameMap:
    """游戏地图"""
    rooms: Dict[str, Room]
    corridors: Dict[str, Corridor]

    def get_room_at(self, pos: Position) -> Optional[Room]:
        """获取指定位置的房间"""
        for room in self.rooms.values():
            if room.contains(pos):
                return room
        return None

    def get_connected_rooms(self, room_id: str) -> Set[str]:
        """获取相连的房间"""
        if room_id in self.rooms:
            return self.rooms[room_id].connected_rooms
        return set()

    def get_path_between(self, room1: str, room2: str) -> List[Position]:
        """获取两个房间之间的路径（简化版：直接通过走廊）"""
        # 实际实现可以用 A* 算法
        pass


# src/game/spatial/vision_system.py

@dataclass
class VisionConfig:
    """视野配置"""
    vision_range: float = 200.0      # 视野距离
    vision_angle: float = 120.0      # 视野角度（度）
    through_walls: bool = False      # 是否穿墙

@dataclass
class WitnessEvent:
    """目击事件"""
    witness_id: str
    target_id: str
    event_type: str  # "kill", "vent", "task"
    position: Position
    timestamp: int

class VisionSystem:
    """视野系统"""

    def __init__(self, game_map: GameMap, config: VisionConfig = None):
        self.map = game_map
        self.config = config or VisionConfig()
        self.witness_events: List[WitnessEvent] = []

    def get_visible_agents(
        self,
        observer_pos: Position,
        observer_direction: float,
        all_agents: Dict[str, 'Agent']
    ) -> List[str]:
        """获取可见的Agent列表"""
        visible = []

        for agent_id, agent in all_agents.items():
            if not agent.is_alive:
                continue

            agent_pos = agent.position

            # 1. 距离检查
            distance = observer_pos.distance_to(agent_pos)
            if distance > self.config.vision_range:
                continue

            # 2. 角度检查（如果使用锥形视野）
            # angle = self._calculate_angle(observer_pos, agent_pos)
            # if abs(angle - observer_direction) > self.config.vision_angle / 2:
            #     continue

            # 3. 遮挡检查（墙壁）
            if not self.config.through_walls:
                if self._is_blocked_by_wall(observer_pos, agent_pos):
                    continue

            visible.append(agent_id)

        return visible

    def _is_blocked_by_wall(self, pos1: Position, pos2: Position) -> bool:
        """检查两点之间是否有墙壁遮挡"""
        # 简化实现：检查是否在同一个房间
        room1 = self.map.get_room_at(pos1)
        room2 = self.map.get_room_at(pos2)

        if room1 is None or room2 is None:
            return True  # 不在房间内，视为遮挡

        if room1.room_id == room2.room_id:
            return False  # 同一房间，不遮挡

        # 不同房间需要检查是否有走廊连接
        return room2.room_id not in room1.connected_rooms

    def record_witness_event(
        self,
        witness_id: str,
        target_id: str,
        event_type: str,
        position: Position,
        timestamp: int
    ):
        """记录目击事件"""
        event = WitnessEvent(
            witness_id=witness_id,
            target_id=target_id,
            event_type=event_type,
            position=position,
            timestamp=timestamp
        )
        self.witness_events.append(event)

        return event

    def get_events_for_agent(
        self,
        agent_id: str,
        as_witness: bool = True
    ) -> List[WitnessEvent]:
        """获取与某Agent相关的目击事件"""
        if as_witness:
            return [e for e in self.witness_events
                    if e.witness_id == agent_id]
        else:
            return [e for e in self.witness_events
                    if e.target_id == agent_id]


# src/game/spatial/movement_system.py

class MovementSystem:
    """移动系统"""

    def __init__(self, game_map: GameMap, vision_system: VisionSystem):
        self.map = game_map
        self.vision = vision_system
        self.agent_positions: Dict[str, Position] = {}
        self.agent_destinations: Dict[str, Position] = {}
        self.move_speed: float = 50.0  # 每tick移动距离

    def set_agent_position(self, agent_id: str, pos: Position):
        """设置Agent位置"""
        self.agent_positions[agent_id] = pos

    def move_agent_towards(
        self,
        agent_id: str,
        destination: Position,
        delta_time: float
    ) -> Position:
        """移动Agent朝向目标"""
        current = self.agent_positions.get(agent_id)
        if current is None:
            return destination

        # 计算移动向量
        dx = destination.x - current.x
        dy = destination.y - current.y
        distance = (dx ** 2 + dy ** 2) ** 0.5

        if distance < self.move_speed * delta_time:
            # 已到达
            self.agent_positions[agent_id] = destination
            return destination

        # 按速度移动
        ratio = self.move_speed * delta_time / distance
        new_pos = Position(
            x=current.x + dx * ratio,
            y=current.y + dy * ratio
        )

        self.agent_positions[agent_id] = new_pos
        return new_pos

    def get_nearby_agents(
        self,
        agent_id: str,
        radius: float
    ) -> List[str]:
        """获取附近的Agent"""
        current = self.agent_positions.get(agent_id)
        if current is None:
            return []

        nearby = []
        for other_id, other_pos in self.agent_positions.items():
            if other_id == agent_id:
                continue
            if current.distance_to(other_pos) <= radius:
                nearby.append(other_id)

        return nearby
```

### 3.3 游戏流程集成

```python
# src/game/phase_scheduler.py

from enum import Enum
from typing import Dict, List, Callable
from dataclasses import dataclass

class GamePhaseType(Enum):
    """游戏阶段类型"""
    LOBBY = "等待大厅"
    ROLE_ASSIGN = "角色分配"
    TASK_PHASE = "任务阶段"      # 新增：鹅做任务，鸭可杀人
    DISCUSSION = "讨论阶段"
    VOTING = "投票阶段"
    EXECUTION = "处决阶段"
    GAME_OVER = "游戏结束"

@dataclass
class PhaseConfig:
    """阶段配置"""
    phase_type: GamePhaseType
    duration: float  # 秒
    allow_movement: bool
    allow_kill: bool
    allow_task: bool

class PhaseScheduler:
    """阶段调度器"""

    DEFAULT_CONFIG = {
        GamePhaseType.TASK_PHASE: PhaseConfig(
            phase_type=GamePhaseType.TASK_PHASE,
            duration=60.0,
            allow_movement=True,
            allow_kill=True,
            allow_task=True
        ),
        GamePhaseType.DISCUSSION: PhaseConfig(
            phase_type=GamePhaseType.DISCUSSION,
            duration=120.0,
            allow_movement=False,
            allow_kill=False,
            allow_task=False
        ),
        GamePhaseType.VOTING: PhaseConfig(
            phase_type=GamePhaseType.VOTING,
            duration=30.0,
            allow_movement=False,
            allow_kill=False,
            allow_task=False
        ),
    }

    def __init__(self):
        self.current_phase: GamePhaseType = GamePhaseType.LOBBY
        self.phase_timer: float = 0.0
        self.phase_callbacks: Dict[GamePhaseType, List[Callable]] = {}

    def register_callback(
        self,
        phase: GamePhaseType,
        callback: Callable
    ):
        """注册阶段回调"""
        if phase not in self.phase_callbacks:
            self.phase_callbacks[phase] = []
        self.phase_callbacks[phase].append(callback)

    def advance_phase(self):
        """进入下一阶段"""
        phase_order = [
            GamePhaseType.TASK_PHASE,
            GamePhaseType.DISCUSSION,
            GamePhaseType.VOTING,
            GamePhaseType.EXECUTION,
        ]

        if self.current_phase == GamePhaseType.EXECUTION:
            self.current_phase = GamePhaseType.TASK_PHASE
        else:
            current_idx = phase_order.index(self.current_phase)
            self.current_phase = phase_order[(current_idx + 1) % len(phase_order)]

        # 重置计时器
        config = self.DEFAULT_CONFIG.get(self.current_phase)
        self.phase_timer = config.duration if config else 0

        # 触发回调
        for callback in self.phase_callbacks.get(self.current_phase, []):
            callback()

    def tick(self, delta_time: float) -> bool:
        """
        时间推进
        Returns: True 如果阶段结束
        """
        self.phase_timer -= delta_time
        if self.phase_timer <= 0:
            self.advance_phase()
            return True
        return False
```

---

## 四、Phase 3 开发建议：增强记忆与知识系统

### 4.1 长期记忆 + RAG

**借鉴 MiroFish 的 Zep Cloud 架构**：

```python
# src/agents/long_term_memory.py

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

# 可选依赖：向量数据库
try:
    import chromadb
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False

@dataclass
class MemoryEntry:
    """记忆条目"""
    content: str
    memory_type: str  # "event", "inference", "dialogue"
    round_num: int
    importance: float  # 0.0 - 1.0
    metadata: Dict[str, Any]

class LongTermMemory:
    """长期记忆系统（带RAG检索）"""

    def __init__(self, use_vector_db: bool = True):
        self.memories: List[MemoryEntry] = []

        # 向量数据库（可选）
        self.use_vector_db = use_vector_db and HAS_CHROMA
        if self.use_vector_db:
            self.client = chromadb.Client()
            self.collection = self.client.create_collection("game_memories")

    def store(self, entry: MemoryEntry):
        """存储记忆"""
        self.memories.append(entry)

        if self.use_vector_db:
            self.collection.add(
                documents=[entry.content],
                metadatas=[{
                    "type": entry.memory_type,
                    "round": entry.round_num,
                    "importance": entry.importance
                }],
                ids=[f"mem_{len(self.memories)}"]
            )

    def retrieve_relevant(
        self,
        query: str,
        top_k: int = 5
    ) -> List[MemoryEntry]:
        """检索相关记忆"""
        if self.use_vector_db:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )

            # 根据ID找回原始记忆
            relevant = []
            for i, doc in enumerate(results['documents'][0]):
                # 简化：直接匹配内容
                for mem in self.memories:
                    if mem.content == doc:
                        relevant.append(mem)
                        break

            return relevant
        else:
            # 简单关键词匹配
            keywords = query.lower().split()
            scored = []
            for mem in self.memories:
                score = sum(1 for kw in keywords
                           if kw in mem.content.lower())
                scored.append((score, mem))

            scored.sort(key=lambda x: x[0], reverse=True)
            return [m for _, m in scored[:top_k]]

    def get_round_summary(self, round_num: int) -> str:
        """获取某轮的总结"""
        round_memories = [
            m for m in self.memories
            if m.round_num == round_num
        ]

        if not round_memories:
            return ""

        summary_parts = []
        for mem in sorted(round_memories, key=lambda m: m.importance,
                          reverse=True)[:5]:
            summary_parts.append(f"- {mem.content}")

        return "\n".join(summary_parts)
```

### 4.2 知识图谱（简化版）

```python
# src/agents/knowledge_graph.py

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
from enum import Enum

class RelationType(Enum):
    """关系类型"""
    ACCUSED = "指控"
    DEFENDED = "辩护"
    VOTED_FOR = "投票给"
    WITNESSED = "目击"
    SUSPECTS = "怀疑"
    TRUSTS = "信任"
    TEAMMATE = "队友"  # 鸭子互相知道

@dataclass
class KnowledgeNode:
    """知识节点"""
    agent_id: str
    attributes: Dict[str, Any] = field(default_factory=dict)

@dataclass
class KnowledgeEdge:
    """知识边"""
    source: str
    target: str
    relation: RelationType
    round_num: int
    evidence: str
    confidence: float = 1.0

class AgentKnowledgeGraph:
    """Agent知识图谱"""

    def __init__(self, owner_id: str):
        self.owner_id = owner_id
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.edges: List[KnowledgeEdge] = []

    def add_observation(
        self,
        source: str,
        target: str,
        relation: RelationType,
        round_num: int,
        evidence: str,
        confidence: float = 1.0
    ):
        """添加观察记录"""
        # 确保节点存在
        if source not in self.nodes:
            self.nodes[source] = KnowledgeNode(agent_id=source)
        if target not in self.nodes:
            self.nodes[target] = KnowledgeNode(agent_id=target)

        # 添加边
        self.edges.append(KnowledgeEdge(
            source=source,
            target=target,
            relation=relation,
            round_num=round_num,
            evidence=evidence,
            confidence=confidence
        ))

    def get_suspicions(self) -> Dict[str, float]:
        """获取对所有玩家的怀疑度"""
        suspicions = {}

        for edge in self.edges:
            if edge.target not in suspicions:
                suspicions[edge.target] = 0.0

            if edge.relation == RelationType.ACCUSED:
                suspicions[edge.target] += 0.2 * edge.confidence
            elif edge.relation == RelationType.DEFENDED:
                suspicions[edge.target] -= 0.1 * edge.confidence
            elif edge.relation == RelationType.WITNESSED:
                # 目击杀人是强证据
                suspicions[edge.target] += 0.5 * edge.confidence

        # 归一化到 [0, 1]
        if suspicions:
            max_val = max(abs(v) for v in suspicions.values())
            if max_val > 0:
                suspicions = {
                    k: min(1.0, max(0.0, (v + max_val) / (2 * max_val)))
                    for k, v in suspicions.items()
                }

        return suspicions

    def format_for_prompt(self) -> str:
        """格式化为提示"""
        parts = ["## 你已知的信息关系"]

        # 按关系类型分组
        by_relation = {}
        for edge in self.edges:
            rel_name = edge.relation.value
            if rel_name not in by_relation:
                by_relation[rel_name] = []
            by_relation[rel_name].append(edge)

        for rel_name, edges in by_relation.items():
            parts.append(f"\n### {rel_name}")
            for edge in edges[-5:]:  # 最近5条
                parts.append(
                    f"- 第{edge.round_num}轮: {edge.source} {rel_name} "
                    f"{edge.target} ({edge.evidence[:30]}...)"
                )

        return "\n".join(parts)
```

---

## 五、Phase 3 开发建议：可视化界面

### 5.1 推荐技术栈

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         可视化系统技术选型                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  方案A: 轻量级（推荐）                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  前端: Vue 3 + Vite (与 MiroFish 一致)                               │   │
│  │  地图: Canvas 2D / SVG                                               │   │
│  │  通信: WebSocket (实时更新)                                          │   │
│  │  优点: 开发快、轻量、与现有架构兼容                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  方案B: 游戏引擎                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  引擎: Phaser.js / PixiJS                                            │   │
│  │  特点: 完整的游戏引擎支持                                            │   │
│  │  适用: 需要复杂动画、特效                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  方案C: 3D版本                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  引擎: Three.js / Babylon.js                                         │   │
│  │  特点: 3D 渲染                                                       │   │
│  │  适用: 需要沉浸式 3D 体验                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 后端 API 扩展建议

```python
# src/api/routes.py (新增)

from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# REST API
@app.route('/api/game/create', methods=['POST'])
def create_game():
    """创建新游戏"""
    data = request.json
    # ... 创建游戏逻辑
    return jsonify({"game_id": "xxx", "status": "created"})

@app.route('/api/game/<game_id>/state', methods=['GET'])
def get_game_state(game_id):
    """获取游戏状态"""
    # ... 返回游戏状态
    return jsonify({"phase": "discussion", "round": 1, ...})

@app.route('/api/game/<game_id>/start', methods=['POST'])
def start_game(game_id):
    """开始游戏"""
    # ... 开始游戏逻辑
    return jsonify({"status": "started"})

# WebSocket 事件
@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    emit('connected', {'status': 'ok'})

@socketio.on('join_game')
def handle_join_game(data):
    """加入游戏"""
    game_id = data.get('game_id')
    player_name = data.get('player_name')
    # ... 加入逻辑

@socketio.on('send_message')
def handle_message(data):
    """发送消息"""
    # ... 处理消息
    # 广播给所有玩家
    emit('message_received', data, broadcast=True)

@socketio.on('vote')
def handle_vote(data):
    """投票"""
    # ... 处理投票

def broadcast_game_state(game_id: str, state: dict):
    """广播游戏状态更新"""
    socketio.emit('game_state_update', state, room=game_id)

def broadcast_agent_action(game_id: str, action: dict):
    """广播 Agent 动作"""
    socketio.emit('agent_action', action, room=game_id)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5001)
```

---

## 六、Phase 4 开发建议：评测系统

### 6.1 自动化评测框架

```python
# src/evaluation/game_evaluator.py

from dataclasses import dataclass
from typing import Dict, List, Any
from collections import defaultdict
import json

@dataclass
class GameResult:
    """游戏结果"""
    game_id: str
    winner: str  # "goose" / "duck" / "dodo"
    rounds: int
    survivors: List[str]
    events: List[Dict]

class GameEvaluator:
    """游戏评测器"""

    def __init__(self):
        self.results: List[GameResult] = []
        self.role_stats: Dict[str, Dict] = defaultdict(lambda: {
            "wins": 0, "losses": 0, "total_rounds": 0
        })

    def record_game(self, result: GameResult):
        """记录游戏结果"""
        self.results.append(result)

        # 更新统计
        for player in result.survivors:
            # 这里需要知道玩家的角色
            pass

    def run_batch_simulation(
        self,
        num_games: int,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """批量模拟游戏"""
        results = []

        for i in range(num_games):
            # 创建游戏引擎
            engine = GameEngine(config)

            # 设置游戏（可以是随机玩家）
            engine.setup_game()

            # 运行游戏
            winner = engine.run_game()

            # 记录结果
            summary = engine.get_game_summary()
            results.append({
                "game_id": f"sim_{i}",
                "winner": winner.value,
                "rounds": summary["rounds"],
                "players": summary["players"]
            })

        return self._analyze_batch_results(results)

    def _analyze_batch_results(
        self,
        results: List[Dict]
    ) -> Dict[str, Any]:
        """分析批量结果"""
        total = len(results)

        # 胜率统计
        win_counts = defaultdict(int)
        for r in results:
            win_counts[r["winner"]] += 1

        win_rates = {
            camp: count / total
            for camp, count in win_counts.items()
        }

        # 平均轮数
        avg_rounds = sum(r["rounds"] for r in results) / total

        return {
            "total_games": total,
            "win_rates": win_rates,
            "avg_rounds": avg_rounds,
            "detailed_results": results
        }

    def generate_report(self) -> str:
        """生成评测报告"""
        report = []
        report.append("# 游戏平衡评测报告")
        report.append(f"\n## 总游戏数: {len(self.results)}")

        # 胜率统计
        report.append("\n## 阵营胜率")
        # ...

        return "\n".join(report)
```

---

## 七、开发优先级建议

### 7.1 推荐开发顺序

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         开发优先级路线图                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  第1周: 增强核心Agent系统                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  [1] 实现增强记忆系统 (EnhancedMemory)                               │   │
│  │  [2] 添加 Agent Profile 生成器                                       │   │
│  │  [3] 优化 LLM 提示词模板                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  第2-3周: 空间模拟系统                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  [4] 实现地图系统 (GameMap, Room, Corridor)                          │   │
│  │  [5] 实现视野系统 (VisionSystem)                                     │   │
│  │  [6] 实现移动系统 (MovementSystem)                                   │   │
│  │  [7] 集成到游戏流程 (PhaseScheduler)                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  第4周: 游戏规则完善                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  [8] 实现完整角色技能                                                │   │
│  │  [9] 实现任务系统                                                    │   │
│  │  [10] 实现击杀/目击机制                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  第5-6周: 可视化界面                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  [11] 后端 API + WebSocket                                           │   │
│  │  [12] 前端地图展示                                                   │   │
│  │  [13] Agent 行为可视化                                               │   │
│  │  [14] 对话界面                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  第7周+: 增强与优化                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  [15] 长期记忆 + RAG                                                 │   │
│  │  [16] 知识图谱                                                       │   │
│  │  [17] 评测系统                                                       │   │
│  │  [18] 性能优化                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 技术债务与注意事项

| 问题 | 影响 | 解决方案 |
|-----|------|---------|
| LLM 调用成本 | 高频调用导致费用增加 | 实现缓存、批量处理、使用更便宜模型 |
| Agent 决策延迟 | 游戏体验卡顿 | 异步处理、预生成回复 |
| 记忆上下文过长 | Token 超限 | 实现记忆压缩、重要性筛选 |
| 状态一致性 | 并发问题 | 使用锁、事件溯源 |

---

## 八、参考资源

### 8.1 MiroFish 可借鉴的代码

| 模块 | 文件 | 可借鉴点 |
|-----|------|---------|
| Agent Profile | `oasis_profile_generator.py` | 人设生成、行为配置 |
| 记忆更新 | `zep_graph_memory_updater.py` | 批量记忆更新 |
| 配置生成 | `simulation_config_generator.py` | 智能参数推理 |
| IPC通信 | `simulation_ipc.py` | 进程间通信模式 |
| 前端架构 | `frontend/src/` | Vue 3 组件结构 |

### 8.2 推荐阅读

- **OASIS 论文**: 社交媒体模拟的理论基础
- **Zep Cloud 文档**: GraphRAG 实现参考
- **LangChain/LangGraph**: Agent 框架最佳实践
- **Phaser.js 文档**: 2D 游戏引擎

---

*文档生成时间: 2026-03-11*
*适用于 Goose-Goose-Duck.ai 项目后续开发*
