#!/usr/bin/env python3
"""
Sandbox runner for Jupyter notebook proxy environments
Configures the application with proper path prefixes for proxy deployment
"""

import os
import sys
import logging
from pathlib import Path

# Setup paths before ANY imports
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))
os.environ["PYTHONPATH"] = str(project_root)

# Get the base path from environment
BASE_PATH = os.getenv("BASE_PATH", "/notebook/pxj363/josh-testing/proxy/8000")
PROXY_PREFIX = os.getenv("PROXY_PREFIX", BASE_PATH)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import FastAPI and dependencies
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import our application components
from backend.api.routes import agent_routes, workflow_routes, activity_routes, chat_routes
from backend.streamlit_runner import StreamlitRunner
from backend.database import init_db

def create_sandbox_app():
    """Create FastAPI app configured for sandbox/proxy environment"""
    
    app = FastAPI(
        title="AI Agent Platform",
        description="Unified platform for AI agents with MCP tools",
        version="1.0.0",
        root_path=BASE_PATH,  # Critical for proxy environments
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )
    
    # Configure CORS for proxy environment
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize database
    init_db()
    
    # Create Streamlit runner
    streamlit_runner = StreamlitRunner(proxy_base_path=BASE_PATH)
    
    # API Routes with prefix awareness
    app.include_router(agent_routes.router, prefix="/api/agents", tags=["agents"])
    app.include_router(workflow_routes.router, prefix="/api/workflows", tags=["workflows"])
    app.include_router(activity_routes.router, prefix="/api/activities", tags=["activities"])
    app.include_router(chat_routes.router, prefix="/api/chat", tags=["chat"])
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "base_path": BASE_PATH,
            "proxy_prefix": PROXY_PREFIX,
            "services": {
                "api": "running",
                "streamlit": streamlit_runner.is_running()
            }
        }
    
    # Root redirect with base path awareness
    @app.get("/")
    async def root():
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Agent Platform - Sandbox Mode</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }}
                .container {{
                    background: white;
                    border-radius: 10px;
                    padding: 40px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                }}
                h1 {{
                    color: #333;
                    border-bottom: 3px solid #667eea;
                    padding-bottom: 10px;
                }}
                .badge {{
                    background: #ff6b6b;
                    color: white;
                    padding: 3px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                    margin-left: 10px;
                }}
                .endpoints {{
                    margin: 30px 0;
                }}
                .endpoint {{
                    display: block;
                    padding: 15px;
                    margin: 10px 0;
                    background: #f8f9fa;
                    border-left: 4px solid #667eea;
                    text-decoration: none;
                    color: #333;
                    border-radius: 5px;
                    transition: all 0.3s;
                }}
                .endpoint:hover {{
                    background: #e9ecef;
                    transform: translateX(5px);
                }}
                .endpoint-title {{
                    font-weight: bold;
                    color: #667eea;
                }}
                .endpoint-desc {{
                    font-size: 14px;
                    color: #666;
                    margin-top: 5px;
                }}
                .config {{
                    background: #f0f0f0;
                    padding: 15px;
                    border-radius: 5px;
                    font-family: monospace;
                    font-size: 13px;
                    margin: 20px 0;
                }}
                .warning {{
                    background: #fff3cd;
                    border: 1px solid #ffc107;
                    color: #856404;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 AI Agent Platform <span class="badge">SANDBOX MODE</span></h1>
                
                <div class="warning">
                    <strong>⚠️ Sandbox/Proxy Mode Active</strong><br>
                    Running behind proxy with base path: <code>{BASE_PATH}</code>
                </div>
                
                <div class="config">
                    <strong>Current Configuration:</strong><br>
                    Base Path: {BASE_PATH}<br>
                    API Endpoint: {BASE_PATH}/api<br>
                    App URL: {BASE_PATH}/app<br>
                    Streamlit URL: {BASE_PATH}/streamlit
                </div>
                
                <div class="endpoints">
                    <h2>Available Interfaces</h2>
                    
                    <a href="{BASE_PATH}/app" class="endpoint">
                        <div class="endpoint-title">⚛️ React Dashboard</div>
                        <div class="endpoint-desc">Modern UI for agent management, workflows, and chat</div>
                    </a>
                    
                    <a href="{BASE_PATH}/streamlit" class="endpoint">
                        <div class="endpoint-title">📊 Streamlit Dashboard</div>
                        <div class="endpoint-desc">Interactive data app with agent configuration and monitoring</div>
                    </a>
                    
                    <a href="{BASE_PATH}/api/docs" class="endpoint">
                        <div class="endpoint-title">📚 API Documentation</div>
                        <div class="endpoint-desc">Interactive Swagger UI for API exploration</div>
                    </a>
                    
                    <a href="{BASE_PATH}/health" class="endpoint">
                        <div class="endpoint-title">🔍 Health Check</div>
                        <div class="endpoint-desc">System status and service availability</div>
                    </a>
                </div>
                
                <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 14px;">
                    <p><strong>For Jupyter Users:</strong> This application is configured to work within your Jupyter notebook proxy environment. All links and API calls are properly prefixed.</p>
                </div>
            </div>
        </body>
        </html>
        """)
    
    # Streamlit proxy endpoint with proper path handling
    @app.get("/streamlit")
    async def streamlit_root():
        if not streamlit_runner.is_running():
            await streamlit_runner.start()
        
        # Redirect to Streamlit with proper base path
        return RedirectResponse(url=f"{BASE_PATH}/streamlit/")
    
    @app.get("/streamlit/{path:path}")
    async def streamlit_proxy(request: Request, path: str):
        if not streamlit_runner.is_running():
            await streamlit_runner.start()
        
        return await streamlit_runner.proxy_request(request, path)
    
    @app.post("/streamlit/{path:path}")
    async def streamlit_proxy_post(request: Request, path: str):
        if not streamlit_runner.is_running():
            await streamlit_runner.start()
        
        return await streamlit_runner.proxy_request(request, path)
    
    # Mount React app with runtime configuration
    frontend_build = project_root / "frontend" / "build"
    if frontend_build.exists():
        from fastapi.responses import FileResponse
        
        @app.get("/app")
        async def serve_react_root():
            """Serve React app with runtime configuration"""
            index_path = frontend_build / "index.html"
            
            # Read the index.html file
            with open(index_path, 'r') as f:
                html_content = f.read()
            
            # Inject runtime configuration
            configured_html = html_content.replace(
                '</head>',
                f'''<script>
                    window.API_CONFIG = {{
                        baseUrl: '{BASE_PATH}',
                        basePath: '{BASE_PATH}'
                    }};
                    console.log('Runtime API Config:', window.API_CONFIG);
                </script>
                </head>'''
            )
            
            return HTMLResponse(content=configured_html)
        
        # Mount static files for everything else
        app.mount("/app", StaticFiles(directory=str(frontend_build), html=True), name="frontend")
        logger.info(f"✅ React app mounted at {BASE_PATH}/app with runtime configuration")
    else:
        logger.warning(f"⚠️ React build not found. Build with: cd frontend && PUBLIC_URL='{BASE_PATH}/app' npm run build")
    
    # Startup and shutdown events
    @app.on_event("startup")
    async def startup_event():
        logger.info(f"🚀 Starting AI Agent Platform in Sandbox Mode")
        logger.info(f"📍 Base Path: {BASE_PATH}")
        logger.info(f"🔗 Proxy Prefix: {PROXY_PREFIX}")
        
        # Start Streamlit
        await streamlit_runner.start()
        
        logger.info(f"✅ All services started successfully")
        logger.info(f"🌐 Access at: http://localhost:8000{BASE_PATH}/")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down services...")
        await streamlit_runner.stop()
        logger.info("Shutdown complete")
    
    return app

def main():
    """Main entry point for sandbox mode"""
    logger.info("=" * 60)
    logger.info("🚀 AI Agent Platform - Sandbox/Jupyter Proxy Mode")
    logger.info("=" * 60)
    logger.info(f"Base Path: {BASE_PATH}")
    logger.info(f"Proxy Prefix: {PROXY_PREFIX}")
    
    # Create the app
    app = create_sandbox_app()
    
    # Get configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"Starting server on http://{host}:{port}")
    logger.info(f"Full URL: http://localhost:{port}{BASE_PATH}/")
    
    # Run with uvicorn
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True,
        # Important: Don't use reload in sandbox mode as it breaks proxy paths
        reload=False
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down AI Agent Platform (Sandbox Mode)")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Failed to start: {e}")
        sys.exit(1)