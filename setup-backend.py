#!/usr/bin/env python3
"""
NewsInsight Backend Setup Script
"""

import os
import sys
import subprocess
import platform

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ is required. Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def setup_virtual_environment():
    """Set up Python virtual environment"""
    if os.path.exists('venv'):
        print("ℹ️  Virtual environment already exists")
        return True
    
    if not run_command("python -m venv venv", "Creating virtual environment"):
        return False
    
    return True

def activate_and_install():
    """Activate virtual environment and install dependencies"""
    system = platform.system()
    
    if system == "Windows":
        activate_cmd = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
    else:
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
    
    # Install requirements
    if not run_command(f"{pip_cmd} install -r requirements-backend.txt", "Installing Python dependencies"):
        return False
    
    return True

def create_env_file():
    """Create .env file for backend configuration"""
    env_file = ".env"
    
    if os.path.exists(env_file):
        print("ℹ️  .env file already exists")
        return
    
    print("📝 Creating .env file...")
    
    env_content = """# NewsInsight Backend Configuration

# AWS Configuration
AWS_REGION=us-west-2
DDB_TABLE=news_metadata
PROC_BUCKET=
RAW_BUCKET=

# Bedrock Configuration
MODEL_FAMILY=anthropic
BEDROCK_MODEL_ID=

# News API Keys (optional)
NEWSAPI_KEY=
GUARDIAN_KEY=

# Processing Configuration
PROCESSED_PREFIX=news-processed/
RAW_PREFIX=news-raw/

# Development
DEBUG_MODE=true
PORT=8000
"""
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env file")

def main():
    print("🚀 Setting up NewsInsight Backend...")
    print()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Set up virtual environment
    if not setup_virtual_environment():
        sys.exit(1)
    
    # Install dependencies
    if not activate_and_install():
        sys.exit(1)
    
    # Create environment file
    create_env_file()
    
    print()
    print("🎉 Backend setup complete!")
    print()
    print("📋 Next steps:")
    print("   1. Configure your .env file with AWS credentials")
    print("   2. Activate virtual environment:")
    
    system = platform.system()
    if system == "Windows":
        print("      venv\\Scripts\\activate")
    else:
        print("      source venv/bin/activate")
    
    print("   3. Start the backend server:")
    print("      python backend.py")
    print()
    print("🔧 Backend will be available at: http://localhost:8000")
    print("📚 API documentation at: http://localhost:8000/docs")
    print()
    print("⚠️  Important: Make sure to configure your AWS credentials and DynamoDB table!")

if __name__ == "__main__":
    main()