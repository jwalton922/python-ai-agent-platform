#!/bin/bash

echo "🚀 Setting up AI Agent Platform..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install Streamlit dependencies (optional)
echo "📦 Installing Streamlit dependencies..."
pip install -r requirements-streamlit.txt

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..

echo "✅ Setup complete!"
echo ""
echo "To start the platform:"
echo "  python3 run.py"
echo ""
echo "Or manually:"
echo "  Backend:  python3 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
echo "  Frontend: cd frontend && npm start"
echo "  Streamlit: streamlit run streamlit_dashboard.py"