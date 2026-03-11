"""
游戏服务 - 封装 GameEngine，提供异步接口
"""
import asyncio
import logging
import uuid
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

import sys
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.game.game_engine import GameEngine
from src.game.game_state import GamePhase, GameResult
from src.agents import Agent
from .event_manager import event_manager

logger = logging.getLogger(__name__)


class GameService:
    """
    游戏服务 - 封装 GameEngine，提供异步接口和事件广播
    """

    # 类级别存储所有游戏实例
    _instances: Dict[str, 'GameService'] = {}

    def __init__(self, game_id: str, config: Optional[Dict[str, Any]] = None):
        """
        初始化游戏服务

        Args:
            game_id: 游戏 ID
            config: 游戏配置
        """
        self.game_id = game_id
        self.engine = GameEngine()
        if config:
            self.engine.config = config

        self._is_running = False
        self._is_paused = False
        self._task: Optional[asyncio.Task] = None
        self._delay_seconds = 1.0  # 事件之间的延迟

        # 对话缓存（用于前端显示）
        self._dialogues: List[Dict[str, Any]] = []

    @classmethod
    def create_game(
        cls,
        player_names: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> 'GameService':
        """
        创建新游戏

        Args:
            player_names: 玩家名称列表
            config: 游戏配置

        Returns:
            GameService 实例
        """
        game_id = str(uuid.uuid4())[:8]  # 使用短 ID
        instance = cls(game_id, config)
        cls._instances[game_id] = instance

        # 设置游戏
        instance.engine.setup_game(player_names)

        logger.info(f"创建游戏: {game_id}")
        return instance

    @classmethod
    def get_game(cls, game_id: str) -> Optional['GameService']:
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
        """
        异步启动游戏

        Args:
            delay_seconds: 事件之间的延迟秒数
        """
        if self._is_running:
            return

        self._is_running = True
        self._is_paused = False
        self._delay_seconds = delay_seconds
        self._task = asyncio.create_task(self._run_game_loop())

        logger.info(f"游戏启动: {self.game_id}")

    async def pause_game(self):
        """暂停游戏"""
        self._is_paused = True
        logger.info(f"游戏暂停: {self.game_id}")

    async def resume_game(self):
        """恢复游戏"""
        self._is_paused = False
        logger.info(f"游戏恢复: {self.game_id}")

    def get_state(self, reveal_roles: bool = False) -> Dict[str, Any]:
        """
        获取当前游戏状态

        Args:
            reveal_roles: 是否揭示角色

        Returns:
            游戏状态字典
        """
        state = self.engine.game_state.to_dict()
        state["game_id"] = self.game_id
        state["players"] = self._get_players_info(reveal_roles)
        state["current_dialogues"] = self._dialogues
        return state

    def get_summary(self) -> Dict[str, Any]:
        """获取游戏总结"""
        return self.engine.get_game_summary()

    def _get_players_info(self, reveal_roles: bool = False) -> List[Dict[str, Any]]:
        """
        获取玩家信息

        Args:
            reveal_roles: 是否揭示角色

        Returns:
            玩家信息列表
        """
        players = []
        for agent_id, agent in self.engine.agents.items():
            info = {
                "agent_id": agent_id,
                "name": agent.name,
                "is_alive": agent.is_alive,
            }
            # 游戏结束后或明确要求时揭示角色
            if reveal_roles or self.engine.game_state.result != GameResult.ONGOING:
                info["role"] = agent.role.name
                info["camp"] = agent.role.camp.value
            players.append(info)
        return players

    async def _run_game_loop(self):
        """异步游戏主循环"""
        try:
            # 广播游戏开始
            await event_manager.broadcast(
                self.game_id,
                "game_started",
                {
                    "players": self._get_players_info(reveal_roles=False),
                    "message": "游戏开始！"
                }
            )
            await asyncio.sleep(self._delay_seconds)

            # 游戏主循环
            while self.engine.game_state.result == GameResult.ONGOING:
                # 检查暂停
                while self._is_paused:
                    await asyncio.sleep(0.5)

                # 检查是否超过最大轮次
                if self.engine.game_state.round_num > self.engine.max_rounds:
                    logger.warning("达到最大轮次，游戏结束")
                    break

                # 讨论阶段
                await self._run_discussion_phase()

                # 投票阶段
                await self._run_voting_phase()

                # 执行阶段
                await self._run_execution_phase()

                # 检查游戏是否结束
                self.engine.game_state.result = self.engine.check_game_over()

                if self.engine.game_state.result != GameResult.ONGOING:
                    break

                # 准备下一轮
                self.engine.game_state.round_num += 1
                self.engine.game_state.reset_round()

                # 重置Agent状态
                for agent in self.engine.agents.values():
                    agent.reset_for_new_round()

            # 游戏结束
            await self._broadcast_game_over()

        except asyncio.CancelledError:
            logger.info(f"游戏任务被取消: {self.game_id}")
        except Exception as e:
            logger.error(f"游戏运行错误: {e}", exc_info=True)
            await event_manager.broadcast(
                self.game_id,
                "error",
                {"message": f"游戏运行错误: {str(e)}"}
            )
        finally:
            self._is_running = False

    async def _run_discussion_phase(self):
        """异步执行讨论阶段"""
        # 广播阶段变化
        await event_manager.broadcast(
            self.game_id,
            "phase_changed",
            {
                "phase": "discussion",
                "round": self.engine.game_state.round_num,
                "message": f"第 {self.engine.game_state.round_num} 轮讨论阶段开始"
            }
        )

        self.engine.game_state.phase = GamePhase.DISCUSSION
        self.engine.dialogue_manager.set_phase("discussion")

        # 通知所有Agent进入讨论阶段
        context = f"第 {self.engine.game_state.round_num} 轮讨论开始。请发表你的看法。"

        # 每个存活的Agent轮流发言
        import random
        alive_agents = [self.engine.agents[aid] for aid in self.engine.game_state.alive_players]
        random.shuffle(alive_agents)

        for agent in alive_agents:
            if agent.is_alive and self._is_running:
                # 检查暂停
                while self._is_paused:
                    await asyncio.sleep(0.5)

                # 构建上下文
                dialogue_history = self.engine.dialogue_manager.get_dialogue_for_agent(
                    agent.agent_id,
                    round_num=self.engine.game_state.round_num,
                    phase="discussion"
                )
                dialogue_context = self.engine.dialogue_manager.format_dialogue_for_context(dialogue_history)

                extra_knowledge = self.engine.info_isolation.format_knowledge_for_prompt(agent.agent_id)
                full_context = f"{context}\n\n{dialogue_context}\n{extra_knowledge}"

                # Agent发言（在线程池中运行以避免阻塞）
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: agent.speak(full_context)
                )

                # 记录对话
                self.engine.dialogue_manager.add_dialogue(
                    speaker_id=agent.agent_id,
                    speaker_name=agent.name,
                    content=response,
                    phase="discussion"
                )

                # 缓存对话
                self._dialogues.append({
                    "speaker": agent.name,
                    "content": response,
                    "phase": "discussion",
                    "round": self.engine.game_state.round_num
                })

                # 广播对话事件
                await event_manager.broadcast(
                    self.game_id,
                    "dialogue",
                    {
                        "speaker": agent.name,
                        "content": response,
                        "phase": "discussion",
                        "round": self.engine.game_state.round_num
                    }
                )

                # 其他Agent观察
                for other_agent in self.engine.agents.values():
                    if other_agent.agent_id != agent.agent_id:
                        other_agent.observe(f"{agent.name}说: {response}")

                await asyncio.sleep(self._delay_seconds)

    async def _run_voting_phase(self):
        """异步执行投票阶段"""
        await event_manager.broadcast(
            self.game_id,
            "phase_changed",
            {
                "phase": "voting",
                "round": self.engine.game_state.round_num,
                "message": f"第 {self.engine.game_state.round_num} 轮投票阶段开始"
            }
        )

        self.engine.game_state.phase = GamePhase.VOTING
        self.engine.dialogue_manager.set_phase("voting")

        context = f"第 {self.engine.game_state.round_num} 轮投票开始。请选择你认为最可疑的人。"

        alive_agents = [self.engine.agents[aid] for aid in self.engine.game_state.alive_players]
        candidates = [agent.name for agent in alive_agents]

        for agent in alive_agents:
            if agent.is_alive and self._is_running:
                while self._is_paused:
                    await asyncio.sleep(0.5)

                dialogue_history = self.engine.dialogue_manager.get_dialogue_for_agent(
                    agent.agent_id,
                    round_num=self.engine.game_state.round_num
                )
                dialogue_context = self.engine.dialogue_manager.format_dialogue_for_context(dialogue_history)
                extra_knowledge = self.engine.info_isolation.format_knowledge_for_prompt(agent.agent_id)
                full_context = f"{context}\n\n{dialogue_context}\n{extra_knowledge}"

                # Agent投票
                voted_name = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: agent.vote(candidates, full_context)
                )

                voted_agent = next((a for a in alive_agents if a.name == voted_name), None)
                if voted_agent:
                    self.engine.game_state.add_vote(agent.agent_id, voted_agent.agent_id)

                    self.engine.dialogue_manager.add_dialogue(
                        speaker_id=agent.agent_id,
                        speaker_name=agent.name,
                        content=f"我投票给 {voted_name}",
                        phase="voting"
                    )

                    # 广播投票事件
                    await event_manager.broadcast(
                        self.game_id,
                        "vote_cast",
                        {
                            "voter": agent.name,
                            "voted": voted_name,
                            "round": self.engine.game_state.round_num
                        }
                    )

                await asyncio.sleep(self._delay_seconds)

    async def _run_execution_phase(self):
        """异步执行处决阶段"""
        await event_manager.broadcast(
            self.game_id,
            "phase_changed",
            {
                "phase": "execution",
                "round": self.engine.game_state.round_num,
                "message": f"第 {self.engine.game_state.round_num} 轮处决阶段"
            }
        )

        self.engine.game_state.phase = GamePhase.EXECUTION

        voted_agent_id = self.engine.game_state.get_vote_winner()

        if voted_agent_id:
            voted_agent = self.engine.agents[voted_agent_id]
            voted_agent.die()

            self.engine.game_state.alive_players.remove(voted_agent_id)
            self.engine.game_state.dead_players.append(voted_agent_id)

            event = {
                "type": "execution",
                "round": self.engine.game_state.round_num,
                "player": voted_agent.name,
                "role": voted_agent.role.name,
                "votes": self.engine.game_state.vote_results.get(voted_agent_id, 0)
            }
            self.engine.game_state.record_event(event)

            # 广播死亡事件
            await event_manager.broadcast(
                self.game_id,
                "player_died",
                {
                    "player_name": voted_agent.name,
                    "role": voted_agent.role.name,
                    "camp": voted_agent.role.camp.value,
                    "votes": self.engine.game_state.vote_results.get(voted_agent_id, 0),
                    "round": self.engine.game_state.round_num
                }
            )

            # 通知所有Agent
            for agent in self.engine.agents.values():
                agent.observe(f"投票结果：{voted_agent.name} 被投票出局，身份是 {voted_agent.role.name}")
        else:
            await event_manager.broadcast(
                self.game_id,
                "phase_changed",
                {
                    "phase": "execution",
                    "round": self.engine.game_state.round_num,
                    "message": "平票，本轮无人出局"
                }
            )

        await asyncio.sleep(self._delay_seconds)

    async def _broadcast_game_over(self):
        """广播游戏结束"""
        self.engine.game_state.phase = GamePhase.GAME_OVER

        await event_manager.broadcast(
            self.game_id,
            "game_over",
            {
                "result": self.engine.game_state.result.value,
                "summary": self.engine.get_game_summary(),
                "players": self._get_players_info(reveal_roles=True)
            }
        )

        logger.info(f"游戏结束: {self.game_id}, 结果: {self.engine.game_state.result.value}")
