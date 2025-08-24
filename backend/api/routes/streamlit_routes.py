"""Routes for proxying Streamlit through FastAPI"""
from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
import httpx
import logging
from backend.streamlit_runner import streamlit_runner

logger = logging.getLogger(__name__)

router = APIRouter()

# HTTP client for proxying requests
client = httpx.AsyncClient(timeout=30.0)


@router.get("/")
async def streamlit_root():
    """Redirect to the Streamlit app or show embedded version"""
    if not streamlit_runner.is_running:
        streamlit_runner.start()
        import asyncio
        await asyncio.sleep(2)  # Give Streamlit time to start
    
    # Return an HTML page that embeds the Streamlit app in an iframe
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Agent Platform - Dashboard</title>
        <style>
            body, html {{
                margin: 0;
                padding: 0;
                height: 100%;
                overflow: hidden;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
                    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 10px 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
            }}
            .header .nav {{
                display: flex;
                gap: 20px;
            }}
            .header a {{
                color: white;
                text-decoration: none;
                padding: 5px 10px;
                border-radius: 4px;
                transition: background 0.3s;
            }}
            .header a:hover {{
                background: rgba(255,255,255,0.2);
            }}
            .iframe-container {{
                height: calc(100vh - 60px);
                width: 100%;
            }}
            iframe {{
                width: 100%;
                height: 100%;
                border: none;
            }}
            .loading {{
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                text-align: center;
            }}
            .spinner {{
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🤖 AI Agent Platform</h1>
            <div class="nav">
                <a href="/api/docs" target="_blank">📚 API Docs</a>
                <a href="/streamlit" target="_blank">📊 Full Dashboard</a>
                <a href="/app" target="_blank">⚛️ React UI</a>
            </div>
        </div>
        <div class="iframe-container">
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Loading Streamlit Dashboard...</p>
            </div>
            <iframe 
                id="streamlit-frame"
                src="/streamlit/proxy/" 
                onload="document.getElementById('loading').style.display='none';"
                onerror="document.getElementById('loading').innerHTML='<p>Error loading dashboard</p>';">
            </iframe>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.api_route("/proxy/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
async def proxy_streamlit(request: Request, path: str):
    """Proxy all requests to the Streamlit app"""
    if not streamlit_runner.is_running:
        raise HTTPException(status_code=503, detail="Streamlit app is not running")
    
    # Build the target URL
    streamlit_url = streamlit_runner.get_url()
    target_url = f"{streamlit_url}/{path}"
    
    # Add query parameters
    if request.url.query:
        target_url += f"?{request.url.query}"
    
    try:
        # Get request body if present
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
        
        # Forward the request
        headers = dict(request.headers)
        # Remove host header to avoid conflicts
        headers.pop("host", None)
        
        response = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
            follow_redirects=True
        )
        
        # Create response with the same status code and headers
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
        
    except httpx.RequestError as e:
        logger.error(f"Error proxying request to Streamlit: {e}")
        raise HTTPException(status_code=502, detail=f"Error connecting to Streamlit: {str(e)}")


@router.get("/status")
async def streamlit_status():
    """Check if Streamlit is running"""
    return {
        "running": streamlit_runner.is_running,
        "port": streamlit_runner.port,
        "url": streamlit_runner.get_url() if streamlit_runner.is_running else None
    }


@router.post("/start")
async def start_streamlit():
    """Start the Streamlit app"""
    if streamlit_runner.is_running:
        return {"message": "Streamlit is already running", "url": streamlit_runner.get_url()}
    
    streamlit_runner.start()
    import asyncio
    await asyncio.sleep(2)  # Give it time to start
    
    if streamlit_runner.is_running:
        return {"message": "Streamlit started successfully", "url": streamlit_runner.get_url()}
    else:
        raise HTTPException(status_code=500, detail="Failed to start Streamlit")


@router.post("/stop")
async def stop_streamlit():
    """Stop the Streamlit app"""
    if not streamlit_runner.is_running:
        return {"message": "Streamlit is not running"}
    
    streamlit_runner.stop()
    return {"message": "Streamlit stopped successfully"}