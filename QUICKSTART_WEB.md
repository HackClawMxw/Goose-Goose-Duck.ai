# Goose-Goose-Duck.ai 可视化系统 - 快速开始

## 系统要求

- Python 3.10+
- Node.js 18+
- LLM API 密钥（GLM / OpenAI / DeepSeek）

## 安装步骤

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 2. 安装前端依赖

```bash
cd frontend
npm install
```

### 3. 配置 API 密钥

设置环境变量：

```bash
# Windows CMD
set GLM_API_KEY=your_api_key_here

# Windows PowerShell
$env:GLM_API_KEY="your_api_key_here"

# Linux/Mac
export GLM_API_KEY=your_api_key_here
```

或者直接修改 `config.yaml` 文件中的 `api_key` 字段。

## 启动服务

### 方式一：使用启动脚本（推荐）

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

### 方式二：手动启动

**终端 1 - 启动后端:**
```bash
uvicorn backend.main:app --reload --port 8000
```

**终端 2 - 启动前端:**
```bash
cd frontend
npm run dev
```

## 访问应用

- **前端界面**: http://localhost:5173
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/health

## 使用流程

1. 打开浏览器访问 http://localhost:5173
2. 在大厅页面设置玩家数量和游戏速度
3. 点击"创建游戏"按钮
4. 进入游戏页面后，点击"开始游戏"
5. 观看 AI Agent 们进行游戏

## 功能说明

### 已实现功能

- 创建游戏并自动生成 AI 玩家
- 实时观看游戏进程（讨论、投票、处决）
- 暂停/继续游戏
- WebSocket 实时通信
- 游戏结束显示结果和角色揭示

### 游戏规则

- **鹅阵营**: 通过讨论和投票找出所有鸭子
- **鸭阵营**: 隐藏身份，当鸭子数量 >= 鹅数量时获胜
- **呆呆鸟**: 被投票出局即可获胜

## 故障排除

### 后端启动失败

1. 检查 Python 版本：`python --version`
2. 检查依赖是否安装：`pip list`
3. 检查 API 密钥是否设置

### 前端启动失败

1. 检查 Node.js 版本：`node --version`
2. 删除 node_modules 重新安装：
   ```bash
   cd frontend
   rm -rf node_modules
   npm install
   ```

### WebSocket 连接失败

1. 确认后端正在运行
2. 检查浏览器控制台是否有错误
3. 尝试刷新页面

## 开发模式

### 后端开发

```bash
# 带自动重载
uvicorn backend.main:app --reload --port 8000
```

### 前端开发

```bash
cd frontend
npm run dev
```

### 构建前端

```bash
cd frontend
npm run build
```

构建产物位于 `frontend/dist` 目录，后端会自动服务这些静态文件。
