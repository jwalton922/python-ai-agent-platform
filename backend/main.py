from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import agent_routes, workflow_routes, mcp_routes, activity_routes, llm_routes, chat_routes

app = FastAPI(title="AI Agent Platform", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agent_routes.router, prefix="/api/agents", tags=["agents"])
app.include_router(workflow_routes.router, prefix="/api/workflows", tags=["workflows"])
app.include_router(mcp_routes.router, prefix="/api/mcp-tools", tags=["mcp-tools"])
app.include_router(activity_routes.router, prefix="/api/activities", tags=["activities"])
app.include_router(llm_routes.router, prefix="/api/llm", tags=["llm"])
app.include_router(chat_routes.router, prefix="/api/chat", tags=["chat"])

@app.get("/")
async def root():
    return {"message": "AI Agent Platform API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)