"""
角色枚举和基础定义
"""
from enum import Enum


class RoleType(Enum):
    """角色类型枚举"""
    # 鹅阵营
    GOOSE = "鹅"

    # 鸭阵营
    DUCK = "鸭子"

    # 中立阵营
    DODO = "呆呆鸟"


class Camp(Enum):
    """阵营枚举"""
    GOOSE = "鹅阵营"
    DUCK = "鸭阵营"
    NEUTRAL = "中立阵营"


# 角色类型到阵营的映射
ROLE_CAMP_MAP = {
    RoleType.GOOSE: Camp.GOOSE,
    RoleType.DUCK: Camp.DUCK,
    RoleType.DODO: Camp.NEUTRAL,
}

# 角色描述
ROLE_DESCRIPTIONS = {
    RoleType.GOOSE: {
        "name": "鹅",
        "camp": "鹅阵营",
        "description": "你是鹅阵营的成员，需要通过讨论和投票找出隐藏的鸭子，保护好人阵营。",
        "goal": "找出所有鸭子并投票出局，确保鹅阵营获胜。",
        "abilities": ["参与讨论", "投票"]
    },
    RoleType.DUCK: {
        "name": "鸭子",
        "camp": "鸭阵营",
        "description": "你是鸭阵营的成员，需要隐藏身份，混淆视听，避免被投票出局。",
        "goal": "隐藏身份，误导其他玩家，确保鸭阵营获胜。",
        "abilities": ["参与讨论", "投票", "伪装成好人"]
    },
    RoleType.DODO: {
        "name": "呆呆鸟",
        "camp": "中立阵营",
        "description": "你是中立阵营的呆呆鸟，需要表现得可疑，让其他玩家投票把你出局。",
        "goal": "被投票出局即可获胜，但不要表现得太明显。",
        "abilities": ["参与讨论", "投票", "表演可疑行为"]
    }
}
