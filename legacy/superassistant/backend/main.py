from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import get_settings
from database import init_db
import uvicorn

# Import routers
from routers import tasks, projects, calendar, ai, documents, knowledge

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Assistant de productivité local avec IA pour la cybersécurité",
    version="1.0.0"
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite + React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["calendar"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["knowledge"])


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    print(f"✅ {settings.app_name} started successfully!")
    print(f"📊 Database: {settings.database_url}")
    print(f"🤖 AI: Claude API configured")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": settings.app_name,
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "tasks": "/api/tasks",
            "projects": "/api/projects",
            "calendar": "/api/calendar",
            "ai": "/api/ai",
            "documents": "/api/documents",
            "knowledge": "/api/knowledge"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
