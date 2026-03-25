#!/usr/bin/env python3
"""Setup script for Voice Claude Assistant"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def print_header(text):
    """Print formatted header"""
    print(f"\n{'='*50}")
    print(f"  {text}")
    print(f"{'='*50}\n")


def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python 3.9 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python {version.major}.{version.minor} detected")
    return True


def check_system_dependencies():
    """Check and install system dependencies"""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        print("🍎 macOS detected")
        
        # Check for Homebrew
        if subprocess.run(["which", "brew"], capture_output=True).returncode != 0:
            print("❌ Homebrew not found. Please install from https://brew.sh")
            return False
            
        # Check for PortAudio
        if subprocess.run(["brew", "list", "portaudio"], capture_output=True).returncode != 0:
            print("📦 Installing PortAudio...")
            subprocess.run(["brew", "install", "portaudio"])
        else:
            print("✅ PortAudio already installed")
            
    elif system == "Linux":
        print("🐧 Linux detected")
        print("📦 Please ensure portaudio19-dev is installed:")
        print("   sudo apt-get install portaudio19-dev")
        
    return True


def create_env_file():
    """Create .env file from example"""
    env_path = Path("config/.env")
    example_path = Path("config/.env.example")
    
    if env_path.exists():
        print("✅ .env file already exists")
        return
        
    if example_path.exists():
        print("📝 Creating .env file from example...")
        env_path.write_text(example_path.read_text())
        print("⚠️  Please edit config/.env and add your API keys!")
    else:
        print("❌ .env.example not found")


def install_python_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    
    # Upgrade pip
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    # Install requirements
    result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    if result.returncode == 0:
        print("✅ Python dependencies installed successfully")
        return True
    else:
        print("❌ Failed to install dependencies")
        return False


def test_imports():
    """Test critical imports"""
    print("🧪 Testing imports...")
    
    critical_imports = [
        ("anthropic", "Anthropic API"),
        ("pyaudio", "Audio I/O"),
        ("speech_recognition", "Speech Recognition"),
        ("gtts", "Text-to-Speech"),
    ]
    
    all_good = True
    for module, name in critical_imports:
        try:
            __import__(module)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ❌ {name}")
            all_good = False
            
    return all_good


def main():
    """Main setup function"""
    print_header("Voice Claude Assistant Setup")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
        
    # Check system dependencies
    if not check_system_dependencies():
        sys.exit(1)
        
    # Create virtual environment if not already in one
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("\n⚠️  Not in a virtual environment!")
        print("   Recommended: python3 -m venv venv && source venv/bin/activate")
        response = input("   Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(0)
            
    # Install dependencies
    if not install_python_dependencies():
        sys.exit(1)
        
    # Create .env file
    create_env_file()
    
    # Test imports
    test_imports()
    
    print_header("Setup Complete!")
    
    print("📋 Next steps:")
    print("1. Edit config/.env and add your API keys:")
    print("   - ANTHROPIC_API_KEY (required)")
    print("   - PORCUPINE_ACCESS_KEY (optional)")
    print("\n2. Run the assistant:")
    print("   python -m src.main")
    print("\n3. Say 'Hey Claude' or press SPACE to activate!")
    
    print("\n🔗 Get API keys:")
    print("   Anthropic: https://console.anthropic.com/")
    print("   Porcupine: https://console.picovoice.ai/")


if __name__ == "__main__":
    main()