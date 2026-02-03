#!/bin/bash
# MedBot 一键设置脚本 / One-click Setup Script
# 用法 / Usage: bash setup.sh

set -e  # Exit on error

echo "=========================================="
echo "  MedBot Setup Script"
echo "=========================================="
echo ""

# Step 1: Check Python
echo "📦 Step 1: Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo "✅ Found $PYTHON_VERSION"
echo ""

# Step 2: Create virtual environment
echo "📦 Step 2: Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi
echo ""

# Step 3: Activate and install dependencies
echo "📦 Step 3: Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✅ Dependencies installed"
echo ""

# Step 4: Check .env file
echo "📦 Step 4: Checking API key..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️  Created .env file from template"
    echo "⚠️  Please edit .env and add your API key (choose one):"
    echo ""
    echo "   OPENAI_API_KEY=your_key    (Recommended)"
    echo "   DEEPSEEK_API_KEY=your_key  (Alternative)"
    echo ""
    echo "   Get keys at:"
    echo "   - OpenAI: https://platform.openai.com/"
    echo "   - DeepSeek: https://platform.deepseek.com/"
    echo ""
else
    echo "✅ .env file exists"
fi
echo ""

# Step 5: Download data (optional)
echo "📦 Step 5: Data setup..."
read -p "Download datasets now? This may take a few minutes. (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Downloading datasets..."
    python scripts/download_all.py
    echo "Building vector store..."
    python scripts/build_vectorstore.py
    echo "✅ Data setup complete"
else
    echo "⏭️  Skipped. Run these commands later:"
    echo "   python scripts/download_all.py"
    echo "   python scripts/build_vectorstore.py"
fi
echo ""

# Done
echo "=========================================="
echo "  ✅ Setup Complete!"
echo "=========================================="
echo ""
echo "To run the application:"
echo ""
echo "  Option A - Chainlit (Recommended):"
echo "    source venv/bin/activate"
echo "    chainlit run app_chainlit.py"
echo "    Open: http://localhost:8000"
echo ""
echo "  Option B - Gradio (Classic UI):"
echo "    source venv/bin/activate"
echo "    python app.py"
echo "    Open: http://localhost:7860"
echo ""
