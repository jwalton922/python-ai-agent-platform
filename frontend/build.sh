#!/bin/bash

# Build script for React app with path prefix support
# Usage: ./build.sh [path-prefix]
# Example: ./build.sh /app

PREFIX=${1:-"/app"}

echo "🚀 Building React app with path prefix: $PREFIX"
echo "================================================"

# Clean previous build
echo "🧹 Cleaning previous build..."
rm -rf build

# Set the PUBLIC_URL environment variable for the build
export PUBLIC_URL=$PREFIX

# Run the build
echo "🔨 Building React app..."
npm run build

echo ""
echo "✅ Build complete!"
echo "================================================"
echo "📁 Build output: ./build"
echo "🌐 App will be served at: $PREFIX"
echo ""
echo "📝 Notes:"
echo "  - The app is configured to be served at path: $PREFIX"
echo "  - Make sure your server serves the build folder at this path"
echo "  - For FastAPI, this is already configured in backend/main.py"