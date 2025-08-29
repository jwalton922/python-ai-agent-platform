# Async Chat Testing Guide

## Overview
The async chat feature allows long-running LLM and tool calls to be processed in the background without blocking other API requests. The chat UI includes a toggle to switch between sync and async modes.

## How It Works

### Backend Flow
1. **Client initiates async chat** → Returns immediately with a UUID
2. **Background task processes** → LLM calls, tool executions logged with UUID
3. **Client polls for status** → Gets progress updates and final result
4. **Timeout after 90 seconds** → Automatic cleanup if no completion

### Frontend Flow
1. **Toggle async mode** → Purple "Async" button in chat header
2. **Send message** → Shows processing placeholder with progress steps
3. **Real-time updates** → Polls every second showing progress
4. **Final result** → Replaces placeholder when complete

## Testing Instructions

### 1. Start the Server
```bash
# For development (single worker, auto-reload)
python run_unified.py

# For production testing (multiple workers)
python run_production.py
```

### 2. Test via API

#### Start Async Chat
```bash
curl -X POST http://localhost:8000/api/chat/async \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "your-agent-id",
    "message": "Create a complex workflow that analyzes emails",
    "chat_history": []
  }'
```

Response:
```json
{
  "chat_id": "uuid-here",
  "status": "pending",
  "message": "Chat processing started in background"
}
```

#### Poll for Status
```bash
curl http://localhost:8000/api/chat/async/{chat_id}/status
```

Response shows progress:
```json
{
  "chat_id": "uuid-here",
  "status": "processing",
  "progress": [
    {"timestamp": "...", "type": "created", "message": "Chat session created"},
    {"timestamp": "...", "type": "agent_loaded", "message": "Loaded agent: Assistant"},
    {"timestamp": "...", "type": "llm_call_start", "message": "Calling LLM for response generation"},
    {"timestamp": "...", "type": "tool_execution", "message": "Executing tool: workflow_tool (create)"}
  ],
  "result": null,
  "error": null,
  "created_at": "...",
  "updated_at": "..."
}
```

When complete:
```json
{
  "chat_id": "uuid-here",
  "status": "completed",
  "progress": [...],
  "result": {
    "message": "I've created a workflow for you...",
    "tool_calls": [...],
    "success": true,
    "workflow_generated": {...}
  },
  "created_at": "...",
  "updated_at": "..."
}
```

### 3. Test via React UI

1. **Navigate to Chat**: http://localhost:8000/app → Agent Chat
2. **Select an agent** with tools (email_tool, workflow_tool, etc.)
3. **Toggle Async Mode**: Click the "Sync" button to switch to "Async" (purple)
4. **Send a complex request**:
   - "Create a workflow that reads emails and sends summaries"
   - "Analyze my inbox and categorize emails by urgency"
5. **Watch progress**:
   - Purple processing box appears
   - Shows real-time progress steps
   - Updates to final result when complete

### 4. Monitor Activities

Open the Activity Monitor to see all logged events with chat_id:
- http://localhost:8000/app → Activities
- Filter by "Agent Executions" or "Tool Invocations"
- Look for entries with `chat_id` in the data

### 5. Test Scenarios

#### Long-Running Request (Good for Async)
```
"Generate a comprehensive workflow that:
1. Reads emails from multiple folders
2. Analyzes sentiment of each email
3. Creates different responses based on sentiment
4. Sends summaries to Slack channels
5. Archives processed emails"
```

#### Quick Request (Compare Sync vs Async)
```
"Hello, what can you help me with?"
```

#### Tool-Heavy Request
```
"Read my latest emails, analyze them, and create a workflow to automate similar tasks"
```

## Performance Benefits

### With Sync Mode (Single Worker)
- Long request blocks all other requests
- Activity polling fails during processing
- UI becomes unresponsive

### With Async Mode
- Request returns immediately
- Other endpoints remain responsive
- Multiple async chats can run in parallel
- Activity monitor continues updating

### With Multiple Workers (Production)
- Even sync requests don't block each other
- Better overall throughput
- Async mode still beneficial for UI responsiveness

## Troubleshooting

### Chat Stuck in Processing
- Check if 90-second timeout triggered
- Look for errors in activity log
- Manually cleanup: `DELETE /api/chat/async/{chat_id}`

### No Progress Updates
- Verify activity logging is working
- Check browser console for polling errors
- Ensure WebSocket/SSE connections aren't blocked

### Server Blocking Despite Async
- Ensure you're using production mode with workers
- Check `WORKERS` environment variable
- Verify background tasks are enabled in FastAPI

## Configuration

### Environment Variables
```bash
# Number of workers (production only)
WORKERS=4

# Disable reload for production
RELOAD=false

# Run with configuration
WORKERS=4 RELOAD=false python run_unified.py
```

### Timeout Settings
- Default: 90 seconds
- Configurable in `chat_routes.py:886`
- Client polling: Every 1 second

## Architecture Notes

### Why Async Chat Helps
1. **Non-blocking**: Returns UUID immediately
2. **Progress tracking**: Real-time status updates
3. **Parallel processing**: Multiple chats simultaneously
4. **Better UX**: UI remains responsive
5. **Activity logging**: Complete audit trail with UUID

### Implementation Details
- Uses FastAPI `BackgroundTasks`
- In-memory session storage (could use Redis for production)
- Polling-based updates (could use WebSockets)
- Activities logged with `chat_id` for correlation

### Future Improvements
1. **Persistent storage**: Redis/database for session state
2. **WebSocket updates**: Replace polling with push
3. **Request queuing**: Celery/RQ for better scaling
4. **Streaming responses**: Stream LLM output as it generates
5. **Cancel support**: Allow canceling in-progress chats