"""
Goose-Goose-Duck.ai 主模块
"""
from .llm import LLMFactory, BaseLLM, GLMLLM, OpenAICompatibleLLM
from .agents import Agent, AgentMemory, Message
from .roles import Role, RoleType, Camp
from .game import GameEngine, GameState, GamePhase, GameResult

__version__ = "0.1.0"

__all__ = [
    'LLMFactory', 'BaseLLM', 'GLMLLM', 'OpenAICompatibleLLM',
    'Agent', 'AgentMemory', 'Message',
    'Role', 'RoleType', 'Camp',
    'GameEngine', 'GameState', 'GamePhase', 'GameResult'
]
