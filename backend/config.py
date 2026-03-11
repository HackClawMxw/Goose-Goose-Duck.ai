"""
后端配置
"""
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
import yaml


class ServerConfig(BaseModel):
    """服务器配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


class Settings(BaseModel):
    """应用设置"""
    server: ServerConfig = ServerConfig()
    game_config_path: str = "config.yaml"
    frontend_dist_path: str = "frontend/dist"

    @classmethod
    def load(cls) -> "Settings":
        """加载配置"""
        return cls()


# 全局配置实例
settings = Settings.load()


def load_game_config() -> dict:
    """加载游戏配置文件"""
    config_path = Path(settings.game_config_path)
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}
