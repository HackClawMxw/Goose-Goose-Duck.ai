"""
WebSocket 处理
"""
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.event_manager import event_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    """
    WebSocket 端点

    客户端可以发送以下消息：
    - {"type": "subscribe", "game_id": "xxx"} - 订阅游戏事件
    - {"type": "ping"} - 心跳检测

    服务端会推送以下事件：
    - game_started - 游戏开始
    - phase_changed - 阶段变化
    - dialogue - 对话消息
    - vote_cast - 投票事件
    - player_died - 玩家死亡
    - game_over - 游戏结束
    """
    await event_manager.subscribe(game_id, websocket)
    logger.info(f"WebSocket 连接建立: game_id={game_id}")

    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                msg_type = message.get("type", "")

                if msg_type == "ping":
                    # 心跳响应
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": __import__('time').time()
                    }))
                elif msg_type == "subscribe":
                    # 订阅确认
                    await websocket.send_text(json.dumps({
                        "type": "subscribed",
                        "game_id": game_id,
                        "message": f"已订阅游戏 {game_id}"
                    }))
                else:
                    logger.debug(f"收到未知消息类型: {msg_type}")

            except json.JSONDecodeError:
                logger.warning(f"无效的 JSON 消息: {data}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket 断开连接: game_id={game_id}")
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}", exc_info=True)
    finally:
        event_manager.unsubscribe(game_id, websocket)
