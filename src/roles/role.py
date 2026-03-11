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

    def __repr__(self):
        return f"Role({self.name}, {self.camp.value})"


__all__ = ['Role']
