#!/usr/bin/env python3
"""
Production startup script for AI Agent Platform
Runs FastAPI backend with multiple workers for better concurrency
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path FIRST
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Now we can import uvicorn after path is set
import uvicorn

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_frontend_build():
    """Check if React frontend is built"""
    frontend_build = Path(__file__).parent / "frontend" / "build"
    if not frontend_build.exists():
        logger.warning(
            "React frontend build not found. Run 'cd frontend && npm install && npm run build' to build it."
        )
        return False
    return True

def main():
    """Run the application in production mode"""
    logger.info("🚀 Starting AI Agent Platform - Production Server")
    
    # Check frontend
    has_frontend = check_frontend_build()
    if has_frontend:
        logger.info("✅ React frontend build found")
    else:
        logger.info("⚠️ React frontend not built - will be unavailable")
    
    # Set environment variables
    os.environ["PYTHONPATH"] = str(project_root)
    
    # Production server configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    workers = int(os.getenv("WORKERS", "4"))  # Default to 4 workers for production
    
    logger.info(f"🌐 Starting production server on http://{host}:{port}")
    logger.info(f"⚙️  Worker processes: {workers}")
    logger.info("📍 Available endpoints:")
    logger.info(f"   - Main Landing:        http://localhost:{port}/")
    logger.info(f"   - Streamlit Dashboard: http://localhost:{port}/streamlit")
    if has_frontend:
        logger.info(f"   - React App:           http://localhost:{port}/app")
    logger.info(f"   - API Documentation:   http://localhost:{port}/api/docs")
    logger.info(f"   - Health Check:        http://localhost:{port}/health")
    logger.info("")
    logger.info("🏭 Running in PRODUCTION mode (no auto-reload)")
    
    # Run the FastAPI app with uvicorn in production mode
    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        workers=workers,  # Multiple workers for better concurrency
        log_level="info",
        access_log=True,
        reload=False  # Explicitly disable reload for production
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down AI Agent Platform")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Failed to start: {e}")
        sys.exit(1)