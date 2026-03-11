#!/bin/bash

echo "Starting Goose-Goose-Duck.ai..."

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 启动后端
echo "Starting Backend Server..."
uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 启动前端
echo "Starting Frontend Dev Server..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "  Goose-Goose-Duck.ai is starting!"
echo "========================================"
echo ""
echo "  Backend API:  http://localhost:8000"
echo "  API Docs:     http://localhost:8000/docs"
echo "  Frontend:     http://localhost:5173"
echo ""
echo "========================================"
echo ""
echo "Press Ctrl+C to stop all servers..."

# 等待子进程
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
