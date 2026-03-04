# Goose-Goose-Duck.ai 快速开始指南

## 简介

Goose-Goose-Duck.ai 是一个基于大语言模型（LLM）的多智能体对话系统，模拟经典的社交推理游戏（类似狼人杀/鹅鸭杀）。每个Agent由一个独立的LLM驱动，扮演角色进行对话、推理和投票。

## 特性

- 🤖 **多Agent对话**：多个LLM Agent扮演角色进行自然对话
- 🎭 **角色扮演**：支持多种角色（鹅、鸭子、呆呆鸟）和阵营
- 🔒 **信息隔离**：不同阵营知道的信息不同（鸭阵营互相认识）
- 💬 **对话管理**：完整的对话历史记录和上下文管理
- 🎮 **游戏流程**：自动化的游戏流程（讨论→投票→处决）
- 📊 **结果分析**：游戏总结和历史记录

## 安装

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/Goose-Goose-Duck.ai.git
cd Goose-Goose-Duck.ai
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置API密钥

复制环境变量示例文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的API密钥：

```env
# GLM API配置（推荐）
GLM_API_KEY=your_glm_api_key_here

# 或使用OpenAI API
OPENAI_API_KEY=your_openai_api_key_here

# 或使用DeepSeek API
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

### 4. 配置游戏（可选）

编辑 `config.yaml` 文件来自定义游戏设置：

```yaml
# 修改玩家数量
game:
  player_count: 8

# 修改角色分配
  roles:
    goose:
      - name: "鹅"
        count: 4
    duck:
      - name: "鸭子"
        count: 3
    neutral:
      - name: "呆呆鸟"
        count: 1
```

## 快速开始

### 运行默认游戏

```bash
python main.py
```

### 运行示例

```bash
# 基础示例
python examples/basic_game.py

# 自定义游戏
python examples/custom_game.py
```

## 游戏流程

1. **初始化**：系统随机分配角色给每个Agent
2. **讨论阶段**：每个Agent轮流发言，表达观点
3. **投票阶段**：每个Agent投票选出最可疑的人
4. **处决阶段**：得票最多的玩家出局
5. **判定胜负**：检查游戏是否结束，否则进入下一轮

## 胜负条件

- **鹅阵营**：消灭所有鸭子
- **鸭阵营**：鸭子数量 ≥ 鹅数量
- **呆呆鸟**：被投票出局

## 项目结构

```
Goose-Goose-Duck.ai/
├── src/                    # 源代码
│   ├── llm/               # LLM接口封装
│   ├── agents/            # Agent类和记忆系统
│   ├── roles/             # 角色定义
│   ├── game/              # 游戏引擎和状态管理
│   └── utils/             # 工具函数
├── examples/              # 示例代码
├── config.yaml            # 配置文件
├── .env                   # 环境变量
├── main.py                # 主程序入口
└── requirements.txt       # 依赖包
```

## 核心概念

### Agent（智能体）

每个Agent是一个独立的角色，由LLM驱动：
- 拥有角色身份和阵营
- 可以发言和投票
- 拥有记忆系统，记录对话历史
- 根据角色目标制定策略

### 信息隔离

不同阵营的Agent知道的信息不同：
- 鸭阵营成员互相认识
- 鹅阵营不知道谁是鸭子
- 中立角色独立行动

### 记忆系统

每个Agent维护自己的记忆：
- 短期记忆：当前对话历史
- 角色信息：身份和目标
- 推理知识：从对话中推断的信息

## 自定义扩展

### 添加新角色

在 `src/roles/enums.py` 中添加新角色类型：

```python
class RoleType(Enum):
    GOOSE = "鹅"
    DUCK = "鸭子"
    DODO = "呆呆鸟"
    # 添加新角色
    FALCON = "猎鹰"  # 新角色
```

在 `ROLE_DESCRIPTIONS` 中添加角色描述：

```python
ROLE_DESCRIPTIONS = {
    # ...
    RoleType.FALCON: {
        "name": "猎鹰",
        "camp": "中立阵营",
        "description": "你是中立阵营的猎鹰...",
        "goal": "...",
        "abilities": [...]
    }
}
```

### 使用不同的LLM

在 `config.yaml` 中切换模型：

```yaml
llm:
  model: "gpt-4"  # 或 "deepseek-chat"
```

## 常见问题

### Q: 如何获取API密钥？

A:
- GLM: https://open.bigmodel.cn/
- OpenAI: https://platform.openai.com/
- DeepSeek: https://platform.deepseek.com/

### Q: 游戏运行很慢怎么办？

A: 可以在 `config.yaml` 中调整：
- 减少玩家数量
- 减少讨论轮次
- 使用更快的模型（如 glm-4-flash）

### Q: 如何查看详细日志？

A: 修改 `config.yaml` 中的日志级别：

```yaml
logging:
  level: "DEBUG"
```

## 下一步计划

- [ ] 添加更多角色和能力
- [ ] 实现地图和移动系统
- [ ] 添加可视化界面
- [ ] 支持人类玩家参与
- [ ] 实现RAG增强记忆系统

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 联系方式

如有问题或建议，欢迎通过 Issue 与我们交流。
