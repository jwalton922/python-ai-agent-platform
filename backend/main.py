from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
import os
from backend.api.routes import agent_routes, workflow_routes, mcp_routes, activity_routes, llm_routes, chat_routes
from backend.api.routes import streamlit_routes, workflow_routes_enhanced

app = FastAPI(title="AI Agent Platform", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(agent_routes.router, prefix="/api/agents", tags=["agents"])
app.include_router(workflow_routes.router, prefix="/api/workflows", tags=["workflows"])
app.include_router(workflow_routes_enhanced.router, prefix="/api/workflows/enhanced", tags=["enhanced-workflows"])
app.include_router(mcp_routes.router, prefix="/api/mcp-tools", tags=["mcp-tools"])
app.include_router(activity_routes.router, prefix="/api/activities", tags=["activities"])
app.include_router(llm_routes.router, prefix="/api/llm", tags=["llm"])
app.include_router(chat_routes.router, prefix="/api/chat", tags=["chat"])

# Include Streamlit proxy routes
app.include_router(streamlit_routes.router, prefix="/streamlit", tags=["streamlit"])

# Serve React frontend build files if they exist
frontend_build_path = Path(__file__).parent.parent / "frontend" / "build"
if frontend_build_path.exists():
    # Mount static files for React app
    app.mount("/static", StaticFiles(directory=str(frontend_build_path / "static")), name="static")
    
    @app.get("/app/{full_path:path}")
    async def serve_react_app(full_path: str):
        """Serve React app for /app routes"""
        file_path = frontend_build_path / full_path if full_path else frontend_build_path / "index.html"
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        # Always return index.html for client-side routing
        return FileResponse(str(frontend_build_path / "index.html"))
    
    @app.get("/app")
    async def serve_react_root():
        """Serve React app root"""
        return FileResponse(str(frontend_build_path / "index.html"))

@app.get("/")
async def root():
    """Main landing page with links to all interfaces"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Agent Platform</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .container {
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 600px;
                width: 90%;
            }
            h1 {
                color: #333;
                text-align: center;
                margin-bottom: 10px;
            }
            .subtitle {
                color: #666;
                text-align: center;
                margin-bottom: 40px;
            }
            .interfaces {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .interface-card {
                background: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                text-decoration: none;
                color: #333;
                transition: transform 0.3s, box-shadow 0.3s;
                border: 2px solid transparent;
            }
            .interface-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 30px rgba(0,0,0,0.15);
                border-color: #667eea;
            }
            .interface-card h3 {
                margin: 0 0 10px 0;
                color: #667eea;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .interface-card p {
                margin: 0;
                color: #666;
                font-size: 14px;
            }
            .icon {
                font-size: 24px;
            }
            .status {
                text-align: center;
                padding: 15px;
                background: #e8f5e9;
                border-radius: 10px;
                color: #2e7d32;
                margin-bottom: 20px;
            }
            .api-section {
                text-align: center;
                padding-top: 20px;
                border-top: 2px solid #f0f0f0;
            }
            .api-link {
                display: inline-block;
                padding: 10px 20px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                transition: background 0.3s;
            }
            .api-link:hover {
                background: #764ba2;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 AI Agent Platform</h1>
            <p class="subtitle">Unified Interface for AI Agents and Workflows</p>
            
            <div class="status">
                ✅ All systems operational
            </div>
            
            <div class="interfaces">
                <a href="/streamlit" class="interface-card">
                    <h3><span class="icon">📊</span> Streamlit Dashboard</h3>
                    <p>Interactive dashboard with data visualization, agent management, and real-time monitoring</p>
                </a>
                
                <a href="/app" class="interface-card">
                    <h3><span class="icon">⚛️</span> React Application</h3>
                    <p>Modern React UI with drag-and-drop workflow editor and real-time updates</p>
                </a>
                
                <a href="/streamlit#chat" class="interface-card">
                    <h3><span class="icon">💬</span> Agent Chat</h3>
                    <p>Chat directly with your AI agents using natural language</p>
                </a>
                
                <a href="/streamlit#activities" class="interface-card">
                    <h3><span class="icon">📈</span> Activity Monitor</h3>
                    <p>Real-time activity feed with detailed MCP tool execution logs</p>
                </a>
            </div>
            
            <div class="api-section">
                <h3>🔧 Developer Tools</h3>
                <a href="/api/docs" class="api-link">API Documentation</a>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    """Start the Streamlit app when FastAPI starts"""
    from backend.streamlit_runner import streamlit_runner
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Streamlit app...")
    
    try:
        streamlit_runner.start()
        logger.info("Streamlit app started successfully")
    except Exception as e:
        logger.error(f"Failed to start Streamlit app: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the Streamlit app when FastAPI shuts down"""
    from backend.streamlit_runner import streamlit_runner
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info("Stopping Streamlit app...")
    
    try:
        streamlit_runner.stop()
        logger.info("Streamlit app stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping Streamlit app: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)