from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import asyncio
import httpx
from pathlib import Path

from app.routers import recommendations
from app.config import settings

async def keep_alive_task():
    """
    Background task to keep the server alive on Render's free tier.
    Pings the health endpoint every 14 minutes to prevent sleep.
    """
    # Wait a bit before starting to ensure the server is fully up
    await asyncio.sleep(60)
    
    while True:
        try:
            # Get the base URL from environment or use localhost for local dev
            base_url = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:8000")
            health_url = f"{base_url}/health"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(health_url)
                if response.status_code == 200:
                    print(f"🔄 Keep-alive ping successful: {response.status_code}")
                else:
                    print(f"⚠️ Keep-alive ping returned: {response.status_code}")
        
        except Exception as e:
            print(f"❌ Keep-alive ping failed: {e}")
        
        # Wait 14 minutes (840 seconds) before next ping
        # This is less than Render's 15-minute timeout
        await asyncio.sleep(840)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 CineReads API starting up...")
    
    # Ensure cache directory exists
    cache_dir = Path(settings.cache_dir)
    cache_dir.mkdir(exist_ok=True)
    (cache_dir / "recommendations").mkdir(exist_ok=True)
    (cache_dir / "books").mkdir(exist_ok=True)
    
    print(f"📁 Cache directory: {cache_dir.absolute()}")
    print(f"🔑 OpenAI API key: {'✅ Set' if settings.openai_api_key else '❌ Missing'}")
    print(f"🔑 Hardcover API key: {'✅ Set' if settings.hardcover_api_key else '❌ Missing'}")
    
    # Start the keep-alive task only in production (when RENDER_EXTERNAL_URL is set)
    keep_alive_enabled = os.getenv("RENDER_EXTERNAL_URL") is not None
    if keep_alive_enabled:
        print("🔄 Starting keep-alive task for Render deployment...")
        keep_alive_task_instance = asyncio.create_task(keep_alive_task())
    else:
        print("🏠 Running locally - keep-alive task disabled")
        keep_alive_task_instance = None
    
    yield
    
    # Shutdown
    print("👋 CineReads API shutting down...")
    if keep_alive_task_instance:
        print("🛑 Stopping keep-alive task...")
        keep_alive_task_instance.cancel()
        try:
            await keep_alive_task_instance
        except asyncio.CancelledError:
            print("✅ Keep-alive task stopped")

app = FastAPI(
    title="CineReads API", 
    version="1.0.0",
    description="Turn your favorite movies into book recommendations",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app",  # Allow all Vercel deployments
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:3001",  # Alternative dev port
        "http://localhost",       # Docker frontend on port 80
        "https://cinereads.vercel.app",  # Production
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if settings.debug:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(exc)}"}
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred"}
        )

# Include routers
app.include_router(recommendations.router, prefix="/api", tags=["recommendations"])

@app.get("/")
async def root():
    return {
        "message": "CineReads API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """
    Enhanced health check endpoint for monitoring and keep-alive purposes.
    """
    import time
    from datetime import datetime
    
    cache_dir = Path(settings.cache_dir)
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": int(time.time()),
        "cache_dir_exists": cache_dir.exists(),
        "openai_configured": bool(settings.openai_api_key),
        "hardcover_configured": bool(settings.hardcover_api_key),
        "debug_mode": settings.debug,
        "render_deployment": bool(os.getenv("RENDER_EXTERNAL_URL")),
        "message": "CineReads API is running and healthy! 🚀"
    }