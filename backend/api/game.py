"""
游戏 REST API
"""
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any

from ..models.requests import CreateGameRequest, StartGameRequest
from ..models.responses import (
    PlayerInfo,
    GameStateResponse,
    GameSummaryResponse,
    GameCreatedResponse
)
from ..services.game_service import GameService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/games", response_model=GameCreatedResponse)
async def create_game(request: CreateGameRequest):
    """
    创建新游戏

    - **player_names**: 可选的玩家名称列表
    - **config_override**: 可选的配置覆盖
    """
    try:
        game_service = GameService.create_game(
            player_names=request.player_names,
            config=request.config_override
        )

        players = [
            PlayerInfo(
                agent_id=agent_id,
                name=agent.name,
                is_alive=agent.is_alive
            )
            for agent_id, agent in game_service.engine.agents.items()
        ]

        return GameCreatedResponse(
            game_id=game_service.game_id,
            status="created",
            players=players,
            message="游戏创建成功"
        )
    except Exception as e:
        logger.error(f"创建游戏失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/games/{game_id}", response_model=GameStateResponse)
async def get_game_state(game_id: str):
    """
    获取游戏状态

    - **game_id**: 游戏 ID
    """
    game_service = GameService.get_game(game_id)
    if not game_service:
        raise HTTPException(status_code=404, detail="游戏不存在")

    state = game_service.get_state()
    return GameStateResponse(**state)


@router.post("/games/{game_id}/start")
async def start_game(game_id: str, request: StartGameRequest, background_tasks: BackgroundTasks):
    """
    开始游戏

    - **game_id**: 游戏 ID
    - **auto_play**: 是否自动进行游戏
    - **delay_seconds**: 事件之间的延迟秒数
    """
    game_service = GameService.get_game(game_id)
    if not game_service:
        raise HTTPException(status_code=404, detail="游戏不存在")

    if game_service._is_running:
        raise HTTPException(status_code=400, detail="游戏已在运行中")

    # 在后台启动游戏
    await game_service.start_game(delay_seconds=request.delay_seconds)

    return {
        "status": "started",
        "game_id": game_id,
        "message": "游戏已开始"
    }


@router.post("/games/{game_id}/pause")
async def pause_game(game_id: str):
    """暂停游戏"""
    game_service = GameService.get_game(game_id)
    if not game_service:
        raise HTTPException(status_code=404, detail="游戏不存在")

    await game_service.pause_game()
    return {"status": "paused", "game_id": game_id}


@router.post("/games/{game_id}/resume")
async def resume_game(game_id: str):
    """恢复游戏"""
    game_service = GameService.get_game(game_id)
    if not game_service:
        raise HTTPException(status_code=404, detail="游戏不存在")

    await game_service.resume_game()
    return {"status": "resumed", "game_id": game_id}


@router.get("/games/{game_id}/summary", response_model=GameSummaryResponse)
async def get_game_summary(game_id: str):
    """获取游戏总结"""
    game_service = GameService.get_game(game_id)
    if not game_service:
        raise HTTPException(status_code=404, detail="游戏不存在")

    summary = game_service.get_summary()
    return GameSummaryResponse(**summary)


@router.get("/games")
async def list_games():
    """列出所有游戏"""
    games = []
    for game_id in GameService.list_games():
        game_service = GameService.get_game(game_id)
        if game_service:
            games.append({
                "game_id": game_id,
                "status": "running" if game_service._is_running else "created",
                "round": game_service.engine.game_state.round_num,
                "phase": game_service.engine.game_state.phase.value,
                "player_count": len(game_service.engine.agents)
            })
    return {"games": games}


@router.delete("/games/{game_id}")
async def delete_game(game_id: str):
    """删除游戏"""
    game_service = GameService.get_game(game_id)
    if not game_service:
        raise HTTPException(status_code=404, detail="游戏不存在")

    if game_service._is_running:
        raise HTTPException(status_code=400, detail="游戏正在运行，无法删除")

    GameService.remove_game(game_id)
    return {"status": "deleted", "game_id": game_id}
