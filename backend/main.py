"""
FastAPI 应用入口
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging

from .config import settings
from .api import game, websocket

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="Goose-Goose-Duck.ai API",
    description="AI 鹅鸭杀游戏后端 API",
    version="0.1.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(game.router, prefix="/api", tags=["game"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "message": "Goose-Goose-Duck.ai API is running"}


# 静态文件服务（前端构建产物）
frontend_dist = Path(settings.frontend_dist_path)
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        """服务前端页面"""
        # 如果是 API 路径，跳过
        if path.startswith("api/") or path.startswith("ws/"):
            return {"error": "Not found"}

        # 尝试返回静态文件
        file_path = frontend_dist / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)

        # 默认返回 index.html (SPA 路由支持)
        index_path = frontend_dist / "index.html"
        if index_path.exists():
            return FileResponse(index_path)

        return {"error": "Frontend not built"}


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("🦆 Goose-Goose-Duck.ai API 启动中...")
    logger.info(f"服务地址: http://{settings.server.host}:{settings.server.port}")
    logger.info(f"API 文档: http://{settings.server.host}:{settings.server.port}/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("🦆 Goose-Goose-Duck.ai API 关闭中...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.debug
    )
