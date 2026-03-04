"""
最小化测试 - 仅验证文件存在和基本语法
"""
import os
import sys

# 设置UTF-8编码输出
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 60)
print("Goose-Goose-Duck.ai 最小化测试")
print("=" * 60)

# 测试1: 检查关键文件是否存在
print("\n1. 检查文件结构...")
required_files = [
    "src/__init__.py",
    "src/roles/__init__.py",
    "src/roles/enums.py",
    "src/roles/role.py",
    "src/agents/__init__.py",
    "src/agents/agent.py",
    "src/agents/memory.py",
    "src/llm/__init__.py",
    "src/game/__init__.py",
    "src/game/game_engine.py",
    "main.py",
    "config.yaml",
    "requirements.txt"
]

missing_files = []
for file in required_files:
    if not os.path.exists(file):
        missing_files.append(file)
        print(f"  ✗ {file} 不存在")
    else:
        print(f"  ✓ {file}")

if missing_files:
    print(f"\n✗ 缺少 {len(missing_files)} 个文件")
    sys.exit(1)

print(f"\n✓ 所有 {len(required_files)} 个关键文件都存在")

# 测试2: 检查Python语法
print("\n2. 检查Python语法...")
import py_compile

python_files = [
    "src/roles/enums.py",
    "src/roles/role.py",
    "src/agents/agent.py",
    "src/agents/memory.py",
    "src/game/game_state.py",
    "src/game/game_engine.py"
]

syntax_errors = []
for file in python_files:
    if os.path.exists(file):
        try:
            py_compile.compile(file, doraise=True)
            print(f"  ✓ {file}")
        except py_compile.PyCompileError as e:
            syntax_errors.append((file, str(e)))
            print(f"  ✗ {file}: {e}")

if syntax_errors:
    print(f"\n✗ {len(syntax_errors)} 个文件有语法错误")
    sys.exit(1)

print(f"\n✓ 所有 {len(python_files)} 个Python文件语法正确")

# 测试3: 尝试导入模块
print("\n3. 测试模块导入...")
try:
    # 添加src到路径
    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

    from src.roles.enums import RoleType, Camp
    print("  ✓ src.roles.enums 导入成功")

    from src.roles.role import Role
    print("  ✓ src.roles.role 导入成功")

    from src.agents.memory import AgentMemory
    print("  ✓ src.agents.memory 导入成功")

    from src.game.game_state import GameState
    print("  ✓ src.game.game_state 导入成功")

    print("\n✓ 所有核心模块导入成功")

except Exception as e:
    print(f"\n✗ 模块导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试4: 测试基本功能
print("\n4. 测试基本功能...")
try:
    # 测试角色创建
    role = Role.from_type(RoleType.GOOSE)
    print(f"  ✓ 创建角色: {role.name}")

    # 测试记忆系统
    memory = AgentMemory(max_history=10)
    memory.add_system_message("测试")
    print(f"  ✓ 记忆系统: {len(memory)} 条消息")

    # 测试游戏状态
    state = GameState()
    state.alive_players = ["p1", "p2"]
    state.add_vote("p1", "p2")
    winner = state.get_vote_winner()
    print(f"  ✓ 游戏状态: 投票获胜者={winner}")

    print("\n✓ 基本功能测试通过")

except Exception as e:
    print(f"\n✗ 功能测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 总结
print("\n" + "=" * 60)
print("✓ 所有测试通过！")
print("=" * 60)
print("\n项目结构完整，代码语法正确，核心功能可用。")
print("\n下一步:")
print("  1. 安装依赖: pip install -r requirements.txt")
print("  2. 配置API密钥: 复制 .env.example 为 .env")
print("  3. 运行游戏: python main.py")
print("=" * 60)
