#!/bin/bash

# Bash startup script for AI Agent Platform

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to project directory
cd "$SCRIPT_DIR"

# Set Python path
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

echo "🚀 Starting AI Agent Platform"
echo "📁 Project root: $SCRIPT_DIR"
echo "🐍 PYTHONPATH: $PYTHONPATH"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "🌐 Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "🌐 Activating virtual environment..."
    source .venv/bin/activate
fi

# Install dependencies if requirements.txt is newer than last install
if [ requirements.txt -nt .last_install ] || [ ! -f .last_install ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    touch .last_install
fi

# Run the application
echo "🎯 Starting unified server..."
python run_unified.py