#!/usr/bin/env python3
"""
Aurora Web Scraper Startup Script
Launches both backend proxy server and frontend web interface
"""

import subprocess
import time
import sys
import os
from threading import Thread

def start_backend_proxy():
    """Start the backend proxy server"""
    print("🔧 Starting Backend Proxy Server...")
    try:
        subprocess.run([sys.executable, "backend_proxy.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Backend proxy stopped by user")
    except Exception as e:
        print(f"❌ Error starting backend proxy: {e}")

def start_frontend():
    """Start the Flask frontend"""
    print("📱 Starting Frontend Web Interface...")
    try:
        subprocess.run([sys.executable, "frontend.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Frontend stopped by user")
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")

def main():
    print("🚀 Aurora Web Scraper")
    print("=" * 50)
    print("This will start both the backend proxy server and frontend web interface.")
    print("You can access the web interface at: http://localhost:8080")
    print("The backend proxy will run on: http://localhost:8000")
    print("=" * 50)
    
    # Check if required files exist
    required_files = ["backend_proxy.py", "frontend.py", "universal_product_extractor.py"]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        print("Please make sure all files are in the current directory.")
        return
    
    # Check if Flask is installed
    try:
        import flask
        print("✅ Flask is installed")
    except ImportError:
        print("❌ Flask is not installed. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "flask==3.0.0"], check=True)
        print("✅ Flask installed successfully")
    
    # Check if Playwright is installed
    try:
        import playwright
        print("✅ Playwright is installed")
    except ImportError:
        print("❌ Playwright is not installed. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
        subprocess.run([sys.executable, "-m", "playwright", "install"], check=True)
        print("✅ Playwright installed successfully")
    
    print("\n🎯 Starting Aurora Web Scraper...")
    print("📱 Frontend: http://localhost:8080")
    print("🔧 Backend: http://localhost:8000")
    print("⏹️  Press Ctrl+C to stop both servers")
    print("=" * 50)
    
    # Start backend proxy in a separate thread
    backend_thread = Thread(target=start_backend_proxy, daemon=True)
    backend_thread.start()
    
    # Wait a moment for backend to start
    time.sleep(2)
    
    # Start frontend in main thread
    start_frontend()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Aurora Web Scraper stopped by user")
        print("👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Please check the error message above and try again.") 