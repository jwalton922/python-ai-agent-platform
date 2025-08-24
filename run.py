#!/usr/bin/env python3
"""
Development server runner for AI Agent Platform
"""
import subprocess
import sys
import signal
import time
from pathlib import Path

def run_backend():
    """Run the FastAPI backend server"""
    print("🚀 Starting FastAPI backend...")
    return subprocess.Popen([
        sys.executable, "-m", "uvicorn", 
        "backend.main:app",
        "--reload",
        "--host", "0.0.0.0", 
        "--port", "8000"
    ])

def run_frontend():
    """Run the React frontend development server"""
    print("⚛️  Starting React frontend...")
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found!")
        return None
    
    return subprocess.Popen([
        "npm", "start"
    ], cwd=frontend_dir)

def run_streamlit():
    """Run the Streamlit dashboard"""
    print("📊 Starting Streamlit dashboard...")
    return subprocess.Popen([
        "streamlit", "run", "streamlit_dashboard.py",
        "--server.port", "8501"
    ])

def main():
    processes = []
    
    try:
        # Start backend
        backend_proc = run_backend()
        if backend_proc:
            processes.append(backend_proc)
        
        # Wait a bit for backend to start
        time.sleep(3)
        
        # Start frontend
        frontend_proc = run_frontend()
        if frontend_proc:
            processes.append(frontend_proc)
        
        # Start streamlit
        streamlit_proc = run_streamlit()
        if streamlit_proc:
            processes.append(streamlit_proc)
        
        print("\n" + "="*60)
        print("🎉 AI Agent Platform is starting up!")
        print("="*60)
        print("📡 Backend API:      http://localhost:8000")
        print("📡 API Docs:         http://localhost:8000/docs")
        print("⚛️  React Frontend:   http://localhost:3000")
        print("📊 Streamlit Dashboard: http://localhost:8501")
        print("="*60)
        print("Press Ctrl+C to stop all servers")
        
        # Wait for all processes
        for proc in processes:
            proc.wait()
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
        for proc in processes:
            proc.terminate()
        
        # Wait a bit for graceful shutdown
        time.sleep(2)
        
        # Force kill if still running
        for proc in processes:
            if proc.poll() is None:
                proc.kill()
        
        print("✅ All servers stopped")

if __name__ == "__main__":
    main()