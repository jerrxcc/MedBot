#!/bin/bash
# MedBot 停止脚本
# 用法: ./stop.sh 或 bash stop.sh

pkill -f "chainlit run" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "MedBot stopped."
else
    echo "MedBot is not running."
fi
