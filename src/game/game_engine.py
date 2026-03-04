"""
游戏引擎 - 控制整个游戏流程
"""
from typing import List, Dict, Any, Optional
import logging
import random
import yaml
from pathlib import Path

from ..llm import LLMFactory, BaseLLM
from ..agents import Agent
from ..roles import Role, RoleType, Camp
from .game_state import GameState, GamePhase, GameResult
from .dialogue_manager import DialogueManager
from .information_isolation import InformationIsolation

logger = logging.getLogger(__name__)


class GameEngine:
    """游戏引擎"""

    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化游戏引擎

        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        self.config = self._load_config(config_path)

        # 初始化LLM
        self.llm = LLMFactory.create_llm(self.config['llm'])

        # 初始化游戏组件
        self.agents: Dict[str, Agent] = {}
        self.game_state = GameState()
        self.dialogue_manager = DialogueManager()
        self.info_isolation = InformationIsolation()

        # 游戏配置
        self.max_rounds = self.config['game']['discussion']['max_rounds']
        self.max_messages_per_round = self.config['game']['discussion']['max_messages_per_round']

        logger.info("游戏引擎初始化完成")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        config_file = Path(config_path)
        if not config_file.exists():
            logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
            return self._get_default_config()

        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            logger.info(f"配置文件加载成功: {config_path}")
            return config

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
                'discussion': {
                    'max_rounds': 3,
                    'max_messages_per_round': 10
                }
            },
            'agent': {
                'memory': {
                    'max_history': 50
                }
            }
        }

    def setup_game(self, player_names: Optional[List[str]] = None):
        """
        设置游戏

        Args:
            player_names: 玩家名称列表（可选）
        """
        logger.info("开始设置游戏...")

        # 获取角色配置
        roles_config = self.config['game']['roles']

        # 创建角色列表
        roles = []
        for camp_name, role_list in roles_config.items():
            for role_info in role_list:
                count = role_info['count']
                # 根据阵营名称映射到RoleType
                if camp_name == 'goose':
                    role_type = RoleType.GOOSE
                elif camp_name == 'duck':
                    role_type = RoleType.DUCK
                else:
                    role_type = RoleType.DODO

                for _ in range(count):
                    roles.append(Role.from_type(role_type))

        # 随机打乱角色
        random.shuffle(roles)

        # 生成玩家名称
        if player_names is None:
            player_names = [f"玩家{i + 1}" for i in range(len(roles))]

        # 创建Agent
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

        # 分享阵营信息（鸭阵营互相认识）
        self.info_isolation.share_camp_information()

        logger.info(f"游戏设置完成，共 {len(self.agents)} 名玩家")
        logger.info(f"角色分配: {[(a.name, a.role.name) for a in self.agents.values()]}")

    def start_discussion_phase(self):
        """开始讨论阶段"""
        logger.info(f"=== 第 {self.game_state.round_num} 轮 - 讨论阶段 ===")
        self.game_state.phase = GamePhase.DISCUSSION
        self.dialogue_manager.set_phase("discussion")

        # 通知所有Agent进入讨论阶段
        context = f"第 {self.game_state.round_num} 轮讨论开始。请发表你的看法。"

        # 每个存活的Agent轮流发言
        alive_agents = [self.agents[aid] for aid in self.game_state.alive_players]
        random.shuffle(alive_agents)  # 随机顺序

        for agent in alive_agents:
            if agent.is_alive:
                # 构建上下文
                dialogue_history = self.dialogue_manager.get_dialogue_for_agent(
                    agent.agent_id,
                    round_num=self.game_state.round_num,
                    phase="discussion"
                )
                dialogue_context = self.dialogue_manager.format_dialogue_for_context(dialogue_history)

                # 添加额外知识
                extra_knowledge = self.info_isolation.format_knowledge_for_prompt(agent.agent_id)

                full_context = f"{context}\n\n{dialogue_context}\n{extra_knowledge}"

                # Agent发言
                response = agent.speak(full_context)

                # 记录对话
                self.dialogue_manager.add_dialogue(
                    speaker_id=agent.agent_id,
                    speaker_name=agent.name,
                    content=response,
                    phase="discussion"
                )

                # 其他Agent观察到这次发言
                for other_agent in self.agents.values():
                    if other_agent.agent_id != agent.agent_id:
                        other_agent.observe(f"{agent.name}说: {response}")

    def start_voting_phase(self):
        """开始投票阶段"""
        logger.info(f"=== 第 {self.game_state.round_num} 轮 - 投票阶段 ===")
        self.game_state.phase = GamePhase.VOTING
        self.dialogue_manager.set_phase("voting")

        # 通知所有Agent进入投票阶段
        context = f"第 {self.game_state.round_num} 轮投票开始。请选择你认为最可疑的人。"

        # 获取存活玩家列表
        alive_agents = [self.agents[aid] for aid in self.game_state.alive_players]
        candidates = [agent.name for agent in alive_agents]

        # 每个存活的Agent投票
        for agent in alive_agents:
            if agent.is_alive:
                # 构建上下文
                dialogue_history = self.dialogue_manager.get_dialogue_for_agent(
                    agent.agent_id,
                    round_num=self.game_state.round_num
                )
                dialogue_context = self.dialogue_manager.format_dialogue_for_context(dialogue_history)

                # 添加额外知识
                extra_knowledge = self.info_isolation.format_knowledge_for_prompt(agent.agent_id)

                full_context = f"{context}\n\n{dialogue_context}\n{extra_knowledge}"

                # Agent投票
                voted_name = agent.vote(candidates, full_context)

                # 找到被投票的Agent ID
                voted_agent = next((a for a in alive_agents if a.name == voted_name), None)
                if voted_agent:
                    self.game_state.add_vote(agent.agent_id, voted_agent.agent_id)

                    # 记录投票
                    self.dialogue_manager.add_dialogue(
                        speaker_id=agent.agent_id,
                        speaker_name=agent.name,
                        content=f"我投票给 {voted_name}",
                        phase="voting"
                    )

    def execute_voting_result(self) -> Optional[str]:
        """执行投票结果"""
        logger.info(f"=== 第 {self.game_state.round_num} 轮 - 处决阶段 ===")
        self.game_state.phase = GamePhase.EXECUTION

        # 获取投票结果
        voted_agent_id = self.game_state.get_vote_winner()

        if voted_agent_id:
            voted_agent = self.agents[voted_agent_id]
            voted_agent.die()

            # 更新游戏状态
            self.game_state.alive_players.remove(voted_agent_id)
            self.game_state.dead_players.append(voted_agent_id)

            # 记录事件
            event = {
                "type": "execution",
                "round": self.game_state.round_num,
                "player": voted_agent.name,
                "role": voted_agent.role.name,
                "votes": self.game_state.vote_results.get(voted_agent_id, 0)
            }
            self.game_state.record_event(event)

            logger.info(f"玩家 {voted_agent.name} ({voted_agent.role.name}) 被投票出局")

            # 通知所有Agent
            for agent in self.agents.values():
                agent.observe(f"投票结果：{voted_agent.name} 被投票出局，身份是 {voted_agent.role.name}")

            return voted_agent.name
        else:
            logger.warning("平票，无人出局")
            for agent in self.agents.values():
                agent.observe("投票结果：平票，本轮无人出局")
            return None

    def check_game_over(self) -> GameResult:
        """检查游戏是否结束"""
        # 统计各阵营存活人数
        alive_by_camp = {camp: 0 for camp in Camp}

        for agent_id in self.game_state.alive_players:
            agent = self.agents[agent_id]
            alive_by_camp[agent.role.camp] += 1

        logger.debug(f"各阵营存活人数: {alive_by_camp}")

        # 检查呆呆鸟是否获胜（被投票出局）
        for event in self.game_state.history:
            if event.get("type") == "execution":
                executed_agent = next(
                    (a for a in self.agents.values() if a.name == event["player"]),
                    None
                )
                if executed_agent and executed_agent.role.role_type == RoleType.DODO:
                    logger.info("呆呆鸟获胜！（被投票出局）")
                    return GameResult.DODO_WIN

        # 检查鸭阵营是否获胜（鸭子数量 >= 鹅数量）
        if alive_by_camp[Camp.DUCK] >= alive_by_camp[Camp.GOOSE]:
            logger.info("鸭阵营获胜！（鸭子数量 >= 鹅数量）")
            return GameResult.DUCK_WIN

        # 检查鹅阵营是否获胜（所有鸭子被消灭）
        if alive_by_camp[Camp.DUCK] == 0:
            logger.info("鹅阵营获胜！（所有鸭子被消灭）")
            return GameResult.GOOSE_WIN

        return GameResult.ONGOING

    def run_game(self) -> GameResult:
        """
        运行完整游戏

        Returns:
            游戏结果
        """
        logger.info("=== 游戏开始 ===")

        # 游戏主循环
        while self.game_state.result == GameResult.ONGOING:
            # 检查是否超过最大轮次
            if self.game_state.round_num > self.max_rounds:
                logger.warning("达到最大轮次，游戏结束")
                break

            # 讨论阶段
            self.start_discussion_phase()

            # 投票阶段
            self.start_voting_phase()

            # 执行投票结果
            self.execute_voting_result()

            # 检查游戏是否结束
            self.game_state.result = self.check_game_over()

            if self.game_state.result != GameResult.ONGOING:
                break

            # 准备下一轮
            self.game_state.round_num += 1
            self.game_state.reset_round()

            # 重置Agent状态
            for agent in self.agents.values():
                agent.reset_for_new_round()

        # 游戏结束
        self.game_state.phase = GamePhase.GAME_OVER
        logger.info(f"=== 游戏结束: {self.game_state.result.value} ===")

        return self.game_state.result

    def get_game_summary(self) -> Dict[str, Any]:
        """获取游戏总结"""
        summary = {
            "result": self.game_state.result.value,
            "rounds": self.game_state.round_num,
            "players": [],
            "history": self.game_state.history
        }

        for agent_id, agent in self.agents.items():
            player_info = {
                "name": agent.name,
                "role": agent.role.name,
                "camp": agent.role.camp.value,
                "status": "存活" if agent.is_alive else "死亡"
            }
            summary["players"].append(player_info)

        return summary

    def __repr__(self):
        return f"GameEngine(agents={len(self.agents)}, state={self.game_state})"
