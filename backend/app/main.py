from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import os
from dotenv import load_dotenv

from app.database import get_db, engine
from app.models import Base
from app import models, schemas
from app.auth import get_current_user_info

# Import routers
from app.routers import users, plants, scan, dashboard, achievements

# Load environment variables
load_dotenv()

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PlantPal API",
    description="Plant identification and care tracking API.",
    version="1.0.0"
) 

# CORS configuration
origins = os.getenv(
    "CORS_ORIGINS", 
    "http://localhost:3000,http://plantpal-frontend-bucket.s3-website-ap-southeast-1.amazonaws.com"
).split(",")

# Strip whitespace from origins
origins = [origin.strip() for origin in origins]

print(f"🌐 CORS Origins configured: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router)
app.include_router(plants.router)
app.include_router(scan.router)
app.include_router(dashboard.router)
app.include_router(achievements.router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to PlantPal API! 🌱",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "updated"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "PlantPal API is running"}

# Simple test endpoint
@app.get("/api/v1/test")
def test_endpoint():
    """Test endpoint to verify API is working"""
    return {"message": "PlantPal API is working!", "timestamp": "2024-01-15T10:00:00Z"}

# Debug endpoint to clear test user
@app.delete("/api/v1/debug/clear-test-user")
def clear_test_user(db: Session = Depends(get_db)):
    """Clear test user from database"""
    try:
        user = db.query(models.User).filter(
            models.User.email == "testuser@plantpal.com"
        ).first()
        
        if user:
            db.delete(user)
            db.commit()
            return {"message": "Test user cleared"}
        else:
            return {"message": "No test user found"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}

# All API v1 routes are now handled by the router modules








if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
