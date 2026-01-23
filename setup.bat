@echo off
REM MedBot 一键设置脚本 (Windows)
REM 用法: 双击运行 setup.bat

echo ==========================================
echo   MedBot Setup Script (Windows)
echo ==========================================
echo.

REM Step 1: Check Python
echo [Step 1] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)
python --version
echo.

REM Step 2: Create virtual environment
echo [Step 2] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo Created virtual environment
) else (
    echo Virtual environment already exists
)
echo.

REM Step 3: Activate and install dependencies
echo [Step 3] Installing dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo Dependencies installed
echo.

REM Step 4: Check .env file
echo [Step 4] Checking API key...
if not exist ".env" (
    copy .env.example .env
    echo Created .env file from template
    echo.
    echo [IMPORTANT] Please edit .env and add your DEEPSEEK_API_KEY
    echo Get your API key at: https://platform.deepseek.com/
    echo.
) else (
    echo .env file exists
)
echo.

REM Step 5: Data setup prompt
echo [Step 5] Data setup...
set /p DOWNLOAD="Download datasets now? (y/n): "
if /i "%DOWNLOAD%"=="y" (
    echo Downloading datasets...
    python scripts\download_all.py
    echo Building vector store...
    python scripts\build_vectorstore.py
    echo Data setup complete
) else (
    echo Skipped. Run these commands later:
    echo   python scripts\download_all.py
    echo   python scripts\build_vectorstore.py
)
echo.

REM Done
echo ==========================================
echo   Setup Complete!
echo ==========================================
echo.
echo To run the application:
echo.
echo   Option A - Gradio:
echo     venv\Scripts\activate
echo     python app.py
echo     Open: http://localhost:7860
echo.
echo   Option B - Chainlit:
echo     venv\Scripts\activate
echo     pip install chainlit
echo     chainlit run app_chainlit.py
echo     Open: http://localhost:8000
echo.
pause
