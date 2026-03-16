"""
私有记忆系统 - Agent 独立思考的核心组件

每个 Agent 都有自己的私有记忆空间，存储：
- 思考记录
- 怀疑分数
- 策略笔记
- 私有观察

这些信息不会被其他 Agent 访问到。
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class PrivateThought:
    """私有思考记录"""
    round_num: int
    phase: str  # "pre_discussion", "during_discussion", "pre_vote", "observation"
    thought_type: str  # "analysis", "suspicion", "strategy", "observation"
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_num": self.round_num,
            "phase": self.phase,
            "thought_type": self.thought_type,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


@dataclass
class SuspicionRecord:
    """怀疑记录"""
    agent_id: str
    agent_name: str
    score: float  # 0-1, 越高越可疑
    reason: str
    timestamp: float = field(default_factory=time.time)
    round_num: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "score": self.score,
            "reason": self.reason,
            "timestamp": self.timestamp,
            "round_num": self.round_num
        }


class PrivateMemory:
    """
    私有记忆系统 - 其他 Agent 无法访问

    用于存储 Agent 的独立思考、策略和观察。
    这是实现 Agent 独立性的关键组件。
    """

    def __init__(self, max_thoughts: int = 100, self_name: str = None):
        """
        初始化私有记忆

        Args:
            max_thoughts: 最大思考记录数量
            self_name: 自己的名字（用于排除对自己的怀疑）
        """
        self.thoughts: List[PrivateThought] = []
        self.suspicion_records: Dict[str, SuspicionRecord] = {}  # agent_id -> record
        self.strategy_notes: List[str] = []
        self.observations: List[str] = []
        self.max_thoughts = max_thoughts
        self.self_name = self_name  # 记录自己的名字

        # 当前策略
        self.current_strategy: Optional[str] = None

    def add_thought(self, thought: PrivateThought) -> None:
        """
        添加思考记录

        Args:
            thought: 思考记录
        """
        self.thoughts.append(thought)

        # 限制历史记录数量
        if len(self.thoughts) > self.max_thoughts:
            self.thoughts = self.thoughts[-self.max_thoughts:]

        logger.debug(f"添加私有思考: [{thought.phase}] {thought.content[:50]}...")

    def update_suspicion(
        self,
        agent_id: str,
        agent_name: str,
        score: float,
        reason: str,
        round_num: int = 0
    ) -> None:
        """
        更新对某个 Agent 的怀疑分数

        Args:
            agent_id: Agent ID
            agent_name: Agent 名称
            score: 怀疑分数 (0-1)
            reason: 怀疑原因
            round_num: 当前轮次
        """
        # 【关键】绝对不能怀疑自己
        if self.self_name and (agent_id == self.self_name or agent_name == self.self_name):
            logger.warning(f"尝试怀疑自己 ({self.self_name})，已阻止")
            return

        # 如果已有记录，更新分数（取平均或最新）
        if agent_id in self.suspicion_records:
            existing = self.suspicion_records[agent_id]
            # 加权平均：新分数占 60%，旧分数占 40%
            new_score = existing.score * 0.4 + score * 0.6
            existing.score = new_score
            existing.reason = f"{existing.reason}; {reason}"
            existing.timestamp = time.time()
            existing.round_num = round_num
        else:
            self.suspicion_records[agent_id] = SuspicionRecord(
                agent_id=agent_id,
                agent_name=agent_name,
                score=score,
                reason=reason,
                round_num=round_num
            )

        logger.debug(f"更新怀疑分数: {agent_name} -> {score:.2f} ({reason[:30]}...)")

    def get_suspicion_summary(self, top_n: int = 5) -> str:
        """
        获取怀疑列表摘要

        Args:
            top_n: 返回前 N 个最可疑的

        Returns:
            怀疑列表的文本摘要
        """
        if not self.suspicion_records:
            return "暂无怀疑对象"

        # 【修复】过滤掉自己，按分数排序
        filtered_suspicions = [
            r for r in self.suspicion_records.values()
            if not (self.self_name and (r.agent_id == self.self_name or r.agent_name == self.self_name))
        ]

        if not filtered_suspicions:
            return "暂无怀疑对象"

        sorted_suspicions = sorted(
            filtered_suspicions,
            key=lambda x: x.score,
            reverse=True
        )[:top_n]

        lines = ["我的怀疑列表："]
        for i, record in enumerate(sorted_suspicions, 1):
            lines.append(
                f"{i}. {record.agent_name} (可疑度: {record.score:.1%}) - {record.reason[:50]}"
            )

        return "\n".join(lines)

    def get_top_suspects(self, n: int = 3) -> List[str]:
        """
        获取最可疑的 N 个 Agent ID

        Args:
            n: 数量

        Returns:
            Agent ID 列表
        """
        if not self.suspicion_records:
            return []

        # 【修复】过滤掉自己
        filtered_suspicions = [
            r for r in self.suspicion_records.values()
            if not (self.self_name and (r.agent_id == self.self_name or r.agent_name == self.self_name))
        ]

        if not filtered_suspicions:
            return []

        sorted_suspicions = sorted(
            filtered_suspicions,
            key=lambda x: x.score,
            reverse=True
        )[:n]

        return [r.agent_id for r in sorted_suspicions]

    def add_strategy_note(self, note: str) -> None:
        """
        添加策略笔记

        Args:
            note: 策略笔记内容
        """
        self.strategy_notes.append(note)
        self.current_strategy = note

        # 限制笔记数量
        if len(self.strategy_notes) > 20:
            self.strategy_notes = self.strategy_notes[-20:]

        logger.debug(f"添加策略笔记: {note[:50]}...")

    def get_strategy_context(self) -> str:
        """
        获取策略上下文

        Returns:
            策略相关的文本
        """
        if not self.current_strategy and not self.strategy_notes:
            return "暂无特定策略"

        # 返回最近的策略笔记
        recent_notes = self.strategy_notes[-3:] if self.strategy_notes else []
        notes_text = "\n".join([f"- {note}" for note in recent_notes])

        return f"我的策略：\n{notes_text}"

    def add_observation(self, observation: str) -> None:
        """
        添加私有观察

        Args:
            observation: 观察内容
        """
        self.observations.append(observation)

        # 限制观察数量
        if len(self.observations) > 50:
            self.observations = self.observations[-50:]

        logger.debug(f"添加私有观察: {observation[:50]}...")

    def get_recent_observations(self, n: int = 5) -> List[str]:
        """
        获取最近的观察

        Args:
            n: 数量

        Returns:
            观察列表
        """
        return self.observations[-n:] if self.observations else []

    def get_recent_thoughts(self, n: int = 5) -> List[PrivateThought]:
        """
        获取最近的思考记录

        Args:
            n: 数量

        Returns:
            思考记录列表
        """
        return self.thoughts[-n:] if self.thoughts else []

    def get_recent_thoughts_str(self, n: int = 5) -> str:
        """
        获取最近的思考记录（文本格式）

        Args:
            n: 数量

        Returns:
            思考记录的文本
        """
        recent = self.get_recent_thoughts(n)
        if not recent:
            return "暂无之前的思考记录"

        lines = ["我最近的思考："]
        for thought in recent:
            lines.append(f"[{thought.phase}] {thought.content[:100]}")

        return "\n".join(lines)

    def clear_round_data(self) -> None:
        """清除一轮游戏的数据（保留长期记忆）"""
        # 只保留最近的思考
        self.thoughts = self.thoughts[-10:]

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典（用于调试/可视化）

        Returns:
            字典表示
        """
        return {
            "thoughts": [t.to_dict() for t in self.thoughts[-10:]],
            "suspicion_records": {
                k: v.to_dict() for k, v in self.suspicion_records.items()
            },
            "strategy_notes": self.strategy_notes[-5:],
            "observations": self.observations[-5:],
            "current_strategy": self.current_strategy
        }
