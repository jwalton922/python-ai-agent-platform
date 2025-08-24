#!/usr/bin/env python3
"""
Alternative startup script with better module resolution
"""

import os
import sys
from pathlib import Path

def setup_python_path():
    """Setup Python path for proper module resolution"""
    # Get absolute path to project root
    project_root = Path(__file__).parent.absolute()
    
    # Add to Python path if not already there
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Set PYTHONPATH environment variable
    current_pythonpath = os.environ.get("PYTHONPATH", "")
    if str(project_root) not in current_pythonpath:
        if current_pythonpath:
            os.environ["PYTHONPATH"] = f"{project_root}:{current_pythonpath}"
        else:
            os.environ["PYTHONPATH"] = str(project_root)
    
    print(f"✅ Python path configured: {project_root}")
    print(f"✅ PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    
    return project_root

def main():
    """Main entry point"""
    project_root = setup_python_path()
    
    # Change to project directory
    os.chdir(project_root)
    print(f"✅ Changed directory to: {os.getcwd()}")
    
    # Import after path is set up
    try:
        from run_unified import main as run_main
        print("✅ Successfully imported run_unified")
        run_main()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("🔧 Trying alternative import method...")
        
        # Alternative: execute the file directly
        exec(open("run_unified.py").read())

if __name__ == "__main__":
    main()