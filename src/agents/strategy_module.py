"""
策略模块 - Agent 独立策略形成

基于角色目标形成独立策略，不受其他 Agent 影响。
每个角色有不同的策略导向：
- 鹅：找出鸭子、完成任务、保护队友
- 鸭子：隐藏身份、击杀目标、混淆视听
- 呆呆鸟：表现得可疑但不过度
"""

import time
from dataclasses import dataclass, field
from typing import List, Optional, Set, Dict, Any
import logging

from ..roles.role import Role
from ..roles.enums import Camp, RoleType

logger = logging.getLogger(__name__)


@dataclass
class StrategyPlan:
    """策略计划"""
    round_num: int
    primary_goal: str
    secondary_goals: List[str]
    tactics: List[str]
    avoid_behaviors: List[str]
    key_suspects: List[str]
    protect_targets: List[str]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_num": self.round_num,
            "primary_goal": self.primary_goal,
            "secondary_goals": self.secondary_goals,
            "tactics": self.tactics,
            "avoid_behaviors": self.avoid_behaviors,
            "key_suspects": self.key_suspects,
            "protect_targets": self.protect_targets,
            "timestamp": self.timestamp
        }


class StrategyModule:
    """
    策略模块 - 基于角色目标形成策略

    每个 Agent 都有独立的策略模块，用于：
    1. 分析当前局势
    2. 形成行动计划
    3. 指导发言和投票决策
    """

    def __init__(self, role: Role, llm=None):
        """
        初始化策略模块

        Args:
            role: 角色对象
            llm: LLM 实例（可选，用于动态策略生成）
        """
        self.role = role
        self.llm = llm
        self.current_plan: Optional[StrategyPlan] = None
        self.plan_history: List[StrategyPlan] = []

    def formulate_strategy(
        self,
        game_context: str,
        private_memory,
        known_info: Set[str] = None
    ) -> StrategyPlan:
        """
        形成策略计划

        Args:
            game_context: 游戏上下文
            private_memory: 私有记忆对象
            known_info: 已知信息集合

        Returns:
            策略计划
        """
        if known_info is None:
            known_info = set()

        round_num = 1  # 默认第一轮

        # 基于角色形成策略
        if self.role.camp == Camp.DUCK:
            plan = self._formulate_duck_strategy(
                game_context, private_memory, known_info, round_num
            )
        elif self.role.camp == Camp.GOOSE:
            plan = self._formulate_goose_strategy(
                game_context, private_memory, known_info, round_num
            )
        else:  # DODO
            plan = self._formulate_dodo_strategy(
                game_context, private_memory, known_info, round_num
            )

        self.current_plan = plan
        self.plan_history.append(plan)

        # 限制历史记录
        if len(self.plan_history) > 10:
            self.plan_history = self.plan_history[-10:]

        return plan

    def _formulate_duck_strategy(
        self,
        game_context: str,
        private_memory,
        known_info: Set[str],
        round_num: int
    ) -> StrategyPlan:
        """鸭子策略"""
        # 获取怀疑列表
        top_suspects = private_memory.get_top_suspects(3) if private_memory else []

        # 鸭子的主要目标是隐藏身份和消灭鹅
        plan = StrategyPlan(
            round_num=round_num,
            primary_goal="隐藏身份，避免被怀疑",
            secondary_goals=[
                "寻找机会击杀落单的鹅",
                "引导投票方向，让鹅互相怀疑",
                "保护队友不被发现"
            ],
            tactics=[
                "假装积极做任务，表现像好人",
                "发言时支持大多数意见，避免站错队",
                "适当怀疑一些好人，但不要过于激进",
                "如果有队友被怀疑，帮忙转移注意力"
            ],
            avoid_behaviors=[
                "不要在讨论中过于沉默",
                "不要盲目攻击某个玩家",
                "不要暴露队友身份"
            ],
            key_suspects=top_suspects,
            protect_targets=[]  # 队友列表会在游戏中更新
        )

        return plan

    def _formulate_goose_strategy(
        self,
        game_context: str,
        private_memory,
        known_info: Set[str],
        round_num: int
    ) -> StrategyPlan:
        """鹅策略"""
        # 获取怀疑列表
        top_suspects = private_memory.get_top_suspects(3) if private_memory else []
        suspicion_summary = private_memory.get_suspicion_summary() if private_memory else ""

        plan = StrategyPlan(
            round_num=round_num,
            primary_goal="找出所有鸭子，保护好人阵营",
            secondary_goals=[
                "完成任务推进游戏进度",
                "分享观察信息，帮助推理",
                "团结好人，避免内部分裂"
            ],
            tactics=[
                "观察每个人的发言是否有矛盾",
                "注意谁在刻意引导讨论方向",
                "完成任务证明自己的好人身份",
                "投票时谨慎选择，避免冤枉好人"
            ],
            avoid_behaviors=[
                "不要轻易相信所有人的发言",
                "不要在没有证据时过度指控",
                "不要孤立自己"
            ],
            key_suspects=top_suspects,
            protect_targets=[]
        )

        return plan

    def _formulate_dodo_strategy(
        self,
        game_context: str,
        private_memory,
        known_info: Set[str],
        round_num: int
    ) -> StrategyPlan:
        """呆呆鸟策略"""
        plan = StrategyPlan(
            round_num=round_num,
            primary_goal="被投票出局即可获胜",
            secondary_goals=[
                "表现得足够可疑，吸引投票",
                "不要暴露呆呆鸟身份",
                "利用阵营对立获得被投机会"
            ],
            tactics=[
                "发言时故意说一些模糊的话",
                "偶尔做出一些可疑的行为",
                "不要过度表现，否则会被识破",
                "让鹅以为你是鸭子"
            ],
            avoid_behaviors=[
                "不要直接暴露自己是呆呆鸟",
                "不要表现得太明显",
                "不要被鸭子击杀（那样就输了）"
            ],
            key_suspects=[],
            protect_targets=[]
        )

        return plan

    def update_strategy(
        self,
        new_information: str,
        private_memory
    ) -> StrategyPlan:
        """
        根据新信息更新策略

        Args:
            new_information: 新获取的信息
            private_memory: 私有记忆

        Returns:
            更新后的策略计划
        """
        if not self.current_plan:
            return self.formulate_strategy(new_information, private_memory)

        # 更新怀疑列表
        if private_memory:
            self.current_plan.key_suspects = private_memory.get_top_suspects(3)

        # 根据新信息调整战术
        # （这里可以添加更复杂的逻辑）

        return self.current_plan

    def get_strategy_prompt(self) -> str:
        """
        获取策略提示（用于 LLM 调用）

        Returns:
            策略提示文本
        """
        if not self.current_plan:
            return self._get_default_strategy_prompt()

        plan = self.current_plan

        prompt = f"""【当前策略】

主要目标：{plan.primary_goal}

次要目标：
{self._format_list(plan.secondary_goals)}

建议战术：
{self._format_list(plan.tactics)}

应避免的行为：
{self._format_list(plan.avoid_behaviors)}
"""
        return prompt

    def _get_default_strategy_prompt(self) -> str:
        """获取默认策略提示"""
        if self.role.camp == Camp.DUCK:
            return """【鸭子策略】
- 隐藏身份，避免被怀疑
- 寻找机会击杀落单的鹅
- 在讨论中混淆视听，转移嫌疑
"""
        elif self.role.camp == Camp.GOOSE:
            return """【鹅策略】
- 观察玩家行为，找出可疑之处
- 完成任务证明自己
- 在讨论中分享信息，帮助推理
"""
        else:
            return """【呆呆鸟策略】
- 表现得可疑但不明显
- 目标是被投票出局
- 不要暴露自己的真实身份
"""

    def _format_list(self, items: List[str]) -> str:
        """格式化列表"""
        if not items:
            return "- 无"
        return "\n".join([f"- {item}" for item in items])

    def should_speak_defensively(self) -> bool:
        """
        判断是否应该防御性发言

        Returns:
            是否应该防御
        """
        if not self.current_plan:
            return False

        # 鸭子通常需要防御性发言
        if self.role.camp == Camp.DUCK:
            return True

        return False

    def get_recommended_vote_target(self, candidates: List[str]) -> Optional[str]:
        """
        获取推荐的投票目标

        Args:
            candidates: 候选人列表

        Returns:
            推荐目标（如果没有则返回 None）
        """
        if not self.current_plan or not self.current_plan.key_suspects:
            return None

        # 在候选人中找到最可疑的
        for suspect in self.current_plan.key_suspects:
            if suspect in candidates:
                return suspect

        return None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "current_plan": self.current_plan.to_dict() if self.current_plan else None,
            "plan_history": [p.to_dict() for p in self.plan_history[-5:]]
        }
