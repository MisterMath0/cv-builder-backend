# app/main.py
from datetime import datetime
from app.api import cv, cover_letter
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import engine
from .models import Base
from app.api import auth
from dotenv import load_dotenv
import os
load_dotenv()



# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION
)

FRONTEND_URL: str = os.getenv("FRONTEND_URL")
# Create database tables
Base.metadata.create_all(bind=engine)

# Include Routers
app.include_router(auth.router)
app.include_router(cv.router)
app.include_router(cover_letter.router)

# CORS middleware
allowed_origins = [
    "https://cv-builder-frontend-six.vercel.app",  # Frontend URL
    "https://cv-builder-frontend-git-main-guy-mathieu-fokos-projects.vercel.app",
    "http://localhost:3000",
    FRONTEND_URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.route("/")
def home():
    return "Backend is running!"

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "cv-builder-api",
        "database": "connected"
    }
