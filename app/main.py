import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database.connection import Base, engine
from app.middleware.rate_limiter import RateLimitMiddleware

# Routers
from app.api import auth, profile, loans, dashboard, gemini, history, admin, guides

# Initialize database tables on startup
Base.metadata.create_all(bind=engine)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FinRelief AI - Debt Relief & Financial Recovery Platform",
    description="Enterprise-grade AI-powered financial debt relief and settlement recommendation system.",
    version="1.0.0"
)

# Apply CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Apply Rate Limiting middleware
app.add_middleware(RateLimitMiddleware, limit_seconds=60, max_requests=100)

# Create static directory if not exists, and mount it
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)
os.makedirs(os.path.join(static_dir, "avatars"), exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include API Routers
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(loans.router)
app.include_router(dashboard.router)
app.include_router(gemini.router)
app.include_router(history.router)
app.include_router(admin.router)
app.include_router(guides.router)

@app.get("/")
def root():
    return {
        "status": "online",
        "platform": "FinRelief AI",
        "api_documentation": "/docs"
    }
