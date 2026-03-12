"""
增强版游戏引擎 - 支持完整的鹅鸭杀游戏循环
包含：夜晚阶段、白天阶段、任务系统、杀人机制
"""
from typing import List, Dict, Any, Optional, Callable
import logging
import random
import asyncio
import time

from ..llm import LLMFactory, BaseLLM
from ..agents import Agent
from ..roles import Role, RoleType, Camp
from .game_state import GameState, GamePhase, GameResult
from .dialogue_manager import DialogueManager
from .information_isolation import InformationIsolation
from .map_system import GameMap, Room, Task, RoomType
from .vision_system import VisionSystem, GameEvent, EventType
from .action_system import ActionType, GameAction, ActionValidator, ActionExecutor

logger = logging.getLogger(__name__)


class EnhancedGameEngine:
    """
    增强版游戏引擎 - 支持完整的鹅鸭杀游戏机制
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化增强版游戏引擎

        Args:
            config: 游戏配置（可选，默认从 config.yaml 加载）
        """
        # 加载配置
        self.config = config or self._load_config()

        # 初始化 LLM
        self.llm = LLMFactory.create_llm(self.config['llm'])

        # 初始化游戏组件
        self.agents: Dict[str, Agent] = {}
        self.game_state = GameState()
        self.dialogue_manager = DialogueManager()
        self.info_isolation = InformationIsolation()

        # Phase 2 新增组件
        self.game_map = GameMap()
        self.vision_system = VisionSystem(self.game_map)
        self.action_executor = ActionExecutor(
            self.game_map,
            self.vision_system,
            self.game_state
        )

        # 游戏配置
        self.max_rounds = self.config.get('game', {}).get('discussion', {}).get('max_rounds', 10)
        self.day_phase_duration = self.config.get('game', {}).get('day_duration', 30)  # 秒
        self.night_phase_duration = self.config.get('game', {}).get('night_duration', 10)  # 秒
        self.task_completion_win = self.config.get('game', {}).get('task_completion_win', 0.8)  # 任务完成80%获胜

        # 事件回调（用于 WebSocket 广播）
        self.event_callback: Optional[Callable] = None

        logger.info("增强版游戏引擎初始化完成")

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        import yaml
        from pathlib import Path

        config_path = Path("config.yaml")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.info(f"配置文件加载成功")
                return config

        return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'llm': {
                'model': 'glm-4',
                'temperature': 0.7,
                'max_tokens': 2000
            },
            'game': {
                'player_count': 6,
                'roles': {
                    'goose': [{'name': '鹅', 'count': 3}],
                    'duck': [{'name': '鸭子', 'count': 2}],
                    'neutral': [{'name': '呆呆鸟', 'count': 1}]
                },
                'discussion': {'max_rounds': 10},
                'day_duration': 30,
                'night_duration': 10,
                'task_completion_win': 0.8
            }
        }

    def set_event_callback(self, callback: Callable):
        """设置事件回调函数"""
        self.event_callback = callback

    async def broadcast_event(self, event_type: str, data: Dict[str, Any]):
        """广播事件"""
        if self.event_callback:
            await self.event_callback(event_type, data)
        logger.info(f"事件: {event_type} - {data}")

    async def broadcast_position_update(self):
        """广播位置更新"""
        positions = {}
        for agent_id in self.agents:
            pos = self.vision_system.get_agent_position(agent_id)
            if pos:
                agent = self.agents[agent_id]
                positions[agent_id] = {
                    "name": agent.name,
                    "room_id": pos.room_id,
                    "is_alive": pos.is_alive,
                    "is_ghost": pos.is_ghost
                }

        await self.broadcast_event("position_update", {
            "positions": positions
        })

    async def broadcast_map_update(self):
        """广播地图更新"""
        rooms = {}
        for room_id, room in self.game_map.rooms.items():
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

        completed, total = self.game_map.get_total_task_progress()

        await self.broadcast_event("map_update", {
            "mapInfo": {
                "rooms": rooms,
                "task_progress": {
                    "completed": completed,
                    "total": total,
                    "percentage": round(completed / total * 100, 1) if total > 0 else 0
                }
            }
        })

    def setup_game(self, player_names: Optional[List[str]] = None):
        """设置游戏"""
        logger.info("开始设置增强版游戏...")

        # 获取角色配置
        roles_config = self.config['game']['roles']

        # 创建角色列表
        roles = []
        for camp_name, role_list in roles_config.items():
            for role_info in role_list:
                count = role_info['count']
                if camp_name == 'goose':
                    role_type = RoleType.GOOSE
                elif camp_name == 'duck':
                    role_type = RoleType.DUCK
                else:
                    role_type = RoleType.DODO

                for _ in range(count):
                    roles.append(Role.from_type(role_type))

        random.shuffle(roles)

        # 生成玩家名称
        if player_names is None:
            player_names = [f"玩家{i + 1}" for i in range(len(roles))]

        # 获取出生点房间
        spawn_room = self.game_map.get_spawn_room()

        # 获取所有房间，用于分散玩家
        all_rooms = list(self.game_map.rooms.keys())
        random.shuffle(all_rooms)

        # 创建 Agent
        for i, (name, role) in enumerate(zip(player_names, roles)):
            agent_id = f"agent_{i}"
            agent = Agent(
                agent_id=agent_id,
                name=name,
                role=role,
                llm=self.llm,
                memory_config=self.config.get('agent', {}).get('memory', {})
            )
            self.agents[agent_id] = agent

            # 注册到信息隔离系统
            self.info_isolation.register_agent(agent_id, role.camp)

            # 添加到存活玩家列表
            self.game_state.alive_players.append(agent_id)

            # 初始化位置（分散在不同房间，避免开局就被杀）
            # 前两个玩家在出生点，其余分散到其他房间
            if i < 2:
                start_room = spawn_room
            else:
                start_room = all_rooms[i % len(all_rooms)]
            self.vision_system.initialize_agent(agent_id, start_room)
            logger.info(f"初始化 Agent {agent_id} ({name}) 位置在 {start_room}, 所有房间: {all_rooms}")

        # 分享阵营信息（鸭阵营互相认识）
        self.info_isolation.share_camp_information()

        logger.info(f"增强版游戏设置完成，共 {len(self.agents)} 名玩家")
        logger.info(f"角色分配: {[(a.name, a.role.name) for a in self.agents.values()]}")

    # ==================== 夜晚阶段 ====================

    async def run_night_phase(self):
        """
        夜晚阶段 - 所有 Agent 独立行动

        改进后的夜晚阶段：
        1. 每个 Agent 都有独立思考和行动
        2. 鸭子：寻找目标、击杀
        3. 鹅：巡逻、休息
        4. 呆呆鸟：观察
        5. 所有行动都会记录并广播（但不影响其他 Agent 的信息）
        """
        logger.info(f"=== 第 {self.game_state.round_num} 轮 - 夜晚阶段 ===")
        self.game_state.phase = GamePhase.NIGHT

        await self.broadcast_event("phase_changed", {
            "phase": "night",
            "round": self.game_state.round_num,
            "message": "夜幕降临，所有人开始行动..."
        })

        # 所有存活的 Agent 按顺序行动
        alive_agents = [self.agents[aid] for aid in self.game_state.alive_players]
        random.shuffle(alive_agents)  # 随机顺序

        for agent in alive_agents:
            if not agent.is_alive:
                continue

            # Agent 夜晚独立思考
            await self._agent_night_think(agent)

            # 根据角色执行不同行动
            if agent.role.camp == Camp.DUCK:
                await self._duck_night_action(agent)
            elif agent.role.camp == Camp.GOOSE:
                await self._goose_night_action(agent)
            else:  # DODO
                await self._dodo_night_action(agent)

            # 广播 Agent 行动日志（观察者视角）
            await self._broadcast_agent_action(agent)

            await asyncio.sleep(0.5)

    async def _agent_night_think(self, agent: Agent):
        """
        Agent 夜晚独立思考

        这是每个 Agent 在夜晚的私有思考过程，
        记录在私有记忆中，不影响其他 Agent。
        """
        pos = self.vision_system.get_agent_position(agent.agent_id)
        room_name = self.game_map.get_room_name(pos.room_id) if pos else "未知"

        context = f"""第 {self.game_state.round_num} 轮 - 夜晚阶段
你当前在 {room_name}。
你的角色是 {agent.role.name} ({agent.role.camp.value})。
"""

        # 调用 Agent 的思考方法
        try:
            thought = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: agent.think(context, phase="night")
            )

            # 记录思考日志（用于观察者）
            agent._last_night_thought = thought
            agent._last_action = "思考"

            logger.info(f"[夜晚思考] {agent.name}: {thought[:100]}...")

        except Exception as e:
            logger.error(f"Agent {agent.name} 夜晚思考失败: {e}")
            agent._last_night_thought = "保持警惕..."
            agent._last_action = "休息"

    async def _duck_night_action(self, duck: Agent):
        """鸭子夜晚行动 - 寻找目标并击杀"""
        pos = self.vision_system.get_agent_position(duck.agent_id)
        if not pos:
            return

        # 获取同房间的其他存活玩家
        targets = []
        for aid in self.game_state.alive_players:
            if aid == duck.agent_id:
                continue
            other_pos = self.vision_system.get_agent_position(aid)
            if other_pos and other_pos.room_id == pos.room_id and other_pos.is_alive:
                targets.append(self.agents[aid])

        if not targets:
            # 鸭子需要移动找目标
            await self._duck_hunt(duck)
            return

        # 鸭子选择目标（AI 决策）
        target_names = [t.name for t in targets]
        context = f"你是鸭子，现在是夜晚。你所在房间有以下玩家: {', '.join(target_names)}。选择一个目标进行击杀。"

        target_name = await self._duck_choose_target(duck, target_names, context)

        if target_name:
            target = next((t for t in targets if t.name == target_name), None)
            if target:
                duck._last_action = f"准备击杀 {target_name}"
                await self._execute_kill(duck, target)

    async def _goose_night_action(self, goose: Agent):
        """鹅夜晚行动 - 巡逻或休息"""
        pos = self.vision_system.get_agent_position(goose.agent_id)
        if not pos:
            return

        # 鹅在夜晚可能会移动巡逻，或者原地休息
        # 这里简化为随机决定
        action = random.choice(["patrol", "rest"])

        if action == "patrol":
            # 移动到相邻房间巡逻
            adjacent = self.game_map.get_adjacent_rooms(pos.room_id)
            if adjacent:
                target_room = random.choice(adjacent)
                self.vision_system.move_agent(goose.agent_id, target_room)
                room_name = self.game_map.get_room_name(target_room)
                goose._last_action = f"巡逻到 {room_name}"
                logger.info(f"[夜晚] {goose.name} 巡逻到 {room_name}")
                await self.broadcast_position_update()
        else:
            goose._last_action = "原地休息"
            logger.info(f"[夜晚] {goose.name} 原地休息")

    async def _dodo_night_action(self, dodo: Agent):
        """呆呆鸟夜晚行动 - 观察周围"""
        pos = self.vision_system.get_agent_position(dodo.agent_id)
        if not pos:
            return

        # 呆呆鸟观察周围环境
        room_name = self.game_map.get_room_name(pos.room_id)

        # 获取同房间的其他玩家
        others = []
        for aid in self.game_state.alive_players:
            if aid == dodo.agent_id:
                continue
            other_pos = self.vision_system.get_agent_position(aid)
            if other_pos and other_pos.room_id == pos.room_id:
                others.append(self.agents[aid].name)

        if others:
            dodo._last_action = f"在{room_name}观察: {', '.join(others)}"
        else:
            dodo._last_action = f"在{room_name}独自观察"

        logger.info(f"[夜晚] {dodo.name} {dodo._last_action}")

    async def _broadcast_agent_action(self, agent: Agent):
        """
        广播 Agent 行动日志（观察者视角）

        这些日志用于前端展示，但不影响 Agent 之间的信息共享。
        """
        action_log = {
            "agent_id": agent.agent_id,
            "agent_name": agent.name,
            "role": agent.role.name,
            "action": getattr(agent, '_last_action', 'unknown'),
            "thought_summary": getattr(agent, '_last_night_thought', '')[:200] if hasattr(agent, '_last_night_thought') else ''
        }

        await self.broadcast_event("agent_action_log", action_log)

    async def _duck_hunt(self, duck: Agent):
        """鸭子寻找猎物"""
        pos = self.vision_system.get_agent_position(duck.agent_id)
        if not pos:
            return

        # 获取可移动的房间
        adjacent = self.game_map.get_adjacent_rooms(pos.room_id)
        if not adjacent:
            return

        # 随机选择一个房间移动
        target_room = random.choice(adjacent)
        self.vision_system.move_agent(duck.agent_id, target_room)
        logger.info(f"鸭子 {duck.name} 移动到 {self.game_map.get_room_name(target_room)}")

        # 广播位置更新
        await self.broadcast_position_update()

    async def _duck_choose_target(self, duck: Agent, targets: List[str], context: str) -> Optional[str]:
        """鸭子选择击杀目标"""
        try:
            # 使用 LLM 进行决策
            prompt = f"""{context}

请从以下目标中选择一个进行击杀: {', '.join(targets)}
只返回目标名称，不要其他解释。"""

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.llm.chat_with_system(
                    duck.role.get_strategy_prompt(),
                    prompt
                )
            )

            # 解析响应，提取目标名称
            for target in targets:
                if target in response:
                    return target

            # 如果没匹配到，随机选择
            return random.choice(targets) if targets else None

        except Exception as e:
            logger.error(f"鸭子选择目标失败: {e}")
            return random.choice(targets) if targets else None

    async def _execute_kill(self, killer: Agent, victim: Agent):
        """执行击杀"""
        pos = self.vision_system.get_agent_position(killer.agent_id)

        # 记录杀人事件
        event = self.vision_system.record_kill(
            killer.agent_id,
            victim.agent_id,
            pos.room_id
        )

        # 更新游戏状态
        victim.die()
        self.game_state.alive_players.remove(victim.agent_id)
        self.game_state.dead_players.append(victim.agent_id)

        self.game_state.record_event({
            "type": "kill",
            "round": self.game_state.round_num,
            "killer": killer.name,
            "victim": victim.name,
            "room": self.game_map.get_room_name(pos.room_id),
            "witnesses": event.witnesses
        })

        await self.broadcast_event("player_killed", {
            "victim": victim.name,
            "room": self.game_map.get_room_name(pos.room_id),
            "witnesses": [self.agents[w].name for w in event.witnesses]
        })

        # 广播位置更新
        await self.broadcast_position_update()

        logger.info(f"鸭子 {killer.name} 杀了 {victim.name} 在 {self.game_map.get_room_name(pos.room_id)}")

    # ==================== 白天阶段 ====================

    async def run_day_phase(self):
        """
        白天阶段 - 玩家移动、做任务
        """
        logger.info(f"=== 第 {self.game_state.round_num} 轮 - 白天阶段 ===")
        self.game_state.phase = GamePhase.DAY

        await self.broadcast_event("phase_changed", {
            "phase": "day",
            "round": self.game_state.round_num,
            "message": "天亮了，玩家开始活动..."
        })

        # 检查是否有尸体需要报告
        unreported = self.vision_system.get_unreported_bodies()
        if unreported:
            # 有人发现尸体，触发会议
            await self._trigger_body_discovery()
            return

        # 每个存活的 Agent 执行动作
        alive_agents = [self.agents[aid] for aid in self.game_state.alive_players]
        random.shuffle(alive_agents)

        for agent in alive_agents:
            if not agent.is_alive:
                continue

            # Agent 决定行动
            await self._agent_take_action(agent)

            # 检查任务进度
            completed, total = self.game_map.get_total_task_progress()
            if completed / total >= self.task_completion_win:
                logger.info(f"任务完成度达到 {completed/total*100:.1f}%，鹅阵营获胜！")
                self.game_state.result = GameResult.GOOSE_WIN
                return

        # 随机触发会议（模拟发现尸体或紧急会议）
        if random.random() < 0.3:  # 30% 概率触发会议
            await self._trigger_random_meeting()

    async def _agent_take_action(self, agent: Agent):
        """Agent 执行行动"""
        pos = self.vision_system.get_agent_position(agent.agent_id)
        if not pos:
            return

        # 获取房间信息
        room_info = self.vision_system.get_room_info_for_agent(agent.agent_id)

        # 根据角色类型决定行动
        if agent.role.camp == Camp.GOOSE:
            # 鹅：移动到有任务的房间做任务
            await self._goose_do_task(agent, room_info)
        elif agent.role.camp == Camp.DUCK:
            # 鸭子：假装做任务或寻找目标
            await self._duck_pretend_task(agent, room_info)
        else:
            # 中立：随机移动
            await self._neutral_move(agent, room_info)

    async def _goose_do_task(self, agent: Agent, room_info: Dict):
        """鹅做任务"""
        # 检查当前房间是否有任务
        incomplete_tasks = [t for t in room_info.get('tasks', []) if not t.get('is_completed', False)]

        if incomplete_tasks:
            # 做任务
            task = incomplete_tasks[0]
            success = self.game_map.complete_task(task['task_id'], agent.agent_id)

            if success:
                await self.broadcast_event("task_completed", {
                    "agent": agent.name,
                    "task": task['name'],
                    "room": room_info['room_name']
                })
                logger.info(f"{agent.name} 完成任务: {task['name']}")
                # 广播地图更新（任务进度变化）
                await self.broadcast_map_update()
                return

        # 移动到有任务的房间
        adjacent = room_info.get('connected_rooms', [])
        if adjacent:
            target_room = random.choice(adjacent)
            self.vision_system.move_agent(agent.agent_id, target_room)
            logger.info(f"{agent.name} 移动到 {self.game_map.get_room_name(target_room)}")
            # 广播位置更新
            await self.broadcast_position_update()

    async def _duck_pretend_task(self, agent: Agent, room_info: Dict):
        """鸭子假装做任务"""
        # 鸭子假装做任务（不实际完成）
        tasks = room_info.get('tasks', [])
        if tasks:
            # 随机选择"假装"做一个任务
            task = random.choice(tasks)
            logger.info(f"鸭子 {agent.name} 假装做任务: {task['name']}")
            await asyncio.sleep(1)

        # 随机移动
        adjacent = room_info.get('connected_rooms', [])
        if adjacent:
            target_room = random.choice(adjacent)
            self.vision_system.move_agent(agent.agent_id, target_room)
            # 广播位置更新
            await self.broadcast_position_update()

    async def _neutral_move(self, agent: Agent, room_info: Dict):
        """中立角色移动"""
        adjacent = room_info.get('connected_rooms', [])
        if adjacent:
            target_room = random.choice(adjacent)
            self.vision_system.move_agent(agent.agent_id, target_room)
            logger.info(f"{agent.name} 移动到 {self.game_map.get_room_name(target_room)}")
            # 广播位置更新
            await self.broadcast_position_update()

    async def _trigger_body_discovery(self):
        """触发发现尸体"""
        unreported = self.vision_system.get_unreported_bodies()
        if not unreported:
            return

        body = unreported[0]
        victim = self.agents.get(body.target_agent)

        if not victim:
            return

        await self.broadcast_event("body_discovered", {
            "victim": victim.name,
            "room": self.game_map.get_room_name(body.room_id),
            "message": f"发现了 {victim.name} 的尸体！"
        })

        # 触发会议
        await self.run_meeting_phase("body_report")

    async def _trigger_random_meeting(self):
        """随机触发会议"""
        alive_agents = [self.agents[aid] for aid in self.game_state.alive_players]
        if alive_agents:
            caller = random.choice(alive_agents)
            await self.broadcast_event("meeting_called", {
                "caller": caller.name,
                "type": "emergency",
                "message": f"{caller.name} 召开了紧急会议！"
            })
            await self.run_meeting_phase("emergency")

    # ==================== 会议阶段 ====================

    async def run_meeting_phase(self, meeting_type: str = "body_report"):
        """
        会议阶段 - 讨论和投票
        """
        logger.info(f"=== 第 {self.game_state.round_num} 轮 - 会议阶段 ({meeting_type}) ===")
        self.game_state.phase = GamePhase.DISCUSSION
        self.dialogue_manager.set_phase("discussion")

        await self.broadcast_event("phase_changed", {
            "phase": "meeting",
            "round": self.game_state.round_num,
            "meeting_type": meeting_type
        })

        # 讨论阶段
        await self._run_discussion()

        # 投票阶段
        await self._run_voting()

        # 执行投票结果
        await self._execute_vote_result()

    async def _run_discussion(self):
        """
        运行讨论 - 支持独立思考机制

        改进后的流程：
        1. 设置发言顺序
        2. 每个 Agent 先进行独立思考（私有）
        3. Agent 只能看到自己发言之前的对话
        4. 基于策略发言，而非直接反应
        """
        context = f"第 {self.game_state.round_num} 轮会议讨论。请发表你的看法。"

        alive_agents = [self.agents[aid] for aid in self.game_state.alive_players]
        random.shuffle(alive_agents)

        # 设置发言顺序
        speaking_order = [a.agent_id for a in alive_agents]
        self.dialogue_manager.set_speaking_order(speaking_order)

        for i, agent in enumerate(alive_agents):
            if not agent.is_alive:
                continue

            # 设置 Agent 当前轮次
            agent.set_round(self.game_state.round_num)

            # Step 1: Agent 进行独立思考（私有）
            await self._agent_think(agent, context, i)

            # Step 2: 获取该 Agent 可见的对话历史（只看到前面的发言）
            visible_dialogues = self.dialogue_manager.get_dialogue_for_agent(
                agent.agent_id,
                round_num=self.game_state.round_num,
                current_position=i  # 只能看到前面的发言
            )
            dialogue_context = self.dialogue_manager.format_dialogue_for_context(visible_dialogues)

            # Step 3: 获取额外知识和目击信息
            extra_knowledge = self.info_isolation.format_knowledge_for_prompt(agent.agent_id)
            witnessed_events = self.vision_system.get_events_for_agent(agent.agent_id)
            witness_info = self._format_witnessed_events(witnessed_events)

            # Step 4: 构建完整上下文
            full_context = f"{context}\n\n{dialogue_context}\n{extra_knowledge}\n{witness_info}"

            # Step 5: Agent 发言
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: agent.speak(full_context)
            )

            # Step 6: 记录对话
            self.dialogue_manager.add_dialogue(
                speaker_id=agent.agent_id,
                speaker_name=agent.name,
                content=response,
                phase="discussion"
            )

            # Step 7: 广播对话
            await self.broadcast_event("dialogue", {
                "speaker": agent.name,
                "content": response,
                "phase": "discussion",
                "round": self.game_state.round_num
            })

            # 推进发言顺序
            self.dialogue_manager.advance_speaker()
            await asyncio.sleep(0.5)

    async def _agent_think(self, agent, context: str, position: int) -> None:
        """
        Agent 独立思考阶段

        这是实现 Agent 独立性的核心方法。
        思考过程存储在私有记忆中，其他 Agent 无法访问。

        Args:
            agent: Agent 对象
            context: 当前情境
            position: Agent 在发言顺序中的位置
        """
        # 获取当前可见的对话历史
        visible_dialogues = self.dialogue_manager.get_dialogue_for_agent(
            agent.agent_id,
            round_num=self.game_state.round_num,
            current_position=position
        )
        dialogue_context = self.dialogue_manager.format_dialogue_for_context(visible_dialogues)

        # 获取私有观察
        witnessed_events = self.vision_system.get_events_for_agent(agent.agent_id)
        witness_info = self._format_witnessed_events(witnessed_events)

        # 获取额外知识
        extra_knowledge = self.info_isolation.format_knowledge_for_prompt(agent.agent_id)

        # 构建思考上下文
        think_context = f"{context}\n\n{dialogue_context}\n{extra_knowledge}\n{witness_info}"

        # 执行独立思考
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: agent.think(think_context, phase="pre_discussion")
            )
        except Exception as e:
            logger.error(f"Agent {agent.name} 思考失败: {e}")

    def _format_witnessed_events(self, events: List[GameEvent]) -> str:
        """格式化目击事件"""
        if not events:
            return ""

        parts = ["你目击到的事件:"]
        for event in events:
            if event.event_type == EventType.KILL:
                killer = self.agents.get(event.source_agent)
                victim = self.agents.get(event.target_agent)
                if killer and victim:
                    parts.append(f"- 你看到 {killer.name} 杀了 {victim.name}！")
            elif event.event_type == EventType.TASK:
                agent = self.agents.get(event.source_agent)
                if agent:
                    parts.append(f"- 你看到 {agent.name} 在做任务")

        return "\n".join(parts) if len(parts) > 1 else ""

    async def _run_voting(self):
        """
        运行投票 - 基于私有策略

        改进后的流程：
        1. 投票前进行独立思考
        2. 基于私有策略投票
        3. 不受其他 Agent 直接影响
        """
        self.game_state.phase = GamePhase.VOTING

        await self.broadcast_event("phase_changed", {
            "phase": "voting",
            "round": self.game_state.round_num
        })

        context = f"第 {self.game_state.round_num} 轮投票。选择你认为最可疑的人。"

        alive_agents = [self.agents[aid] for aid in self.game_state.alive_players]
        candidates = [agent.name for agent in alive_agents]

        for agent in alive_agents:
            if not agent.is_alive:
                continue

            # Step 1: 投票前的独立思考
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda a=agent: a.think(
                        f"{context}\n候选人：{', '.join(candidates)}",
                        phase="pre_vote"
                    )
                )
            except Exception as e:
                logger.error(f"Agent {agent.name} 投票前思考失败: {e}")

            # Step 2: 获取对话历史和额外知识
            dialogue_history = self.dialogue_manager.get_dialogue_for_agent(
                agent.agent_id,
                round_num=self.game_state.round_num
            )
            dialogue_context = self.dialogue_manager.format_dialogue_for_context(dialogue_history)
            extra_knowledge = self.info_isolation.format_knowledge_for_prompt(agent.agent_id)

            full_context = f"{context}\n\n{dialogue_context}\n{extra_knowledge}"

            # Step 3: Agent 投票
            voted_name = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda a=agent, c=candidates, ctx=full_context: a.vote(c, ctx)
            )

            # 记录投票
            voted_agent = next((a for a in alive_agents if a.name == voted_name), None)
            if voted_agent:
                self.game_state.add_vote(agent.agent_id, voted_agent.agent_id)

                await self.broadcast_event("vote_cast", {
                    "voter": agent.name,
                    "voted": voted_name,
                    "round": self.game_state.round_num
                })

    async def _execute_vote_result(self):
        """执行投票结果"""
        self.game_state.phase = GamePhase.EXECUTION

        voted_agent_id = self.game_state.get_vote_winner()

        if voted_agent_id:
            voted_agent = self.agents[voted_agent_id]
            voted_agent.die()

            self.game_state.alive_players.remove(voted_agent_id)
            self.game_state.dead_players.append(voted_agent_id)

            self.game_state.record_event({
                "type": "execution",
                "round": self.game_state.round_num,
                "player": voted_agent.name,
                "role": voted_agent.role.name
            })

            await self.broadcast_event("player_died", {
                "player_name": voted_agent.name,
                "player": voted_agent.name,
                "role": voted_agent.role.name,
                "camp": voted_agent.role.camp.value,
                "cause": "vote"
            })

            # 广播位置更新
            await self.broadcast_position_update()

            logger.info(f"{voted_agent.name} ({voted_agent.role.name}) 被投票出局")

            # 检查呆呆鸟是否获胜
            if voted_agent.role.role_type == RoleType.DODO:
                self.game_state.result = GameResult.DODO_WIN
                return
        else:
            await self.broadcast_event("vote_tie", {
                "message": "平票，无人出局"
            })

    # ==================== 游戏循环 ====================

    async def run_game_async(self) -> GameResult:
        """
        异步运行完整游戏

        Returns:
            游戏结果
        """
        logger.info("=== 增强版游戏开始 ===")

        # 初始广播地图信息和玩家位置
        await self.broadcast_map_update()
        await self.broadcast_position_update()

        await self.broadcast_event("game_started", {
            "players": [
                {
                    "agent_id": aid,
                    "name": a.name,
                    "is_alive": a.is_alive,
                    "room": self.game_map.get_room_name(
                        self.vision_system.get_agent_position(aid).room_id
                    ) if self.vision_system.get_agent_position(aid) else None
                }
                for aid, a in self.agents.items()
            ]
        })

        while self.game_state.result == GameResult.ONGOING:
            if self.game_state.round_num > self.max_rounds:
                logger.warning("达到最大轮次")
                break

            # 夜晚阶段
            await self.run_night_phase()

            if self.game_state.result != GameResult.ONGOING:
                break

            # 检查游戏状态
            result = self.check_game_over()
            if result != GameResult.ONGOING:
                self.game_state.result = result
                break

            # 白天阶段
            await self.run_day_phase()

            if self.game_state.result != GameResult.ONGOING:
                break

            result = self.check_game_over()
            if result != GameResult.ONGOING:
                self.game_state.result = result
                break

            # 下一轮
            self.game_state.round_num += 1
            self.game_state.reset_round()
            self.vision_system.new_round()

            for agent in self.agents.values():
                agent.reset_for_new_round()

            await asyncio.sleep(1)

        # 游戏结束
        self.game_state.phase = GamePhase.GAME_OVER

        summary = self.get_game_summary()
        await self.broadcast_event("game_over", {
            "result": self.game_state.result.value,
            "summary": summary,
            "players": summary["players"]  # 添加到顶层供前端使用
        })

        logger.info(f"=== 游戏结束: {self.game_state.result.value} ===")
        return self.game_state.result

    def check_game_over(self) -> GameResult:
        """检查游戏是否结束"""
        # 统计各阵营存活人数
        alive_by_camp = {Camp.GOOSE: 0, Camp.DUCK: 0, Camp.NEUTRAL: 0}

        for agent_id in self.game_state.alive_players:
            agent = self.agents[agent_id]
            alive_by_camp[agent.role.camp] += 1

        logger.info(f"检查游戏结束: 鹅={alive_by_camp[Camp.GOOSE]}, 鸭={alive_by_camp[Camp.DUCK]}, 中立={alive_by_camp[Camp.NEUTRAL]}")

        # 检查任务完成度
        completed, total = self.game_map.get_total_task_progress()
        if total > 0 and completed / total >= self.task_completion_win:
            logger.info(f"鹅阵营获胜！（任务完成 {completed}/{total}）")
            return GameResult.GOOSE_WIN

        # 检查鸭阵营是否获胜 - 鸭子数量必须严格大于鹅数量
        if alive_by_camp[Camp.DUCK] > alive_by_camp[Camp.GOOSE]:
            logger.info("鸭阵营获胜！（鸭子数量 > 鹅数量）")
            return GameResult.DUCK_WIN

        # 检查鹅阵营是否获胜
        if alive_by_camp[Camp.DUCK] == 0:
            logger.info("鹅阵营获胜！（所有鸭子被消灭）")
            return GameResult.GOOSE_WIN

        return GameResult.ONGOING

    def get_game_summary(self) -> Dict[str, Any]:
        """获取游戏总结"""
        completed, total = self.game_map.get_total_task_progress()

        return {
            "result": self.game_state.result.value,
            "rounds": self.game_state.round_num,
            "task_progress": {"completed": completed, "total": total},
            "players": [
                {
                    "agent_id": aid,
                    "name": a.name,
                    "role": a.role.name,
                    "camp": a.role.camp.value,
                    "is_alive": a.is_alive,
                    "status": "存活" if a.is_alive else "死亡"
                }
                for aid, a in self.agents.items()
            ],
            "history": self.game_state.history
        }

    def get_state(self) -> Dict[str, Any]:
        """获取当前游戏状态"""
        completed, total = self.game_map.get_total_task_progress()

        return {
            "phase": self.game_state.phase.value,
            "round": self.game_state.round_num,
            "result": self.game_state.result.value,
            "task_progress": {"completed": completed, "total": total},
            "players": [
                {
                    "agent_id": aid,
                    "name": self.agents[aid].name,
                    "is_alive": self.agents[aid].is_alive,
                    "room": self.game_map.get_room_name(
                        self.vision_system.get_agent_position(aid).room_id
                    ) if self.vision_system.get_agent_position(aid) else "未知"
                }
                for aid in self.agents
            ]
        }
