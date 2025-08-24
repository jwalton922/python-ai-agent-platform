# Troubleshooting Guide

## Module Not Found Errors

If you're getting "ModuleNotFoundError" or import errors, here are several solutions:

### Quick Fix - Test First

Run the import test to see what's failing:

```bash
python test_imports.py
```

This will show you exactly which modules are missing and provide specific guidance.

### Solution 1: Use the Setup Scripts

**Linux/Mac:**
```bash
./run.sh
```

**Windows:**
```batch
run.bat
```

**Python (Cross-platform):**
```bash
python start.py
```

### Solution 2: Manual Python Path Setup

```bash
# Linux/Mac
export PYTHONPATH="$(pwd):$PYTHONPATH"
python run_unified.py

# Windows (Command Prompt)
set PYTHONPATH=%CD%;%PYTHONPATH%
python run_unified.py

# Windows (PowerShell)
$env:PYTHONPATH="$(Get-Location);$env:PYTHONPATH"
python run_unified.py
```

### Solution 3: Install as Package

```bash
# Install in development mode
pip install -e .

# Then run
python run_unified.py
```

### Solution 4: Direct Module Execution

```bash
# Run as module from project root
python -m backend.main

# For Streamlit
python -m streamlit run streamlit_dashboard.py
```

## Common Issues and Solutions

### 1. "No module named 'backend'"

**Cause:** Python can't find the backend module.

**Solutions:**
- Make sure you're running from the project root directory
- Use `python start.py` instead of `python run_unified.py`
- Set PYTHONPATH: `export PYTHONPATH=$(pwd):$PYTHONPATH`

### 2. "No module named 'streamlit_components'"

**Cause:** Streamlit can't find the components.

**Solutions:**
- Run `python test_imports.py` to verify paths
- Use the provided shell scripts (`./run.sh`)
- Make sure you're in the project root directory

### 3. "ImportError: attempted relative import"

**Cause:** Running scripts from wrong directory or incorrect import syntax.

**Solutions:**
- Always run from the project root directory
- Use absolute imports in scripts
- Use `python -m module_name` syntax

### 4. Missing Dependencies

**Error:** Various import errors for packages like `fastapi`, `streamlit`, etc.

**Solutions:**
```bash
# Install all dependencies
pip install -r requirements.txt

# If using virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### 5. Port Already in Use

**Error:** `Address already in use`

**Solutions:**
```bash
# Find process using port 8000
lsof -i :8000          # Linux/Mac
netstat -ano | find "8000"  # Windows

# Kill the process
kill -9 <PID>          # Linux/Mac
taskkill /PID <PID> /F # Windows

# Or change port in .env
echo "PORT=8080" >> .env
```

### 6. Streamlit Won't Start

**Symptoms:** Streamlit proxy returns 502 errors

**Solutions:**
- Check if streamlit is installed: `pip show streamlit`
- Try manual start: `streamlit run streamlit_dashboard.py`
- Check logs in the FastAPI terminal
- Use `/streamlit/status` endpoint to check status

### 7. React Frontend Not Loading

**Symptoms:** `/app` route returns 404

**Solutions:**
```bash
# Build the React frontend
cd frontend
npm install
npm run build
cd ..

# Verify build exists
ls -la frontend/build/
```

### 8. API Endpoints Not Working

**Symptoms:** 404 errors for `/api/*` routes

**Solutions:**
- Verify FastAPI is running: `curl http://localhost:8000/health`
- Check API docs: `http://localhost:8000/api/docs`
- Verify environment variables in `.env`

## Environment-Specific Solutions

### Docker/Container Environments

```bash
# Set PYTHONPATH in Dockerfile
ENV PYTHONPATH=/app:$PYTHONPATH

# Or in docker-compose.yml
environment:
  - PYTHONPATH=/app
```

### Virtual Environments

```bash
# Create and activate venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Install with path setup
pip install -e .
```

### IDE/Editor Issues

**VS Code:**
- Add to `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "python.envFile": "${workspaceFolder}/.env"
}
```

**PyCharm:**
- Mark project root as "Sources Root"
- Set Python interpreter to virtual environment

## Verification Steps

1. **Test imports:** `python test_imports.py`
2. **Check health:** `curl http://localhost:8000/health`
3. **Verify Streamlit:** `curl http://localhost:8000/streamlit/status`
4. **Test API:** `curl http://localhost:8000/api/agents/`

## Still Having Issues?

1. **Check Python version:** `python --version` (need 3.8+)
2. **Verify project structure:**
   ```
   python-ai-agent-platform/
   ├── backend/
   ├── frontend/
   ├── streamlit_components/
   ├── requirements.txt
   ├── run_unified.py
   └── __init__.py
   ```
3. **Clean install:**
   ```bash
   rm -rf venv .venv __pycache__ */__pycache__ */*/__pycache__
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install -e .
   ```

4. **Debug mode:**
   ```bash
   export LOG_LEVEL=DEBUG
   python start.py
   ```

## Getting Help

If you're still having issues:

1. Run `python test_imports.py` and share the output
2. Check the exact error message and stack trace
3. Verify your environment:
   - Operating system
   - Python version
   - Virtual environment status
   - Current working directory

The most common solution is to ensure you're running from the project root directory and that PYTHONPATH is set correctly.