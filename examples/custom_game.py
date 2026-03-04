"""
示例：自定义游戏 - 使用自定义配置和玩家
"""
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.game import GameEngine
from src.utils import setup_logger
from dotenv import load_dotenv


def custom_game():
    """自定义游戏示例"""
    # 加载环境变量
    load_dotenv()

    # 设置日志
    logger = setup_logger(level="DEBUG", log_file="logs/custom_game.log")

    print("=" * 60)
    print("鹅鸭杀 - 自定义游戏")
    print("=" * 60)

    # 创建游戏引擎（使用自定义配置文件）
    engine = GameEngine(config_path="config.yaml")

    # 自定义玩家名称
    player_names = [
        "福尔摩斯", "华生", "莫里亚蒂",
        "艾琳", "雷斯垂德", "玛丽"
    ]

    # 设置游戏
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

    # 获取详细总结
    summary = engine.get_game_summary()
    print("\n玩家信息:")
    for player in summary['players']:
        print(f"  {player['name']}: {player['role']} ({player['camp']}) - {player['status']}")

    print("\n游戏历史:")
    for i, event in enumerate(summary['history'], 1):
        print(f"  {i}. {event}")


if __name__ == "__main__":
    custom_game()
