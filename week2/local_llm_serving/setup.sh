#!/bin/bash

# vLLM Tool Calling Demo - Setup Script
# This script helps set up the environment for the demo

echo "======================================"
echo "vLLM Tool Calling Demo Setup"
echo "======================================"

# Check Python version
echo -e "\n1. Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then 
    echo "✅ Python $python_version is installed (>= $required_version required)"
else
    echo "❌ Python $python_version is too old. Please install Python >= $required_version"
    exit 1
fi

# Check CUDA availability
echo -e "\n2. Checking CUDA availability..."
if command -v nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA GPU detected:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
else
    echo "⚠️  No NVIDIA GPU detected. vLLM requires a CUDA-capable GPU."
    echo "   You can still install dependencies but won't be able to run the model locally."
fi

# Create virtual environment
echo -e "\n3. Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo -e "\n4. Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo -e "\n5. Installing requirements..."
pip install -r requirements.txt

# Check PyTorch CUDA
echo -e "\n6. Checking PyTorch CUDA support..."
python3 -c "import torch; print('✅ PyTorch CUDA available' if torch.cuda.is_available() else '❌ PyTorch CUDA not available')"

# Create .env file if it doesn't exist
echo -e "\n7. Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp env.example .env
    echo "✅ Created .env file from template"
else
    echo "✅ .env file already exists"
fi

# Create logs directory
echo -e "\n8. Creating logs directory..."
mkdir -p logs
echo "✅ Logs directory created"

# Optional: Install ModelScope for downloading from Chinese mirror
echo -e "\n9. Optional packages..."
read -p "Install ModelScope for downloading models from Chinese mirror? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pip install modelscope
    echo "✅ ModelScope installed"
fi

echo -e "\n======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Check system compatibility: python check_compatibility.py"
echo "3. Run the main script: python main.py"
echo ""
echo "The script will automatically detect your platform and use:"
echo "  - vLLM if you have an NVIDIA GPU"
echo "  - Ollama on Mac or systems without GPU"
echo ""
echo "For more information, see README.md"
