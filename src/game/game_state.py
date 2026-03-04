"""
游戏状态管理
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class GamePhase(Enum):
    """游戏阶段枚举"""
    INIT = "初始化"
    DISCUSSION = "讨论阶段"
    VOTING = "投票阶段"
    EXECUTION = "处决阶段"
    GAME_OVER = "游戏结束"


class GameResult(Enum):
    """游戏结果枚举"""
    GOOSE_WIN = "鹅阵营获胜"
    DUCK_WIN = "鸭阵营获胜"
    DODO_WIN = "呆呆鸟获胜"
    ONGOING = "游戏进行中"


@dataclass
class GameState:
    """游戏状态"""
    # 基本信息
    round_num: int = 1
    phase: GamePhase = GamePhase.INIT
    result: GameResult = GameResult.ONGOING

    # 玩家状态
    alive_players: List[str] = field(default_factory=list)
    dead_players: List[str] = field(default_factory=list)

    # 投票信息
    votes: Dict[str, str] = field(default_factory=dict)  # voter_id -> voted_id
    vote_results: Dict[str, int] = field(default_factory=dict)  # voted_id -> count

    # 游戏历史
    history: List[Dict[str, Any]] = field(default_factory=list)

    def add_vote(self, voter_id: str, voted_id: str):
        """添加投票"""
        self.votes[voter_id] = voted_id
        if voted_id not in self.vote_results:
            self.vote_results[voted_id] = 0
        self.vote_results[voted_id] += 1
        logger.debug(f"投票: {voter_id} -> {voted_id}")

    def get_vote_winner(self) -> Optional[str]:
        """获取投票结果（得票最多的玩家）"""
        if not self.vote_results:
            return None

        max_votes = max(self.vote_results.values())
        winners = [player_id for player_id, votes in self.vote_results.items()
                   if votes == max_votes]

        # 如果平票，返回None（需要重新投票或其他处理）
        if len(winners) > 1:
            logger.warning(f"平票: {winners}")
            return None

        return winners[0]

    def reset_round(self):
        """重置回合状态"""
        self.votes.clear()
        self.vote_results.clear()

    def record_event(self, event: Dict[str, Any]):
        """记录游戏事件"""
        self.history.append(event)
        logger.info(f"游戏事件: {event}")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "round_num": self.round_num,
            "phase": self.phase.value,
            "result": self.result.value,
            "alive_players": self.alive_players,
            "dead_players": self.dead_players,
            "votes": self.votes,
            "vote_results": self.vote_results
        }

    def __repr__(self):
        return f"GameState(round={self.round_num}, phase={self.phase.value}, alive={len(self.alive_players)})"
