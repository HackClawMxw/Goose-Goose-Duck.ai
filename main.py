"""
主程序入口 - Goose-Goose-Duck.ai
基于鹅鸭杀的多Agent对话系统
"""
import sys
import json
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.game import GameEngine
from src.utils import setup_logger
from dotenv import load_dotenv
import yaml


def main():
    """主函数"""
    # 加载环境变量
    load_dotenv()

    # 加载配置
    config_path = Path("config.yaml")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    else:
        print("警告: config.yaml 不存在，使用默认配置")
        config = {}

    # 设置日志
    log_config = config.get('logging', {})
    logger = setup_logger(
        name="GooseGooseDuck",
        level=log_config.get('level', 'INFO'),
        log_file=log_config.get('file'),
        format_string=log_config.get('format')
    )

    logger.info("=" * 60)
    logger.info("鹅鸭杀 - 多Agent对话系统")
    logger.info("=" * 60)

    try:
        # 创建游戏引擎
        engine = GameEngine(config_path=str(config_path))

        # 自定义玩家名称（可选）
        player_names = [
            "小明", "小红", "小刚",
            "小丽", "小华", "小芳"
        ]

        # 设置游戏
        engine.setup_game(player_names=player_names)

        # 打印角色分配
        logger.info("\n角色分配:")
        for agent_id, agent in engine.agents.items():
            logger.info(f"  {agent.name}: {agent.role.name} ({agent.role.camp.value})")

        # 运行游戏
        result = engine.run_game()

        # 输出游戏总结
        summary = engine.get_game_summary()
        logger.info("\n" + "=" * 60)
        logger.info("游戏总结:")
        logger.info("=" * 60)
        logger.info(f"游戏结果: {summary['result']}")
        logger.info(f"总轮数: {summary['rounds']}")
        logger.info("\n玩家信息:")
        for player in summary['players']:
            logger.info(f"  {player['name']}: {player['role']} ({player['camp']}) - {player['status']}")

        # 保存游戏记录
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        game_log_path = output_dir / "game_log.json"
        with open(game_log_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        logger.info(f"\n游戏记录已保存到: {game_log_path}")

        logger.info("\n感谢游玩！")

    except Exception as e:
        logger.error(f"游戏运行出错: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
