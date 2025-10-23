#!/usr/bin/env python3
"""
Setup script for ChatGPT Clone application.
This script helps set up the environment and run the application.
"""

import os
import sys
import subprocess
import shutil

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"   Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} is compatible")
    return True

def setup_environment():
    """Set up the environment"""
    print("\n🚀 Setting up ChatGPT Clone Environment")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        return False
    
    # Create .env file if it doesn't exist
    if not os.path.exists('.env'):
        print("📝 Creating .env file...")
        with open('.env', 'w') as f:
            f.write("SECRET_KEY=django-insecure-change-this-in-production-12345\n")
            f.write("DEBUG=True\n")
            f.write("GEMINI_API_KEY=your-gemini-api-key-here\n")
        print("✅ .env file created")
    else:
        print("✅ .env file already exists")
    
    # Run migrations
    if not run_command("python manage.py makemigrations", "Creating database migrations"):
        return False
    
    if not run_command("python manage.py migrate", "Applying database migrations"):
        return False
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Get a Gemini API key from: https://makersuite.google.com/app/apikey")
    print("2. Edit the .env file and add your API key")
    print("3. Run: python manage.py runserver")
    print("4. Open http://localhost:8000 in your browser")
    
    return True

def main():
    """Main setup function"""
    print("🤖 ChatGPT Clone Setup Script")
    print("=" * 50)
    
    if setup_environment():
        print("\n✨ Ready to chat with AI!")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
