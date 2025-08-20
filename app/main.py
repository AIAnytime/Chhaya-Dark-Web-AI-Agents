from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.v1.api import api_router
from app.core.config import settings
import uvicorn

app = FastAPI(
    title="Chhaya OS",
    description="Dark Web Monitoring AI Agent - Advanced threat intelligence and monitoring platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "Welcome to Chhaya OS - Dark Web Monitoring AI Agent",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "interface": "/static/index.html"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Chhaya OS"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
