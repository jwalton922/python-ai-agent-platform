#!/usr/bin/env python3
"""
Debug script to show exactly what's happening with Python paths
"""

import os
import sys
from pathlib import Path

def debug_environment():
    """Show detailed environment information"""
    print("🔍 ENVIRONMENT DEBUG")
    print("=" * 50)
    
    # Basic info
    print(f"🐍 Python version: {sys.version}")
    print(f"📁 Current working directory: {os.getcwd()}")
    print(f"📂 Script location: {Path(__file__).parent.absolute()}")
    print(f"🌍 PYTHONPATH env var: {os.environ.get('PYTHONPATH', 'Not set')}")
    
    # Python path
    print(f"\n🛤️  sys.path (first 5 entries):")
    for i, path in enumerate(sys.path[:5]):
        print(f"   {i}: {path}")
    
    if len(sys.path) > 5:
        print(f"   ... and {len(sys.path) - 5} more entries")
    
    # Check if project root is in path
    project_root = Path(__file__).parent.absolute()
    in_path = str(project_root) in sys.path
    print(f"\n📍 Project root in sys.path: {'✅ Yes' if in_path else '❌ No'}")
    print(f"   Project root: {project_root}")
    
    return project_root

def check_directories():
    """Check if required directories exist"""
    project_root = Path(__file__).parent.absolute()
    
    dirs_to_check = [
        "backend",
        "backend/models", 
        "backend/api",
        "backend/api/routes",
        "streamlit_components",
    ]
    
    print(f"\n📂 DIRECTORY CHECK")
    print("-" * 30)
    
    for dir_name in dirs_to_check:
        dir_path = project_root / dir_name
        exists = dir_path.exists()
        has_init = (dir_path / "__init__.py").exists() if exists else False
        
        status = "✅" if exists else "❌"
        init_status = "📄" if has_init else "📄❌"
        
        print(f"{status} {dir_name:<25} {init_status if exists else ''}")
        
        if exists and not has_init and dir_name.startswith("backend"):
            print(f"   ⚠️  Missing __init__.py in {dir_name}")

def test_specific_imports():
    """Test the specific imports that are failing"""
    print(f"\n🧪 IMPORT TESTING")
    print("-" * 30)
    
    # Add project root to path first
    project_root = Path(__file__).parent.absolute()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        print(f"✅ Added project root to sys.path")
    
    imports_to_test = [
        "backend",
        "backend.models", 
        "backend.models.base",
        "backend.models.agent",
        "backend.models.workflow",
        "backend.models.activity",
        "backend.api",
        "backend.api.routes",
        "backend.main",
        "streamlit_components",
    ]
    
    for module_name in imports_to_test:
        try:
            __import__(module_name)
            print(f"✅ {module_name}")
        except ModuleNotFoundError as e:
            print(f"❌ {module_name}: {e}")
        except ImportError as e:
            print(f"⚠️  {module_name}: {e}")
        except Exception as e:
            print(f"🔴 {module_name}: {type(e).__name__}: {e}")

def provide_solutions():
    """Provide specific solutions based on findings"""
    print(f"\n💡 SOLUTIONS")
    print("-" * 30)
    
    project_root = Path(__file__).parent.absolute()
    
    print(f"Try these commands in order:")
    print(f"")
    print(f"1. 📍 Make sure you're in the project root:")
    print(f"   cd {project_root}")
    print(f"")
    print(f"2. 🔧 Run the fix script:")
    print(f"   python fix_imports.py")
    print(f"")
    print(f"3. 🚀 Run the direct launcher:")
    print(f"   python run_direct.py")
    print(f"")
    print(f"4. 🆘 If still failing, install as package:")
    print(f"   pip install -e .")
    print(f"   python run_unified.py")
    print(f"")
    print(f"5. 🔄 Alternative - manual path setup:")
    print(f"   export PYTHONPATH={project_root}")
    print(f"   python run_unified.py")

def main():
    """Main function"""
    project_root = debug_environment()
    check_directories()
    test_specific_imports()
    provide_solutions()
    
    print(f"\n" + "=" * 50)
    print(f"Debug complete. Run solutions above to fix the issue.")

if __name__ == "__main__":
    main()