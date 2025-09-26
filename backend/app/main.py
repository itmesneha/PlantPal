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

@app.get("/")
def read_root():
    return {
        "message": "Welcome to PlantPal API! 🌱",
        "version": "1.0.0",
        "docs": "/docs"
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

# API v1 routes
@app.get("/api/v1/users/me", response_model=schemas.User)
def get_current_user(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    """Get current user profile"""
    try:
        # First, try to find user by cognito_user_id
        user = db.query(models.User).filter(
            models.User.cognito_user_id == user_info["cognito_user_id"]
        ).first()
        
        if not user:
            # User doesn't exist yet, create them from JWT claims
            user_data = {
                "cognito_user_id": user_info["cognito_user_id"],
                "email": user_info["email"],
                "name": user_info.get("name") or user_info.get("username") or "Plant Lover"
            }
            user = models.User(**user_data)
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✅ Created new user from JWT: {user.name} ({user.email})")
        
        return user
        
    except Exception as e:
        print(f"❌ Error in get_current_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/api/v1/users", response_model=schemas.User)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    """Create a new user (called after Cognito signup)"""
    # Check if user already exists
    existing_user = db.query(models.User).filter(
        models.User.cognito_user_id == user.cognito_user_id
    ).first()
    
    if existing_user:
        print(f"✅ User already exists in database: {existing_user.name}")
        return existing_user  # Return existing user instead of error
    
    # Create new user
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    print(f"✅ Created new user via API: {db_user.name} ({db_user.email})")
    
    return db_user

# Test endpoint to create a user manually (no auth required)
@app.post("/api/v1/users/test")
def create_test_user(db: Session = Depends(get_db)):
    """Create a test user for development"""
    try:
        from datetime import datetime
        
        # Check if test user already exists
        existing_user = db.query(models.User).filter(
            models.User.email == "testuser@plantpal.com"
        ).first()
        
        if existing_user:
            print(f"✅ Test user already exists: {existing_user.name}")
            return {
                "id": existing_user.id,
                "cognito_user_id": existing_user.cognito_user_id,
                "email": existing_user.email,
                "name": existing_user.name,
                "created_at": existing_user.created_at.isoformat() if existing_user.created_at else None,
                "updated_at": existing_user.updated_at.isoformat() if existing_user.updated_at else None
            }
        
        # Create test user
        test_user_data = {
            "cognito_user_id": "test-user-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
            "email": "testuser@plantpal.com",
            "name": "Sarah Green"
        }
        
        test_user = models.User(**test_user_data)
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"✅ Created test user: {test_user.name}")
        
        return {
            "id": test_user.id,
            "cognito_user_id": test_user.cognito_user_id,
            "email": test_user.email,
            "name": test_user.name,
            "created_at": test_user.created_at.isoformat() if test_user.created_at else None,
            "updated_at": test_user.updated_at.isoformat() if test_user.updated_at else None
        }
    
    except Exception as e:
        print(f"❌ Error creating test user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create test user: {str(e)}"
        )

@app.get("/api/v1/plants", response_model=List[schemas.Plant])
def get_user_plants(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Get all plants for the current user"""
    user = db.query(models.User).filter(
        models.User.cognito_user_id == user_info["cognito_user_id"]
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    plants = db.query(models.Plant).filter(
        models.Plant.user_id == user.id
    ).offset(skip).limit(limit).all()
    
    return plants

@app.post("/api/v1/plants", response_model=schemas.Plant)
def create_plant(
    plant: schemas.PlantCreate,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    """Add a new plant to user's garden"""
    user = db.query(models.User).filter(
        models.User.cognito_user_id == user_info["cognito_user_id"]
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db_plant = models.Plant(**plant.dict(), user_id=user.id)
    db.add(db_plant)
    db.commit()
    db.refresh(db_plant)
    
    return db_plant

@app.post("/api/v1/scan", response_model=schemas.ScanResult)
def scan_plant(
    scan_request: schemas.PlantIdentificationRequest,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    """Scan a plant for identification and health analysis"""
    # Lookup user
    user = db.query(models.User).filter(
        models.User.cognito_user_id == user_info["cognito_user_id"]
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # TODO: integrate HuggingFace plant/disease detection model
    mock_result = schemas.ScanResult(
        species="Monstera deliciosa",
        confidence=0.95,
        is_healthy=True,
        disease=None,
        health_score=92.0,
        care_recommendations=[
            "Provide bright, indirect light",
            "Water when soil is dry to touch",
            "Maintain high humidity (60-80%)",
            "Fertilize monthly during growing season"
        ]
    )

    return mock_result


@app.get("/api/v1/dashboard", response_model=schemas.DashboardResponse)
def get_dashboard(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    """Get dashboard data for the user"""
    # Lookup user
    user = db.query(models.User).filter(
        models.User.cognito_user_id == user_info["cognito_user_id"]
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Get user's plants
    plants = db.query(models.Plant).filter(
        models.Plant.user_id == user.id
    ).all()

    # Calculate stats
    total_plants = len(plants)
    healthy_plants = len([p for p in plants if p.current_health_score >= 70])
    plants_needing_care = total_plants - healthy_plants

    # Get user achievements
    user_achievements = db.query(models.UserAchievement).filter(
        models.UserAchievement.user_id == user.id,
        models.UserAchievement.is_completed == True
    ).limit(5).all()

    # Build dashboard response
    stats = schemas.DashboardStats(
        total_plants=total_plants,
        healthy_plants=healthy_plants,
        plants_needing_care=plants_needing_care,
        current_streak=max([p.streak_days for p in plants], default=0),
        total_scans=0,  # TODO: track scan sessions
        achievements_earned=len(user_achievements)
    )

    dashboard_plants = [
        schemas.DashboardPlant(
            id=plant.id,
            name=plant.name,
            species=plant.species,
            health_score=plant.current_health_score,
            streak_days=plant.streak_days,
            last_check_in=plant.last_check_in,
            image_url=plant.image_url,
            needs_attention=plant.current_health_score < 70
        )
        for plant in plants[:5]
    ]

    return schemas.DashboardResponse(
        user=user,
        stats=stats,
        recent_plants=dashboard_plants,
        recent_achievements=user_achievements
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
