"""
对话管理器 - 管理多Agent对话和信息隔离
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class DialogueMessage:
    """对话消息"""
    speaker_id: str
    speaker_name: str
    content: str
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    phase: str = "discussion"  # discussion, voting, execution
    round_num: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


class DialogueManager:
    """对话管理器 - 支持发言顺序和信息隔离"""

    def __init__(self):
        """初始化对话管理器"""
        self.dialogue_history: List[DialogueMessage] = []
        self.current_round = 1
        self.current_phase = "discussion"

        # 发言顺序管理
        self.speaking_order: List[str] = []  # 当前轮发言顺序 (agent_id 列表)
        self.current_speaker_index: int = 0
        self.speaking_position_map: Dict[str, int] = {}  # agent_id -> position

    def add_dialogue(
        self,
        speaker_id: str,
        speaker_name: str,
        content: str,
        phase: str = None,
        metadata: Dict[str, Any] = None
    ):
        """
        添加对话消息

        Args:
            speaker_id: 发言者ID
            speaker_name: 发言者名称
            content: 对话内容
            phase: 阶段
            metadata: 元数据
        """
        message = DialogueMessage(
            speaker_id=speaker_id,
            speaker_name=speaker_name,
            content=content,
            phase=phase or self.current_phase,
            round_num=self.current_round,
            metadata=metadata or {}
        )
        self.dialogue_history.append(message)
        logger.info(f"对话记录: [{message.phase}] {speaker_name}: {content[:50]}...")

    def get_dialogue_for_agent(
        self,
        agent_id: str,
        round_num: int = None,
        phase: str = None,
        current_position: int = None
    ) -> List[DialogueMessage]:
        """
        获取特定Agent可见的对话历史

        改进后的方法支持按发言位置过滤，
        Agent 只能看到自己发言之前的对话。

        Args:
            agent_id: Agent ID
            round_num: 轮次（None表示所有轮次）
            phase: 阶段（None表示所有阶段）
            current_position: Agent 在当前发言顺序中的位置
                              如果提供，只返回该位置之前的对话

        Returns:
            可见的对话消息列表
        """
        messages = self.dialogue_history

        # 按轮次过滤
        if round_num is not None:
            messages = [m for m in messages if m.round_num == round_num]

        # 按阶段过滤
        if phase is not None:
            messages = [m for m in messages if m.phase == phase]

        # 按发言位置过滤（新增）
        # Agent 只能看到自己发言位置之前的对话
        if current_position is not None:
            if current_position == 0:
                # 第一个发言者看不到任何之前的对话
                messages = []
            elif len(messages) >= current_position:
                # 只保留该位置之前的对话
                messages = messages[:current_position]

        return messages

    def format_dialogue_for_context(
        self,
        messages: List[DialogueMessage],
        max_messages: int = 20
    ) -> str:
        """
        格式化对话历史为上下文文本

        Args:
            messages: 对话消息列表
            max_messages: 最大消息数

        Returns:
            格式化的上下文文本
        """
        if not messages:
            return "暂无对话历史。"

        # 只取最近的N条消息
        recent_messages = messages[-max_messages:]

        lines = ["【对话历史】"]
        for msg in recent_messages:
            lines.append(f"{msg.speaker_name}: {msg.content}")

        return "\n".join(lines)

    def start_new_round(self):
        """开始新一轮"""
        self.current_round += 1
        logger.info(f"开始第 {self.current_round} 轮")

    def set_phase(self, phase: str):
        """设置当前阶段"""
        self.current_phase = phase
        logger.info(f"进入 {phase} 阶段")

    def set_speaking_order(self, agent_ids: List[str]) -> None:
        """
        设置本轮发言顺序

        Args:
            agent_ids: Agent ID 列表，按发言顺序排列
        """
        self.speaking_order = agent_ids.copy()
        self.current_speaker_index = 0
        # 构建位置映射
        self.speaking_position_map = {
            agent_id: i for i, agent_id in enumerate(agent_ids)
        }
        logger.info(f"设置发言顺序: {agent_ids}")

    def get_current_position(self, agent_id: str) -> int:
        """
        获取 Agent 在发言顺序中的位置

        Args:
            agent_id: Agent ID

        Returns:
            位置索引（如果不在列表中返回 -1）
        """
        return self.speaking_position_map.get(agent_id, -1)

    def advance_speaker(self) -> None:
        """推进到下一个发言者"""
        self.current_speaker_index += 1

    def get_current_speaker(self) -> Optional[str]:
        """获取当前发言者 ID"""
        if self.current_speaker_index < len(self.speaking_order):
            return self.speaking_order[self.current_speaker_index]
        return None

    def get_recent_dialogue(self, n: int = 10) -> List[DialogueMessage]:
        """获取最近的n条对话"""
        return self.dialogue_history[-n:]

    def clear(self):
        """清空对话历史"""
        self.dialogue_history = []
        self.current_round = 1
        self.current_phase = "discussion"
        logger.info("对话历史已清空")

    def __len__(self):
        return len(self.dialogue_history)

    def __repr__(self):
        return f"DialogueManager(rounds={self.current_round}, messages={len(self.dialogue_history)})"
