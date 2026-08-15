#!/bin/bash

# IMO Project Environment Setup Script
# This script creates a new conda environment and installs all necessary dependencies

echo "🚀 Setting up IMO Project Environment..."

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "❌ Error: conda is not installed or not in PATH"
    echo "Please install Miniconda or Anaconda first"
    exit 1
fi

# Environment name
ENV_NAME="imo_env"

echo "📦 Creating conda environment: $ENV_NAME"

# Create new conda environment with Python 3.11
conda create -n $ENV_NAME python=3.11 -y

if [ $? -ne 0 ]; then
    echo "❌ Failed to create conda environment"
    exit 1
fi

echo "✅ Conda environment created successfully"

# Activate the environment
echo "🔄 Activating environment..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate $ENV_NAME

if [ $? -ne 0 ]; then
    echo "❌ Failed to activate conda environment"
    exit 1
fi

echo "✅ Environment activated"

# Install requirements
echo "📥 Installing dependencies from requirements.txt..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    echo "You can try installing them manually:"
    echo "conda activate $ENV_NAME"
    echo "pip install -r requirements.txt"
    exit 1
fi

echo "✅ Dependencies installed successfully"

# Install AWorld framework in development mode
echo "🔧 Installing AWorld framework..."
cd ../../../
pip install -e .

if [ $? -ne 0 ]; then
    echo "⚠️  Warning: Failed to install AWorld framework in development mode"
    echo "You may need to install it manually:"
    echo "cd ../../../ && pip install -e ."
fi

echo "✅ AWorld framework installed"

# Go back to imo directory
cd AWorld/examples/imo

echo ""
echo "🎉 Environment setup completed successfully!"
echo ""
echo "To use this environment:"
echo "1. Activate the environment: conda activate $ENV_NAME"
echo "2. Navigate to the imo directory: cd AWorld/examples/imo"
echo "3. Run your script: python run.py --q imo6"
echo ""
echo "To deactivate the environment: conda deactivate" 