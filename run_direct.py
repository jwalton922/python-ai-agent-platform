#!/usr/bin/env python3
"""
Direct runner that handles all path issues internally
Use this if you're getting "No module named backend.models" errors
"""

import os
import sys
import logging
from pathlib import Path

# =============================================================================
# PATH SETUP - MUST BE FIRST!
# =============================================================================

def setup_paths():
    """Setup all paths before any imports"""
    # Get absolute project root
    project_root = Path(__file__).parent.absolute()
    
    # Change to project directory first
    original_cwd = os.getcwd()
    os.chdir(project_root)
    
    # Add project root to Python path at the very beginning
    sys.path.insert(0, str(project_root))
    
    # Set environment variable for subprocesses
    os.environ["PYTHONPATH"] = str(project_root)
    
    print(f"🔧 Path setup complete:")
    print(f"   📁 Project root: {project_root}")
    print(f"   📂 Working dir: {os.getcwd()}")
    print(f"   🐍 Python path: {sys.path[0]}")
    
    return project_root, original_cwd

# Setup paths before ANY imports
PROJECT_ROOT, ORIGINAL_CWD = setup_paths()

# =============================================================================
# NOW WE CAN SAFELY IMPORT
# =============================================================================

try:
    import uvicorn
    print("✅ uvicorn imported successfully")
except ImportError as e:
    print(f"❌ Failed to import uvicorn: {e}")
    print("Run: pip install uvicorn")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_imports():
    """Test critical imports before starting server"""
    critical_modules = [
        ("backend.main", "Main FastAPI app"),
        ("backend.models.agent", "Agent models"),
        ("backend.models.workflow", "Workflow models"), 
        ("backend.api.routes.agent_routes", "Agent routes"),
        ("streamlit", "Streamlit dashboard"),
    ]
    
    logger.info("🧪 Testing critical imports...")
    
    failed_imports = []
    
    for module_name, description in critical_modules:
        try:
            __import__(module_name)
            logger.info(f"✅ {module_name}")
        except ImportError as e:
            logger.error(f"❌ {module_name}: {e}")
            failed_imports.append((module_name, str(e)))
        except Exception as e:
            logger.warning(f"⚠️ {module_name}: {e}")
    
    if failed_imports:
        logger.error("🚨 Critical imports failed!")
        for module, error in failed_imports:
            logger.error(f"   {module}: {error}")
        
        logger.info("🔧 Suggested fixes:")
        logger.info("   1. pip install -r requirements.txt")
        logger.info("   2. pip install -e .")
        logger.info("   3. python fix_imports.py")
        return False
    
    logger.info("✅ All critical imports successful!")
    return True

def check_frontend():
    """Check if React frontend is built"""
    frontend_build = PROJECT_ROOT / "frontend" / "build"
    if frontend_build.exists():
        logger.info("✅ React frontend build found")
        return True
    else:
        logger.warning("⚠️ React frontend not built - will be unavailable")
        logger.info("   To build: cd frontend && npm install && npm run build")
        return False

def main():
    """Main function"""
    logger.info("🚀 AI Agent Platform - Direct Runner")
    logger.info("=" * 50)
    
    # Test imports first
    if not test_imports():
        logger.error("❌ Import test failed - cannot start server")
        return False
    
    # Check frontend
    check_frontend()
    
    # Server configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    logger.info(f"🌐 Starting server on http://{host}:{port}")
    logger.info("📍 Available endpoints:")
    logger.info(f"   - Main Landing:        http://localhost:{port}/")
    logger.info(f"   - Streamlit Dashboard: http://localhost:{port}/streamlit")
    logger.info(f"   - React App:           http://localhost:{port}/app")
    logger.info(f"   - API Documentation:   http://localhost:{port}/api/docs")
    
    try:
        # Import the app after path setup
        from backend.main import app
        logger.info("✅ Successfully imported FastAPI app")
        
        # Run with uvicorn
        uvicorn.run(
            app,  # Pass the app directly instead of string
            host=host,
            port=port,
            reload=reload,
            log_level="info",
            access_log=True
        )
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        logger.error("🔧 Try running: python fix_imports.py")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down AI Agent Platform")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)