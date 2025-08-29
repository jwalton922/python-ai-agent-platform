#!/bin/bash

echo "================================"
echo "Async Chat Testing Setup"
echo "================================"

# Check if server is running
echo "Checking if server is running..."
curl -s http://localhost:8000/health > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Server not running. Please start it first:"
    echo "   python run_production.py"
    echo "   or"
    echo "   WORKERS=4 RELOAD=false python run_unified.py"
    exit 1
fi
echo "✅ Server is running"

# Create a test agent if needed
echo ""
echo "Creating test agent for async chat..."
curl -X POST http://localhost:8000/api/agents/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Async Test Agent",
    "instructions": "You are a helpful assistant for testing async chat. When asked, provide detailed responses that might take some time to generate.",
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "mcp_tool_permissions": []
  }' > /tmp/agent_result.json 2>/dev/null

if [ $? -eq 0 ]; then
    AGENT_ID=$(python3 -c "import json; print(json.load(open('/tmp/agent_result.json'))['id'])")
    echo "✅ Test agent created: $AGENT_ID"
else
    echo "⚠️  Could not create test agent (may already exist)"
fi

echo ""
echo "================================"
echo "Testing Instructions"
echo "================================"
echo ""
echo "1. API Testing:"
echo "   python test_async_chat.py"
echo ""
echo "2. UI Testing:"
echo "   - Open http://localhost:3000 (React dev)"
echo "   - Or http://localhost:8000/app (Production)"
echo "   - Go to Agent Chat"
echo "   - Toggle to 'Async' mode (purple button)"
echo "   - Send a message"
echo ""
echo "3. Monitor Activities:"
echo "   - Open http://localhost:8000/app"
echo "   - Go to Activity Monitor"
echo "   - Watch for events with chat_id"
echo ""
echo "4. Manual API Test:"
echo "   # Start async chat"
echo "   curl -X POST http://localhost:8000/api/chat/async \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"agent_id\": \"'$AGENT_ID'\", \"message\": \"Hello async\", \"chat_history\": []}'"
echo ""
echo "================================"