# Unified Server Documentation

## Overview

The AI Agent Platform now runs as a **single unified server** that serves:
- **FastAPI Backend** (Main server on port 8000)
- **Streamlit Dashboard** (Proxied through `/streamlit`)
- **React Frontend** (Served at `/app`)
- **API Documentation** (Available at `/api/docs`)

## Quick Start

### 1. Install Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Build React frontend (optional but recommended)
cd frontend
npm install
npm run build
cd ..
```

### 2. Configure Environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
# OPENAI_API_KEY=your_key_here
# ANTHROPIC_API_KEY=your_key_here
```

### 3. Run the Unified Server
```bash
# Run the unified server
python run_unified.py

# Or use uvicorn directly
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

## Available Endpoints

Once the server is running on `http://localhost:8000`, you can access:

| Endpoint | Description |
|----------|-------------|
| `/` | Main landing page with links to all interfaces |
| `/streamlit` | Streamlit dashboard (embedded in iframe) |
| `/streamlit/proxy/` | Direct Streamlit proxy |
| `/app` | React frontend application |
| `/api/docs` | Interactive API documentation (Swagger UI) |
| `/api/redoc` | Alternative API documentation (ReDoc) |
| `/health` | Health check endpoint |

## Architecture

```
┌─────────────────────────────────────────────┐
│           FastAPI Main Server (8000)        │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │         API Routes (/api/*)         │   │
│  │  - Agents, Workflows, Activities    │   │
│  │  - Chat, MCP Tools, LLM             │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │    Streamlit Proxy (/streamlit)     │   │
│  │  ┌─────────────────────────────┐    │   │
│  │  │  Streamlit Process (8501)   │    │   │
│  │  │  Running as subprocess      │    │   │
│  │  └─────────────────────────────┘    │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │    Static Files Server (/app)       │   │
│  │  - React Build Files                │   │
│  │  - Client-side Routing              │   │
│  └─────────────────────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

## How It Works

### 1. **FastAPI Main Server**
- Runs on port 8000 (configurable)
- Handles all API requests
- Manages Streamlit subprocess
- Serves static files for React app

### 2. **Streamlit Integration**
- Streamlit runs as a subprocess on port 8501
- FastAPI proxies all `/streamlit/*` requests
- Automatic start/stop with main server
- Embedded in iframe for seamless integration

### 3. **React Frontend**
- Pre-built files served from `/frontend/build`
- Available at `/app` route
- Client-side routing supported
- Communicates with API at `/api/*`

## Benefits

1. **Single Port Access**: Everything accessible through port 8000
2. **Unified Management**: Start/stop everything with one command
3. **Seamless Integration**: All interfaces work together
4. **CORS Simplified**: No cross-origin issues
5. **Production Ready**: Easy to deploy behind nginx/Apache

## Troubleshooting

### Streamlit Not Loading
```bash
# Check if Streamlit is running
curl http://localhost:8501

# Check Streamlit status
curl http://localhost:8000/streamlit/status

# Restart Streamlit
curl -X POST http://localhost:8000/streamlit/stop
curl -X POST http://localhost:8000/streamlit/start
```

### React App Not Found
```bash
# Build the React frontend
cd frontend
npm install
npm run build
```

### Port Already in Use
```bash
# Change port in .env file
PORT=8080

# Or kill the process using the port
lsof -i :8000
kill -9 <PID>
```

## Development

### Hot Reload
- FastAPI: Automatic with `--reload` flag
- Streamlit: Automatic file watching
- React: Run `npm start` in separate terminal for development

### Adding New Routes
1. Add route file in `backend/api/routes/`
2. Import and include in `backend/main.py`
3. Routes automatically available at `/api/your-route`

### Customizing Streamlit
- Edit `streamlit_dashboard.py`
- Changes reflected immediately (auto-reload)
- Custom components in `streamlit_components/`

## Production Deployment

### Using Gunicorn
```bash
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Using Docker
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Build React frontend
RUN cd frontend && npm install && npm run build

# Expose port
EXPOSE 8000

# Run unified server
CMD ["python", "run_unified.py"]
```

### Environment Variables
- Set `RELOAD=false` for production
- Use strong `SECRET_KEY`
- Configure proper API keys
- Set appropriate `LOG_LEVEL`

## Security Considerations

1. **API Keys**: Never commit `.env` file
2. **CORS**: Configure for specific origins in production
3. **Authentication**: Implement before production deployment
4. **HTTPS**: Use reverse proxy (nginx) with SSL
5. **Rate Limiting**: Add middleware for API protection

## API Integration

All API endpoints remain the same and are accessible at:
- `/api/agents` - Agent management
- `/api/workflows` - Workflow operations
- `/api/activities` - Activity monitoring
- `/api/chat` - Chat with agents
- `/api/mcp-tools` - MCP tool management
- `/api/llm` - LLM operations

Example API call:
```javascript
// From React app
fetch('/api/agents')
  .then(res => res.json())
  .then(data => console.log(data));

// From external client
fetch('http://localhost:8000/api/agents')
  .then(res => res.json())
  .then(data => console.log(data));
```

## Support

For issues or questions:
1. Check the health endpoint: `http://localhost:8000/health`
2. View logs in the terminal running the server
3. Check individual component status at `/streamlit/status`
4. Review API documentation at `/api/docs`