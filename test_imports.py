#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""

import os
import sys
from pathlib import Path

# Setup path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))
os.environ["PYTHONPATH"] = str(project_root)

print("🧪 Testing imports...")
print(f"📁 Project root: {project_root}")
print(f"🐍 Python path: {sys.path[:3]}...")  # Show first few entries
print(f"🌍 PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
print(f"📂 Current directory: {os.getcwd()}")

tests = [
    ("fastapi", "FastAPI web framework"),
    ("uvicorn", "ASGI server"),
    ("streamlit", "Streamlit dashboard"),
    ("backend.main", "Main FastAPI app"),
    ("backend.models.agent", "Agent models"),
    ("backend.models.workflow", "Workflow models"),
    ("backend.api.routes.agent_routes", "Agent API routes"),
    ("backend.streamlit_runner", "Streamlit runner"),
    ("streamlit_components.react_components", "Streamlit components"),
]

passed = 0
failed = 0

for module_name, description in tests:
    try:
        __import__(module_name)
        print(f"✅ {module_name:35} - {description}")
        passed += 1
    except ImportError as e:
        print(f"❌ {module_name:35} - {description}")
        print(f"   Error: {e}")
        failed += 1
    except Exception as e:
        print(f"⚠️  {module_name:35} - {description}")
        print(f"   Error: {e}")
        failed += 1

print(f"\n📊 Results: {passed} passed, {failed} failed")

if failed == 0:
    print("🎉 All imports successful! You can run the application.")
else:
    print("🚨 Some imports failed. Check the errors above.")
    print("\n🔧 Troubleshooting tips:")
    print("1. Run: pip install -r requirements.txt")
    print("2. Make sure you're in the project root directory")
    print("3. Try: python -m pip install -e .")
    print("4. Check Python version: python --version (need 3.8+)")