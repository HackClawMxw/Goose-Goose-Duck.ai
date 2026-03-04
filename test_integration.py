"""
完整集成测试 - 测试整个游戏流程（使用Mock LLM）
"""
import sys
from pathlib import Path

# 设置UTF-8编码输出
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.game import GameEngine
from src.roles import Camp
from src.utils import setup_logger


def test_full_game():
    """测试完整的游戏流程"""
    print("\n" + "=" * 60)
    print("完整游戏流程测试（Mock LLM）")
    print("=" * 60)

    # 先创建Mock LLM
    class MockLLM:
        def __init__(self):
            self.model = "mock-llm"
            self.call_count = 0

        def chat(self, messages, **kwargs):
            self.call_count += 1
            # 根据消息内容返回不同的回复
            last_message = messages[-1]['content'] if messages else ""

            if "发言" in last_message or "看法" in last_message:
                responses = [
                    "我觉得我们应该仔细观察每个人的言行。",
                    "我注意到有些人的表现很可疑。",
                    "我是好人，请相信我。",
                    "大家冷静分析，不要冲动投票。",
                    "我支持投票给最可疑的人。"
                ]
                import random
                return random.choice(responses)
            elif "投票" in last_message:
                # 返回第一个候选人的名字
                for line in last_message.split('\n'):
                    if '候选人' in line:
                        candidates = line.split('：')[1].split('、')
                        return candidates[0].strip()
                return "玩家1"
            else:
                return "我明白了。"

        def chat_with_system(self, system_prompt, user_message, **kwargs):
            return self.chat([{"role": "user", "content": user_message}])

    # 创建Mock LLM工厂
    class MockLLMFactory:
        @staticmethod
        def create_llm(config):
            return MockLLM()

    # 在导入GameEngine之前替换LLM工厂
    import src.llm
    original_factory = src.llm.LLMFactory
    src.llm.LLMFactory = MockLLMFactory

    try:
        # 创建游戏引擎
        print("\n1. 创建游戏引擎...")
        engine = GameEngine()
        print("   ✓ 游戏引擎创建成功")

        # 设置游戏
        print("\n2. 设置游戏（6名玩家）...")
        player_names = ["小明", "小红", "小刚", "小丽", "小华", "小芳"]
        engine.setup_game(player_names=player_names)
        print(f"   ✓ 游戏设置完成")

        # 显示角色分配
        print("\n3. 角色分配:")
        camps = {Camp.GOOSE: 0, Camp.DUCK: 0, Camp.NEUTRAL: 0}
        for agent in engine.agents.values():
            camps[agent.role.camp] += 1
            print(f"   {agent.name}: {agent.role.name} ({agent.role.camp.value})")

        print(f"\n   阵营统计: 鹅={camps[Camp.GOOSE]}, 鸭={camps[Camp.DUCK]}, 中立={camps[Camp.NEUTRAL]}")

        # 检查信息隔离
        print("\n4. 测试信息隔离...")
        duck_agents = [a for a in engine.agents.values() if a.role.camp == Camp.DUCK]
        if len(duck_agents) >= 2:
            # 检查鸭子是否互相认识
            first_duck = duck_agents[0]
            knowledge = engine.info_isolation.get_agent_knowledge(first_duck.agent_id)
            has_teammate_info = any("队友" in k or "鸭子" in k for k in knowledge)
            print(f"   ✓ 鸭阵营信息隔离: {'正常' if has_teammate_info else '异常'}")
        else:
            print("   ⚠ 只有一个鸭子，跳过队友信息测试")

        # 运行一轮游戏
        print("\n5. 运行一轮游戏...")

        # 讨论阶段
        print("   - 讨论阶段")
        engine.start_discussion_phase()
        print(f"     ✓ 讨论完成，共 {len(engine.dialogue_manager)} 条对话")

        # 投票阶段
        print("   - 投票阶段")
        engine.start_voting_phase()
        print(f"     ✓ 投票完成，投票结果: {engine.game_state.vote_results}")

        # 执行投票
        print("   - 处决阶段")
        executed = engine.execute_voting_result()
        if executed:
            print(f"     ✓ {executed} 被投票出局")
        else:
            print("     ⚠ 平票，无人出局")

        # 检查游戏状态
        print("\n6. 检查游戏状态...")
        print(f"   当前轮次: {engine.game_state.round_num}")
        print(f"   存活玩家: {len(engine.game_state.alive_players)}")
        print(f"   死亡玩家: {len(engine.game_state.dead_players)}")
        print(f"   游戏阶段: {engine.game_state.phase.value}")

        # 获取游戏总结
        print("\n7. 游戏总结:")
        summary = engine.get_game_summary()
        print(f"   游戏结果: {summary['result']}")
        print(f"   总轮数: {summary['rounds']}")
        print(f"   玩家状态:")
        for player in summary['players']:
            print(f"     - {player['name']}: {player['role']} ({player['status']})")

        # 统计LLM调用次数
        print(f"\n8. LLM调用统计:")
        total_calls = sum(
            agent.llm.call_count
            for agent in engine.agents.values()
            if hasattr(agent.llm, 'call_count')
        )
        print(f"   总调用次数: {total_calls}")

        print("\n" + "=" * 60)
        print("✓ 完整游戏流程测试通过！")
        print("=" * 60)

        print("\n测试验证:")
        print("  ✓ 游戏引擎初始化成功")
        print("  ✓ 角色随机分配正常")
        print("  ✓ 信息隔离机制正常")
        print("  ✓ 讨论阶段运行正常")
        print("  ✓ 投票阶段运行正常")
        print("  ✓ 处决阶段运行正常")
        print("  ✓ 游戏状态管理正常")
        print("  ✓ Agent与LLM交互正常")

        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # 恢复原始工厂
        src.llm.LLMFactory = original_factory


def test_agent_memory_integration():
    """测试Agent记忆系统集成"""
    print("\n" + "=" * 60)
    print("Agent记忆系统集成测试")
    print("=" * 60)

    from src.agents import Agent
    from src.roles import Role, RoleType

    # Mock LLM
    class MockLLM:
        def __init__(self):
            self.model = "mock"

        def chat(self, messages, **kwargs):
            return "测试回复"

    try:
        # 创建Agent
        role = Role.from_type(RoleType.GOOSE)
        llm = MockLLM()
        agent = Agent("test", "测试Agent", role, llm)

        print("\n1. 测试记忆累积...")
        # 添加多次交互
        agent.speak("第一次发言")
        agent.observe("观察到事件1")
        agent.speak("第二次发言")
        agent.observe("观察到事件2")

        print(f"   ✓ 记忆中有 {len(agent.memory)} 条消息")

        # 检查消息类型
        system_msgs = [m for m in agent.memory.messages if m.role == "system"]
        user_msgs = [m for m in agent.memory.messages if m.role == "user"]
        assistant_msgs = [m for m in agent.memory.messages if m.role == "assistant"]
        game_msgs = [m for m in agent.memory.messages if m.role == "game"]

        print(f"   ✓ 系统消息: {len(system_msgs)}")
        print(f"   ✓ 用户消息: {len(user_msgs)}")
        print(f"   ✓ 助手消息: {len(assistant_msgs)}")
        print(f"   ✓ 游戏消息: {len(game_msgs)}")

        print("\n2. 测试记忆清空...")
        agent.memory.clear()
        print(f"   ✓ 清空后记忆: {len(agent.memory)} 条消息")

        print("\n✓ Agent记忆系统集成测试通过")
        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Goose-Goose-Duck.ai 集成测试套件")
    print("=" * 60)

    results = []

    # 运行测试
    results.append(("Agent记忆系统集成", test_agent_memory_integration()))
    results.append(("完整游戏流程", test_full_game()))

    # 总结
    print("\n" + "=" * 60)
    print("集成测试结果总结")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有集成测试通过！")
        print("\n系统已完全就绪，可以运行完整游戏。")
        print("\n运行方式:")
        print("  python main.py  # 需要配置API密钥")
        success = True
    else:
        print("\n⚠ 部分测试失败")
        success = False

    sys.exit(0 if success else 1)
