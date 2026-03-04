"""
Agent基础类
"""
from typing import Dict, Any, Optional
import logging
from ..llm import BaseLLM
from ..roles import Role, RoleType
from .memory import AgentMemory

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

        # 初始化记忆系统
        memory_config = memory_config or {}
        self.memory = AgentMemory(max_history=memory_config.get('max_history', 50))

        # 添加角色系统提示
        self.memory.add_system_message(self.role.get_system_prompt())

        # Agent状态
        self.is_alive = True
        self.has_spoken = False  # 本轮是否已发言

        logger.info(f"Agent初始化: {name} ({role.name})")

    def speak(self, context: str, **kwargs) -> str:
        """
        Agent发言

        Args:
            context: 发言上下文（如讨论主题）
            **kwargs: 其他参数

        Returns:
            Agent的发言内容
        """
        if not self.is_alive:
            return f"{self.name}已经死亡，无法发言。"

        # 构建提示
        prompt = f"""当前情境：
{context}

请根据你的角色和目标，发表你的看法（50-100字）。
注意：
1. 保持角色一致性
2. 发言要简洁有力
3. 不要暴露你不想让别人知道的信息
"""

        # 添加到记忆
        self.memory.add_user_message(prompt)

        # 调用LLM
        messages = self.memory.get_messages_for_llm()
        response = self.llm.chat(messages, **kwargs)

        # 保存回复到记忆
        self.memory.add_assistant_message(response)
        self.has_spoken = True

        logger.info(f"{self.name}发言: {response[:100]}...")
        return response

    def vote(self, candidates: list, context: str = "", **kwargs) -> str:
        """
        Agent投票

        Args:
            candidates: 候选人列表
            context: 投票上下文
            **kwargs: 其他参数

        Returns:
            投票的候选人名称
        """
        if not self.is_alive:
            return ""

        # 构建提示
        candidates_text = "、".join(candidates)
        prompt = f"""投票阶段：
候选人：{candidates_text}

{context}

请根据你的判断，选择一个你认为最可疑的人投票。
只需回复候选人名字，不要有其他内容。
"""

        # 添加到记忆
        self.memory.add_user_message(prompt)

        # 调用LLM
        messages = self.memory.get_messages_for_llm()
        response = self.llm.chat(messages, **kwargs).strip()

        # 验证投票是否有效
        for candidate in candidates:
            if candidate in response:
                logger.info(f"{self.name}投票给: {candidate}")
                return candidate

        # 如果没有匹配到，随机选择
        import random
        voted = random.choice(candidates)
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

    def die(self):
        """Agent死亡"""
        self.is_alive = False
        logger.info(f"{self.name}已死亡")

    def __repr__(self):
        status = "存活" if self.is_alive else "死亡"
        return f"Agent({self.name}, {self.role.name}, {status})"


__all__ = ['Agent']
