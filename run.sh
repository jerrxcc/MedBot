#!/bin/bash
# MedBot 快速启动脚本
# 用法: ./run.sh 或 bash run.sh

# 先停止已有进程
pkill -f "chainlit run" 2>/dev/null

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Starting MedBot..."
echo "Open: http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

chainlit run app_chainlit.py --port 8000
