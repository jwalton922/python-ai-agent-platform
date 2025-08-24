#!/bin/bash

# Sandbox runner for Jupyter notebook proxy environment
# This script configures the application to work behind a path prefix

echo "🚀 AI Agent Platform - Sandbox/Jupyter Proxy Mode"
echo "=================================================="

# Set the base path for the proxy environment
export BASE_PATH="/notebook/pxj363/josh-testing/proxy/8000"
export PROXY_PREFIX="/notebook/pxj363/josh-testing/proxy/8000"
export PUBLIC_URL="$BASE_PATH/app"

# Python path setup
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Server configuration
export HOST="0.0.0.0"
export PORT="8000"
export RELOAD="false"

echo "📍 Configuration:"
echo "   Base Path: $BASE_PATH"
echo "   API URL: $BASE_PATH/api"
echo "   App URL: $BASE_PATH/app"
echo "   Streamlit URL: $BASE_PATH/streamlit"
echo ""

# Check if React app needs to be built
FRONTEND_BUILD="frontend/build"
if [ ! -d "$FRONTEND_BUILD" ]; then
    echo "⚠️  React app not built. Building now..."
    cd frontend
    PUBLIC_URL="$BASE_PATH/app" npm run build
    cd ..
    echo "✅ React app built with correct path prefix"
else
    echo "ℹ️  React build found. If URLs don't work correctly, rebuild with:"
    echo "   cd frontend && PUBLIC_URL='$BASE_PATH/app' npm run build"
fi

echo ""
echo "🌐 Starting server..."
echo "=================================================="
echo "Access the application at:"
echo "   Main Landing: http://localhost:8000$BASE_PATH/"
echo "   React App: http://localhost:8000$BASE_PATH/app"
echo "   Streamlit: http://localhost:8000$BASE_PATH/streamlit"
echo "   API Docs: http://localhost:8000$BASE_PATH/api/docs"
echo ""
echo "Or through your Jupyter proxy at your external URL + $BASE_PATH"
echo "=================================================="

# Run the Python server with sandbox configuration
python3 run_sandbox.py