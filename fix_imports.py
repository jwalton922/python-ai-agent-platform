#!/usr/bin/env python3
"""
Emergency import fix script
Run this if you're getting "ModuleNotFoundError: No module named 'backend.models'"
"""

import os
import sys
from pathlib import Path

def fix_python_path():
    """Fix Python path for the current session"""
    # Get absolute project root
    project_root = Path(__file__).parent.absolute()
    
    print(f"🔧 Fixing Python path...")
    print(f"📁 Project root: {project_root}")
    print(f"📂 Current directory: {os.getcwd()}")
    
    # Change to project root
    os.chdir(project_root)
    print(f"✅ Changed to: {os.getcwd()}")
    
    # Add to Python path at the beginning
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        print(f"✅ Added to sys.path: {project_root}")
    else:
        print(f"ℹ️  Already in sys.path: {project_root}")
    
    # Set environment variable
    os.environ["PYTHONPATH"] = str(project_root)
    print(f"✅ Set PYTHONPATH: {project_root}")
    
    return project_root

def test_backend_imports():
    """Test if backend imports work"""
    tests = [
        "backend",
        "backend.models",
        "backend.models.base",
        "backend.models.agent", 
        "backend.models.workflow",
        "backend.models.activity",
        "backend.api",
        "backend.api.routes",
        "backend.main",
    ]
    
    print(f"\n🧪 Testing backend imports...")
    
    passed = 0
    failed = 0
    
    for module in tests:
        try:
            __import__(module)
            print(f"✅ {module}")
            passed += 1
        except ImportError as e:
            print(f"❌ {module}: {e}")
            failed += 1
        except Exception as e:
            print(f"⚠️  {module}: {e}")
    
    print(f"\n📊 Results: {passed} passed, {failed} failed")
    return failed == 0

def main():
    """Main function"""
    print("🚨 Backend Models Import Fix")
    print("=" * 40)
    
    # Fix the path
    project_root = fix_python_path()
    
    # Test imports
    if test_backend_imports():
        print("\n🎉 All backend imports working!")
        print("\n▶️  You can now run:")
        print("   python run_unified.py")
        print("   python -m uvicorn backend.main:app --reload")
        return True
    else:
        print("\n🚨 Some imports still failing!")
        print("\n🔧 Try these solutions:")
        
        # Check if __init__.py files exist
        init_files = [
            project_root / "backend" / "__init__.py",
            project_root / "backend" / "models" / "__init__.py", 
            project_root / "backend" / "api" / "__init__.py",
        ]
        
        missing_init = []
        for init_file in init_files:
            if not init_file.exists():
                missing_init.append(init_file)
        
        if missing_init:
            print("\n❌ Missing __init__.py files:")
            for f in missing_init:
                print(f"   {f}")
                # Create missing __init__.py files
                f.touch()
                print(f"   ✅ Created: {f}")
        
        print("\n🔄 Trying imports again...")
        if test_backend_imports():
            print("🎉 Fixed! All imports working now!")
            return True
        else:
            print("\n🆘 Still having issues. Try:")
            print("1. pip install -e .")
            print("2. Restart your terminal")  
            print("3. Make sure you're in the project root directory")
            return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)