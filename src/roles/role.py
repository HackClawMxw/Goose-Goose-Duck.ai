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

    def __repr__(self):
        return f"Role({self.name}, {self.camp.value})"


__all__ = ['Role']
