#!/usr/bin/env python3
"""
Unified launcher for the AI Agent Platform
Starts both FastAPI backend and Streamlit frontend in a single command
"""
import subprocess
import sys
import time
import signal
import os
from pathlib import Path

def start_services():
    """Start FastAPI backend and Streamlit frontend"""
    print("🚀 Starting AI Agent Platform - Unified Dashboard")
    print("=" * 60)
    
    # Start FastAPI backend
    print("📡 Starting FastAPI backend on port 8003...")
    backend_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "backend.main:app",
        "--host", "0.0.0.0", "--port", "8003", "--reload"
    ])
    
    # Wait a moment for backend to start
    time.sleep(3)
    
    # Start Streamlit frontend
    print("🌐 Starting Streamlit frontend on port 8501...")
    streamlit_process = subprocess.Popen([
        "streamlit", "run", "streamlit_dashboard.py",
        "--server.port", "8501",
        "--server.headless", "false",
        "--browser.gatherUsageStats", "false"
    ])
    
    print("\n✅ Both services are starting...")
    print("📡 FastAPI Backend: http://localhost:8003")
    print("📚 API Documentation: http://localhost:8003/docs")
    print("🌐 Streamlit Frontend: http://localhost:8501")
    print("\nPress Ctrl+C to stop all services")
    print("=" * 60)
    
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down services...")
        backend_process.terminate()
        streamlit_process.terminate()
        print("✅ All services stopped.")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Keep both processes running
        while True:
            if backend_process.poll() is not None:
                print("❌ Backend process died!")
                break
            if streamlit_process.poll() is not None:
                print("❌ Frontend process died!")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    start_services()