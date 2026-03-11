"""
游戏系统模块
"""
from .dialogue_manager import DialogueManager, DialogueMessage
from .information_isolation import InformationIsolation
from .game_state import GameState, GamePhase, GameResult
from .game_engine import GameEngine
from .map_system import GameMap, Room, Task, RoomType
from .vision_system import VisionSystem, GameEvent, EventType, AgentPosition
from .action_system import ActionType, GameAction, ActionValidator, ActionExecutor
from .enhanced_game_engine import EnhancedGameEngine

__all__ = [
    'DialogueManager', 'DialogueMessage',
    'InformationIsolation',
    'GameState', 'GamePhase', 'GameResult',
    'GameEngine',
    # Phase 2 新增
    'GameMap', 'Room', 'Task', 'RoomType',
    'VisionSystem', 'GameEvent', 'EventType', 'AgentPosition',
    'ActionType', 'GameAction', 'ActionValidator', 'ActionExecutor',
    'EnhancedGameEngine'
]
