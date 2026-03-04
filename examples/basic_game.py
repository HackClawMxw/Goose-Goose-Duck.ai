"""
示例：快速开始 - 运行一个简单的鹅鸭杀游戏
"""
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.game import GameEngine
from src.utils import setup_logger
from dotenv import load_dotenv


def quick_start():
    """快速开始示例"""
    # 加载环境变量
    load_dotenv()

    # 设置日志
    logger = setup_logger(level="INFO")

    print("=" * 60)
    print("鹅鸭杀 - 快速开始")
    print("=" * 60)

    # 创建游戏引擎
    engine = GameEngine(config_path="config.yaml")

    # 设置游戏（使用默认配置：3鹅2鸭1呆呆鸟）
    player_names = ["玩家A", "玩家B", "玩家C", "玩家D", "玩家E", "玩家F"]
    engine.setup_game(player_names=player_names)

    # 打印角色分配
    print("\n角色分配:")
    for agent_id, agent in engine.agents.items():
        print(f"  {agent.name}: {agent.role.name} ({agent.role.camp.value})")

    # 运行游戏
    result = engine.run_game()

    # 输出结果
    print("\n" + "=" * 60)
    print(f"游戏结束: {result.value}")
    print("=" * 60)

    # 获取游戏总结
    summary = engine.get_game_summary()
    print("\n玩家信息:")
    for player in summary['players']:
        print(f"  {player['name']}: {player['role']} ({player['camp']}) - {player['status']}")


if __name__ == "__main__":
    quick_start()
