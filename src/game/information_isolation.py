"""
信息隔离系统 - 控制不同角色可见的信息
"""
from typing import Dict, List, Set, Any
import logging
from ..roles import RoleType, Camp

logger = logging.getLogger(__name__)


class InformationIsolation:
    """信息隔离系统"""

    def __init__(self):
        """初始化信息隔离系统"""
        # 存储每个Agent知道的信息
        self.agent_knowledge: Dict[str, Set[str]] = {}

        # 存储阵营信息（鸭阵营知道谁是鸭子）
        self.camp_members: Dict[Camp, List[str]] = {
            Camp.GOOSE: [],
            Camp.DUCK: [],
            Camp.NEUTRAL: []
        }

    def register_agent(self, agent_id: str, camp: Camp):
        """
        注册Agent

        Args:
            agent_id: Agent ID
            camp: 阵营
        """
        self.agent_knowledge[agent_id] = set()
        self.camp_members[camp].append(agent_id)
        logger.debug(f"注册Agent: {agent_id} -> {camp.value}")

    def add_knowledge(self, agent_id: str, knowledge: str):
        """
        添加Agent的知识

        Args:
            agent_id: Agent ID
            knowledge: 知识内容
        """
        if agent_id not in self.agent_knowledge:
            self.agent_knowledge[agent_id] = set()
        self.agent_knowledge[agent_id].add(knowledge)
        logger.debug(f"Agent {agent_id} 获得知识: {knowledge[:50]}...")

    def share_camp_information(self):
        """分享阵营信息（鸭阵营成员互相认识）"""
        # 鸭阵营成员互相知道身份
        duck_ids = self.camp_members[Camp.DUCK]
        if len(duck_ids) > 1:
            for duck_id in duck_ids:
                # 每个鸭子知道其他鸭子的身份
                other_ducks = [d for d in duck_ids if d != duck_id]
                for other_duck in other_ducks:
                    self.add_knowledge(duck_id, f"玩家{other_duck}是鸭子（你的队友）")

            logger.info(f"鸭阵营信息已共享: {duck_ids}")

    def can_see_information(self, agent_id: str, information: str) -> bool:
        """
        判断Agent是否可以看到某信息

        Args:
            agent_id: Agent ID
            information: 信息内容

        Returns:
            是否可见
        """
        # 简单实现：所有公开信息都可见
        # 后续可以根据信息类型添加更复杂的逻辑
        return True

    def get_agent_knowledge(self, agent_id: str) -> Set[str]:
        """
        获取Agent的所有知识

        Args:
            agent_id: Agent ID

        Returns:
            知识集合
        """
        return self.agent_knowledge.get(agent_id, set())

    def format_knowledge_for_prompt(self, agent_id: str) -> str:
        """
        格式化Agent的知识为提示文本

        Args:
            agent_id: Agent ID

        Returns:
            格式化的知识文本
        """
        knowledge = self.get_agent_knowledge(agent_id)
        if not knowledge:
            return ""

        lines = ["【你知道的额外信息】"]
        for info in knowledge:
            lines.append(f"- {info}")

        return "\n".join(lines)

    def clear(self):
        """清空信息"""
        self.agent_knowledge.clear()
        for camp in self.camp_members:
            self.camp_members[camp] = []
        logger.info("信息隔离系统已清空")

    def __repr__(self):
        return f"InformationIsolation(agents={len(self.agent_knowledge)})"
