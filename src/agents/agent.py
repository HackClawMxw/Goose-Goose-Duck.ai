"""
Agent基础类 - 支持独立思考机制

每个 Agent 都有：
- 公开记忆：记录对话和游戏事件
- 私有记忆：存储独立思考和策略（其他 Agent 不可见）
- 策略模块：基于角色目标形成独立策略
"""
import time
from typing import Dict, Any, Optional, List, Set
import logging
import re

from ..llm import BaseLLM
from ..roles import Role, RoleType
from .memory import AgentMemory
from .private_memory import PrivateMemory, PrivateThought
from .strategy_module import StrategyModule

logger = logging.getLogger(__name__)


class Agent:
    """Agent基础类"""

    def __init__(
        self,
        agent_id: str,
        name: str,
        role: Role,
        llm: BaseLLM,
        memory_config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化Agent

        Args:
            agent_id: Agent唯一ID
            name: Agent名称
            role: 角色对象
            llm: LLM实例
            memory_config: 记忆配置
        """
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.llm = llm

        # 初始化公开记忆系统（记录对话和游戏事件）
        memory_config = memory_config or {}
        self.memory = AgentMemory(max_history=memory_config.get('max_history', 50))

        # 添加角色系统提示
        self.memory.add_system_message(self.role.get_system_prompt())

        # 初始化私有记忆系统（存储独立思考，其他 Agent 不可见）
        self.private_memory = PrivateMemory(max_thoughts=100, self_name=name)

        # 初始化策略模块
        self.strategy_module = StrategyModule(self.role, self.llm)

        # Agent状态
        self.is_alive = True
        self.has_spoken = False  # 本轮是否已发言
        self._current_round = 1  # 当前轮次

        logger.info(f"Agent初始化: {name} ({role.name})")

    def think(self, context: str, phase: str = "pre_discussion", known_players: List[str] = None) -> str:
        """
        Agent 独立思考过程

        这是实现 Agent 独立性的核心方法。
        思考过程存储在私有记忆中，其他 Agent 无法访问。

        Args:
            context: 当前情境
            phase: 思考阶段 (pre_discussion, during_discussion, pre_vote)
            known_players: 已知的其他玩家名称列表（用于怀疑对象提取）

        Returns:
            思考结果（仅存储在私有记忆中）
        """
        if not self.is_alive:
            return ""

        # 获取策略指导
        strategy_prompt = self.strategy_module.get_strategy_prompt()

        # 获取私有记忆上下文
        recent_thoughts = self.private_memory.get_recent_thoughts_str(3)
        suspicion_summary = self.private_memory.get_suspicion_summary()

        # 构建思考提示
        think_prompt = f"""【独立思考时间 - 只有你能看到】

当前情境：
{context}

你的策略指导：
{strategy_prompt}

你之前的思考：
{recent_thoughts}

你的怀疑列表：
{suspicion_summary}

请进行独立思考，分析当前局势：
1. 你认为谁最可疑？为什么？
2. 你接下来应该如何行动？
3. 你的发言策略是什么？

注意：这是你的私有思考，不会被其他玩家看到。请诚实分析。
"""

        # 调用 LLM 进行思考
        try:
            response = self.llm.chat_with_system(
                self.role.get_strategy_prompt(),
                think_prompt
            )
        except Exception as e:
            logger.error(f"{self.name} 思考失败: {e}")
            response = "我需要保持警惕，观察其他人的行为。"

        # 存储到私有记忆
        thought = PrivateThought(
            round_num=self._current_round,
            phase=phase,
            thought_type="analysis",
            content=response,
            timestamp=time.time()
        )
        self.private_memory.add_thought(thought)

        # 从思考中提取怀疑对象（传入已知玩家列表，排除自己）
        if known_players:
            # 确保不包含自己
            other_players = [p for p in known_players if p != self.name]
            self._update_suspicions_from_thought(response, other_players)

        # 更新策略
        self.strategy_module.formulate_strategy(
            context,
            self.private_memory
        )

        logger.debug(f"{self.name} 完成独立思考 ({phase})")
        return response

    def _update_suspicions_from_thought(self, thought_content: str, known_players: List[str] = None) -> None:
        """
        从思考内容中提取怀疑对象

        Args:
            thought_content: 思考内容
            known_players: 已知的其他玩家名称列表（不包括自己）
        """
        if known_players is None:
            # 如果没有传入玩家列表，无法提取
            return

        # 怀疑关键词
        suspicion_keywords = ["可疑", "怀疑", "可能是", "应该是", "像是", "嫌疑", "不对劲"]
        avoid_keywords = ["不像", "不是", "应该不是", "不太像", "排除"]

        lines = thought_content.split('\n')
        for line in lines:
            # 检查是否有怀疑关键词
            has_suspicion = any(kw in line for kw in suspicion_keywords)
            has_avoid = any(kw in line for kw in avoid_keywords)

            if has_suspicion and not has_avoid:
                # 提取提到的其他玩家名称（排除自己）
                for player_name in known_players:
                    if player_name in line and player_name != self.name:
                        # 计算怀疑分数（简单实现：基于关键词强度）
                        score = 0.5
                        if "非常" in line or "很" in line:
                            score = 0.7
                        if "确定" in line or "肯定" in line:
                            score = 0.9

                        self.update_suspicion(
                            agent_id=player_name,  # 简化：用名称作为ID
                            agent_name=player_name,
                            score=score,
                            reason=f"从思考中发现: {line[:50]}"
                        )
                        logger.debug(f"{self.name} 怀疑 {player_name}: {score:.2f}")

    def observe_private(self, event: str, event_type: str = "observation") -> None:
        """
        记录私有观察（其他 Agent 不可见）

        Args:
            event: 观察到的事件
            event_type: 事件类型
        """
        thought = PrivateThought(
            round_num=self._current_round,
            phase="observation",
            thought_type=event_type,
            content=event,
            timestamp=time.time()
        )
        self.private_memory.add_thought(thought)
        self.private_memory.add_observation(event)
        logger.debug(f"{self.name} 私有观察: {event[:50]}...")

    def update_suspicion(
        self,
        agent_id: str,
        agent_name: str,
        score: float,
        reason: str
    ) -> None:
        """
        更新对某个玩家的怀疑度

        Args:
            agent_id: 玩家 ID
            agent_name: 玩家名称
            score: 怀疑分数 (0-1)
            reason: 怀疑原因
        """
        # 【关键修复】绝对不能怀疑自己
        if agent_id == self.agent_id or agent_name == self.name:
            logger.warning(f"{self.name} 尝试怀疑自己，已阻止")
            return

        self.private_memory.update_suspicion(
            agent_id, agent_name, score, reason, self._current_round
        )

    def speak(self, context: str, **kwargs) -> str:
        """
        Agent发言 - 基于策略而非直接反应

        改进后的发言方法：
        1. 考虑私有策略
        2. 参考怀疑列表
        3. 保持角色一致性

        Args:
            context: 发言上下文（如讨论主题）
            **kwargs: 其他参数

        Returns:
            Agent的发言内容
        """
        if not self.is_alive:
            return f"{self.name}已经死亡，无法发言。"

        # 获取策略指导
        strategy_context = self.private_memory.get_strategy_context()
        suspicion_summary = self.private_memory.get_suspicion_summary()

        # 构建发言提示（包含策略指导）
        prompt = f"""【发言阶段】

当前情境：
{context}

你的策略指导：
{strategy_context}

你的怀疑分析（只有你知道）：
{suspicion_summary}

请根据你的策略发表看法（50-100字）。

注意：
1. 发言要支持你的角色目标
2. 不要暴露你不想让别人知道的信息（如你是鸭子）
3. 保持角色一致性
4. 根据你的策略选择性分享信息
5. 如果你有怀疑对象，可以适当表达，但要有依据
"""

        # 添加到公开记忆
        self.memory.add_user_message(prompt)

        # 调用LLM
        messages = self.memory.get_messages_for_llm()
        response = self.llm.chat(messages, **kwargs)

        # 保存回复到公开记忆
        self.memory.add_assistant_message(response)
        self.has_spoken = True

        logger.info(f"{self.name}发言: {response[:100]}...")
        return response

    def vote(self, candidates: list, context: str = "", **kwargs) -> str:
        """
        Agent投票 - 基于私有策略

        改进后的投票方法：
        1. 排除自己（不能投给自己）
        2. 优先投票给怀疑列表中的人
        3. 考虑角色目标
        4. 不受其他 Agent 直接影响

        Args:
            candidates: 候选人列表
            context: 投票上下文
            **kwargs: 其他参数

        Returns:
            投票的候选人名称
        """
        if not self.is_alive:
            return ""

        # 【关键修复】排除自己 - 不能投给自己
        valid_candidates = [c for c in candidates if c != self.name]
        if not valid_candidates:
            logger.warning(f"{self.name} 没有有效的投票候选人")
            return ""

        # 获取策略推荐的投票目标
        recommended = self.strategy_module.get_recommended_vote_target(valid_candidates)

        # 获取怀疑列表
        suspicion_summary = self.private_memory.get_suspicion_summary()
        top_suspects = self.private_memory.get_top_suspects(3)

        # 【实现】检查怀疑对象是否在有效候选人中
        for suspect_id in top_suspects:
            # suspect_id 可能是 agent_id 或 name（简化处理）
            if suspect_id in valid_candidates:
                # 如果怀疑对象在候选人中，记录日志
                logger.info(f"{self.name} 发现怀疑对象 {suspect_id} 在候选人中")

        # 构建投票提示
        candidates_text = "、".join(valid_candidates)
        prompt = f"""【投票阶段】

候选人：{candidates_text}

{context}

你的怀疑分析（只有你知道）：
{suspicion_summary}

你的策略推荐投票对象：{recommended if recommended else '无特定推荐'}

【重要规则】
- 你不能投票给自己（{self.name}）
- 请只从候选人列表中选择一人

请根据你的判断投票。
只需回复候选人名字，不要有其他内容。
"""

        # 添加到记忆
        self.memory.add_user_message(prompt)

        # 调用LLM
        messages = self.memory.get_messages_for_llm()
        response = self.llm.chat(messages, **kwargs).strip()

        # 验证投票是否有效（排除自己）
        for candidate in valid_candidates:
            if candidate in response:
                logger.info(f"{self.name}投票给: {candidate}")
                return candidate

        # 如果 LLM 没有返回有效候选人，使用策略推荐
        if recommended and recommended in valid_candidates:
            logger.info(f"{self.name}使用策略推荐投票: {recommended}")
            return recommended

        # 【实现】如果有怀疑对象在有效候选人中，优先投票
        for suspect_id in top_suspects:
            if suspect_id in valid_candidates:
                logger.info(f"{self.name}根据怀疑列表投票: {suspect_id}")
                return suspect_id

        # 最后随机选择（从有效候选人中）
        import random
        voted = random.choice(valid_candidates)
        logger.warning(f"{self.name}的投票无效，随机选择: {voted}")
        return voted

    def observe(self, event: str, metadata: Dict[str, Any] = None):
        """
        观察游戏事件

        Args:
            event: 事件描述
            metadata: 事件元数据
        """
        self.memory.add_game_message(event, metadata)
        logger.debug(f"{self.name}观察到事件: {event[:50]}...")

    def reset_for_new_round(self):
        """重置新一轮状态"""
        self.has_spoken = False

    def set_round(self, round_num: int) -> None:
        """
        设置当前轮次

        Args:
            round_num: 轮次号
        """
        self._current_round = round_num

    def die(self):
        """Agent死亡"""
        self.is_alive = False
        logger.info(f"{self.name}已死亡")

    def __repr__(self):
        status = "存活" if self.is_alive else "死亡"
        return f"Agent({self.name}, {self.role.name}, {status})"


__all__ = ['Agent']
