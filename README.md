# AI Agent Platform

A platform for creating custom AI agents and orchestrating them in workflows using a visual DAG (Directed Acyclic Graph) interface.

## 🚀 Features

- **Agent Definition System**: Create AI agents with custom instructions, tool permissions, and trigger conditions
- **LLM Integration**: Real AI agent execution using OpenAI API with automatic fallback to mock responses
- **Visual Workflow Builder**: Drag-and-drop DAG editor built with React Flow
- **Mock MCP Tool System**: Simulated tools for email, Slack, file operations, and more
- **Workflow Execution Engine**: Process DAGs with parallel and sequential execution
- **Real-time Activity Monitoring**: Live activity feed with SSE (Server-Sent Events)
- **Streamlit Dashboard**: Quick admin interface with system monitoring

## 🏗️ Architecture

```
├── backend/                 # FastAPI backend
│   ├── models/             # Pydantic data models
│   ├── api/routes/         # API endpoints
│   ├── llm/                # LLM integration (OpenAI, mock providers)
│   ├── mcp/tools/          # Mock MCP tool implementations
│   ├── workflow/           # Workflow execution engine
│   └── storage/            # In-memory storage layer
├── frontend/               # React frontend with TypeScript
│   └── src/components/     # React components
├── tests/                  # Unit tests
└── streamlit_dashboard.py  # Streamlit admin dashboard
```

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.8+, Pydantic, Uvicorn, OpenAI
- **Frontend**: React 18, TypeScript, React Flow, Tailwind CSS
- **Dashboard**: Streamlit, Plotly
- **AI/LLM**: OpenAI API with automatic fallback to mock responses
- **Development**: pytest, pytest-asyncio

## 📦 Installation & Setup

### 1. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Optional: Configure OpenAI API key for real AI agent execution
cp .env.example .env
# Edit .env and add your OpenAI API key

# Start the FastAPI server
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

**Note**: The platform works without an OpenAI API key using mock responses for development.

### 2. Frontend Setup

```bash
# Install Node.js dependencies
cd frontend
npm install

# Start the React development server
npm start
```

The frontend will be available at `http://localhost:3000`

### 3. Streamlit Dashboard (Optional)

```bash
# Install Streamlit dependencies
pip install -r requirements-streamlit.txt

# Start the Streamlit dashboard
streamlit run streamlit_dashboard.py
```

The dashboard will be available at `http://localhost:8501`

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend

# Run specific test files
pytest tests/test_models.py
pytest tests/test_api.py
pytest tests/test_workflow_executor.py
```

## 📚 API Documentation

Once the backend is running, you can access:

- **Interactive API docs**: http://localhost:8000/docs
- **OpenAPI schema**: http://localhost:8000/openapi.json
- **Health check**: http://localhost:8000/health

### Key Endpoints

```
POST   /api/agents                 # Create new agent
GET    /api/agents                 # List all agents
GET    /api/agents/{id}            # Get agent details
PUT    /api/agents/{id}            # Update agent
DELETE /api/agents/{id}            # Delete agent

POST   /api/workflows              # Create workflow
GET    /api/workflows              # List workflows
POST   /api/workflows/{id}/execute # Execute workflow

GET    /api/llm/provider           # Get current LLM provider info
GET    /api/llm/providers          # List available LLM providers
POST   /api/llm/test               # Test LLM with simple prompt
POST   /api/llm/chat               # Chat with LLM (conversation)

GET    /api/mcp-tools              # List available MCP tools
POST   /api/mcp-tools/{id}/action  # Execute tool action

GET    /api/activities             # Get activity feed
GET    /api/activities/stream      # SSE endpoint for real-time updates
```

## 🔧 Usage Examples

### 1. Create an Agent

```bash
curl -X POST http://localhost:8000/api/agents/ \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "Email Assistant",
    "description": "Helps manage emails",
    "instructions": "You are a helpful email assistant. Read and respond to emails professionally.",
    "mcp_tool_permissions": ["email_tool"],
    "trigger_conditions": ["manual"]
  }'
```

### 2. Create a Workflow

```bash
curl -X POST http://localhost:8000/api/workflows/ \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "Email Processing Workflow",
    "description": "Processes incoming emails",
    "nodes": [
      {
        "id": "node1",
        "agent_id": "your-agent-id",
        "position": {"x": 100, "y": 100}
      }
    ],
    "edges": [],
    "trigger_conditions": ["email"]
  }'
```

### 3. Execute a Workflow

```bash
curl -X POST http://localhost:8000/api/workflows/your-workflow-id/execute \\
  -H "Content-Type: application/json" \\
  -d '{
    "context": {
      "input_data": "test"
    }
  }'
```

## 🤖 LLM Integration

The platform includes a flexible LLM integration system that allows AI agents to use real language models.

### Configuration

```bash
# Set your OpenAI API key (optional)
export OPENAI_API_KEY=your-key-here

# Or add to .env file
echo "OPENAI_API_KEY=your-key-here" >> .env
```

### Test LLM Integration

```bash
# Check current LLM provider
curl http://localhost:8000/api/llm/provider

# Test with a simple prompt
curl -X POST http://localhost:8000/api/llm/test \\
  -H "Content-Type: application/json" \\
  -d '{
    "prompt": "Write a Python function to calculate fibonacci numbers",
    "system_prompt": "You are a helpful programming assistant"
  }'

# Chat with the LLM
curl -X POST http://localhost:8000/api/llm/chat \\
  -H "Content-Type: application/json" \\
  -d '[
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Explain quantum computing"}
  ]'
```

### Automatic Fallback

- **With API key**: Uses real OpenAI API
- **Without API key**: Uses mock responses for development
- **On API failure**: Automatically falls back to mock responses

## 🎯 Mock MCP Tools

The platform includes several mock MCP tools for demonstration:

### Email Tool
- **Actions**: send, read
- **Usage**: Send emails and read from inbox
- **Parameters**: to, subject, body (for send), folder, limit (for read)

### Slack Tool
- **Actions**: post, read
- **Usage**: Post messages and read from channels
- **Parameters**: channel, message (for post), limit (for read)

### File Tool
- **Actions**: read, write, list
- **Usage**: File system operations
- **Parameters**: filepath, content (for write), directory (for list)

## 🔍 Activity Monitoring

The platform provides comprehensive activity monitoring:

- **Real-time Updates**: SSE-based live activity feed
- **Activity Types**: Agent executions, tool invocations, workflow events
- **Filtering**: Filter by type, success status, time range
- **Detailed Logging**: Full parameter and result logging

## 🎨 Frontend Features

### Visual Workflow Editor
- Drag-and-drop interface using React Flow
- Add agent nodes by selecting from dropdown
- Connect nodes with edges to define execution flow
- Save and load workflows
- Execute workflows directly from the editor

### Agent Builder
- Form-based agent creation and editing
- MCP tool permission management
- Instruction editor with syntax highlighting (planned)
- Agent listing with search and filters

### Activity Monitor
- Real-time activity stream
- Success/failure indicators
- Detailed activity information
- Activity type filtering
- Expandable details view

## 🚦 Development Status

This is a development/demo version with the following limitations:

- **In-memory Storage**: Data is not persisted between restarts
- **Mock AI Execution**: Agents return mock responses instead of actual AI processing
- **Basic Authentication**: No user authentication system
- **Simplified Error Handling**: Basic error handling and validation

## 🔮 Future Enhancements

- **Persistent Storage**: Database integration (PostgreSQL/SQLite)
- **Real AI Integration**: Connect to actual AI models (OpenAI, Anthropic, etc.)
- **User Authentication**: JWT-based authentication system
- **Workflow Templates**: Pre-built workflow templates
- **Advanced Scheduling**: Cron-based workflow scheduling
- **Plugin System**: Extensible MCP tool system
- **Performance Monitoring**: Detailed metrics and analytics
- **Export/Import**: Workflow and agent import/export functionality

## 📝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋‍♂️ Support

If you encounter any issues or have questions:

1. Check the API documentation at http://localhost:8000/docs
2. Review the test files for usage examples
3. Check the browser console for frontend errors
4. Ensure all services are running (backend on :8000, frontend on :3000)

---

Built with ❤️ using FastAPI, React, and modern web technologies.