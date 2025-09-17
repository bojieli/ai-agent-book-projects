#!/bin/bash

# User Memory System Setup Script

echo "=========================================="
echo "User Memory System - Setup"
echo "=========================================="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate
echo "✓ Virtual environment activated"

# Install requirements
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    cp env.example .env
    echo "✓ Created .env file from template"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your MOONSHOT_API_KEY"
    echo "   Get your API key from: https://platform.moonshot.cn/"
else
    echo "✓ .env file already exists"
fi

# Create necessary directories
mkdir -p data/memories
mkdir -p data/conversations
mkdir -p data/locomo
mkdir -p results/locomo
mkdir -p logs
echo "✓ Created necessary directories"

# Run tests
echo ""
echo "Running system tests..."
python test_memory_system.py

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env and add your MOONSHOT_API_KEY"
echo "2. Run: python quickstart.py"
echo "3. Run: python main.py interactive <your_name>"
echo ""
echo "For more information, see README.md"
