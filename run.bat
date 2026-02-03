@echo off
REM MedBot 快速启动脚本 (Windows)
REM 用法: 双击 run.bat

REM 停止已有进程
taskkill /F /IM python.exe /FI "WINDOWTITLE eq chainlit*" 2>nul

REM 激活虚拟环境
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo Starting MedBot...
echo Open: http://localhost:8000
echo Press Ctrl+C to stop
echo.

chainlit run app_chainlit.py --port 8000
