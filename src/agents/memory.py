"""
Agent记忆系统
"""
from typing import List, Dict, Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """消息类"""
    role: str  # "system", "user", "assistant", "game"
    content: str
    agent_id: str = ""
    timestamp: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, str]:
        """转换为字典格式（用于LLM调用）"""
        return {
            "role": self.role if self.role in ["system", "user", "assistant"] else "user",
            "content": self.content
        }


class AgentMemory:
    """Agent记忆系统"""

    def __init__(self, max_history: int = 50):
        """
        初始化记忆系统

        Args:
            max_history: 最大历史消息数
        """
        self.max_history = max_history
        self.messages: List[Message] = []

    def add_message(self, message: Message):
        """添加消息到记忆"""
        self.messages.append(message)
        # 保持历史消息数量限制
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
        logger.debug(f"添加消息到记忆: {message.role} - {message.content[:50]}...")

    def add_system_message(self, content: str, metadata: Dict[str, Any] = None):
        """添加系统消息"""
        self.add_message(Message(
            role="system",
            content=content,
            metadata=metadata or {}
        ))

    def add_user_message(self, content: str, agent_id: str = "", metadata: Dict[str, Any] = None):
        """添加用户消息"""
        self.add_message(Message(
            role="user",
            content=content,
            agent_id=agent_id,
            metadata=metadata or {}
        ))

    def add_assistant_message(self, content: str, metadata: Dict[str, Any] = None):
        """添加助手消息"""
        self.add_message(Message(
            role="assistant",
            content=content,
            metadata=metadata or {}
        ))

    def add_game_message(self, content: str, metadata: Dict[str, Any] = None):
        """添加游戏消息（系统通知）"""
        self.add_message(Message(
            role="game",
            content=content,
            metadata=metadata or {}
        ))

    def get_messages_for_llm(self) -> List[Dict[str, str]]:
        """获取用于LLM调用的消息列表"""
        return [msg.to_dict() for msg in self.messages]

    def get_recent_messages(self, n: int = 10) -> List[Message]:
        """获取最近的n条消息"""
        return self.messages[-n:]

    def clear(self):
        """清空记忆"""
        self.messages = []
        logger.info("记忆已清空")

    def __len__(self):
        return len(self.messages)

    def __repr__(self):
        return f"AgentMemory(messages={len(self.messages)})"
