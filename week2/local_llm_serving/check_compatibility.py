#!/usr/bin/env python3
"""
Check system compatibility for running vLLM tool calling demo
"""

import sys
import platform
import subprocess
import shutil


def check_system():
    """Check system compatibility"""
    print("="*60)
    print("🔍 System Compatibility Check")
    print("="*60)
    
    # Get system info
    system = platform.system()
    machine = platform.machine()
    python_version = sys.version_info
    
    print(f"\n📊 System Information:")
    print(f"  OS: {system} ({platform.platform()})")
    print(f"  Architecture: {machine}")
    print(f"  Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check for CUDA
    cuda_available = False
    gpu_info = None
    
    print(f"\n🎮 GPU Check:")
    
    if system == "Darwin":  # macOS
        print("  ❌ macOS detected - No CUDA support available")
        print("  ℹ️  Macs use Metal (Apple Silicon) or AMD/Intel GPUs")
        return False, "darwin"
    
    # Check for NVIDIA GPU
    if shutil.which("nvidia-smi"):
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                gpu_info = result.stdout.strip()
                print(f"  ✅ NVIDIA GPU found: {gpu_info}")
                cuda_available = True
            else:
                print("  ⚠️  nvidia-smi found but couldn't query GPU")
        except Exception as e:
            print(f"  ⚠️  Error checking GPU: {e}")
    else:
        print("  ❌ No NVIDIA GPU detected (nvidia-smi not found)")
    
    # Check PyTorch CUDA
    print(f"\n🔥 PyTorch CUDA Check:")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"  ✅ PyTorch CUDA is available")
            print(f"  CUDA version: {torch.version.cuda}")
            print(f"  Number of GPUs: {torch.cuda.device_count()}")
            if torch.cuda.device_count() > 0:
                print(f"  GPU 0: {torch.cuda.get_device_name(0)}")
        else:
            print("  ❌ PyTorch CUDA is not available")
            cuda_available = False
    except ImportError:
        print("  ⚠️  PyTorch not installed")
    
    return cuda_available, system.lower()


def provide_recommendations(cuda_available, system):
    """Provide recommendations based on system"""
    
    print("\n" + "="*60)
    print("💡 Recommendations")
    print("="*60)
    
    if cuda_available:
        print("\n✅ Your system supports vLLM!")
        print("\nNext steps:")
        print("1. Install requirements: pip install -r requirements.txt")
        print("2. Run the main script: python main.py")
        print("3. The script will automatically use vLLM")
        
    elif system == "darwin" or system.lower() == "darwin":  # macOS
        print("\n🍎 You're on macOS - will use Ollama")
        print("\n📋 Setup steps:\n")
        
        print("1️⃣  Install Ollama:")
        print("   brew install ollama")
        print("   ollama serve  # Run in separate terminal\n")
        
        print("2️⃣  Install a model with tool support:")
        print("   ollama pull qwen3:0.6b  # Default model for this project\n")
        
        print("3️⃣  Run the main script:")
        print("   python main.py")
        print("   # Will automatically use Ollama")
        
    elif system.lower() == "windows":  # Windows
        if not cuda_available:
            print("\n🪟 You're on Windows without CUDA - will use Ollama")
            print("\n📋 Setup steps:\n")
            
            print("1️⃣  Install Ollama:")
            print("   Download from: https://ollama.com/download/windows")
            print("   Run OllamaSetup.exe\n")
            
            print("2️⃣  Install a model:")
            print("   ollama pull qwen3:0.6b  # Default model for this project\n")
            
            print("3️⃣  Run the main script:")
            print("   python main.py")
            print("   # Will automatically use Ollama")
        
    else:  # Linux without CUDA
        print("\n🐧 You're on Linux without CUDA - will use Ollama")
        print("\n📋 Setup steps:\n")
        
        print("1️⃣  Install Ollama:")
        print("   curl -fsSL https://ollama.com/install.sh | sh")
        print("   systemctl start ollama  # Or: ollama serve\n")
        
        print("2️⃣  Install a model:")
        print("   ollama pull qwen3:0.6b  # Default model for this project\n")
        
        print("3️⃣  Run the main script:")
        print("   python main.py")
        print("   # Will automatically use Ollama")


def main():
    """Main compatibility check"""
    cuda_available, system = check_system()
    provide_recommendations(cuda_available, system)
    
    print("\n" + "="*60)
    print("For more details, see README.md")
    print("="*60)


if __name__ == "__main__":
    main()
