"""
角色类定义
"""
from dataclasses import dataclass
from typing import List, Dict, Any
from .enums import RoleType, Camp, ROLE_CAMP_MAP, ROLE_DESCRIPTIONS


@dataclass
class Role:
    """角色类"""
    role_type: RoleType
    name: str
    camp: Camp
    description: str
    goal: str
    abilities: List[str]

    @classmethod
    def from_type(cls, role_type: RoleType) -> 'Role':
        """从角色类型创建角色实例"""
        info = ROLE_DESCRIPTIONS[role_type]
        return cls(
            role_type=role_type,
            name=info['name'],
            camp=ROLE_CAMP_MAP[role_type],
            description=info['description'],
            goal=info['goal'],
            abilities=info['abilities']
        )

    def get_system_prompt(self) -> str:
        """获取角色的系统提示"""
        abilities_text = "、".join(self.abilities)
        return f"""你正在玩鹅鸭杀游戏。

【你的身份】
角色：{self.name}
阵营：{self.camp.value}

【角色描述】
{self.description}

【获胜目标】
{self.goal}

【你的能力】
{abilities_text}

【游戏规则】
1. 你需要扮演好你的角色，根据你的阵营目标行动
2. 在讨论阶段，你可以发言表达观点
3. 在投票阶段，你需要投票选出你认为最可疑的人
4. 注意：不同阵营的玩家知道的信息不同，要小心信息泄露

【行为准则】
- 保持角色一致性，始终按照角色设定行动
- 发言要简洁有力，不要过于冗长
- 注意观察其他玩家的言行，寻找破绽
- 根据你的阵营目标制定策略
"""

    def get_strategy_prompt(self) -> str:
        """获取角色的策略提示（用于AI决策)"""
        if self.camp == Camp.DUCK:
            return f"""你是鸭子阵营。你的目标是悄悄消灭鹅阵营的玩家。

策略建议：
1. 伪装成好人，不要暴露自己的身份
2. 寻找落单的鹅玩家下手
3. 利用通风管快速移动
4. 在讨论时混淆视听，转移嫌疑
5. 和其他鸭子配合行动

"""
        elif self.camp == Camp.GOOSE:
            return f"""你是鹅阵营。你的目标是找出鸭子并保护自己。

策略建议：
1. 观察其他玩家的行为，寻找可疑之处
2. 完成任务来证明自己的价值
3. 在讨论时积极发言，分享信息
4. 投票时谨慎选择
"""
        else:
            return f"""你的目标是生存到最后。观察游戏进程。"""

    def get_thinking_prompt(self) -> str:
        """
        获取独立思考提示（私有）

        这是 Agent 进行独立思考时使用的提示，
        帮助 Agent 形成自己的判断和策略。
        """
        if self.camp == Camp.DUCK:
            return """【鸭子思考指南】

你需要隐藏身份并消灭鹅阵营。

思考要点：
1. 谁可能怀疑你？如何应对？
2. 哪个鹅最容易被投票出局？
3. 如何引导讨论方向，让鹅互相怀疑？
4. 是否需要保护队友？如何在不暴露的情况下帮忙？
5. 下一次行动的目标是谁？

注意事项：
- 永远不要在公开场合暴露你的身份
- 注意谁在针对你或你的队友
- 寻找机会嫁祸给好人
"""
        elif self.camp == Camp.GOOSE:
            return """【鹅思考指南】

你需要找出鸭子并保护好人阵营。

思考要点：
1. 谁的发言有矛盾或不自然？
2. 谁在刻意引导讨论方向？
3. 谁的行为不符合好人逻辑？
4. 如何说服其他人相信你的判断？
5. 你观察到了哪些可疑行为？

注意事项：
- 不要轻易相信所有人的发言
- 注意谁在保护谁
- 记录每个人的发言，寻找不一致
"""
        else:  # DODO
            return """【呆呆鸟思考指南】

你需要被投票出局才能获胜。

思考要点：
1. 如何表现得可疑但不明显？
2. 如何吸引投票但不暴露目标？
3. 哪些行为会让人觉得你是鸭子？
4. 如何在鹅和鸭子的对抗中找到被投机会？

注意事项：
- 不要直接暴露你是呆呆鸟
- 表现要自然，不能太刻意
- 避免被鸭子击杀（那样你就输了）
"""

    def __repr__(self):
        return f"Role({self.name}, {self.camp.value})"


__all__ = ['Role']
