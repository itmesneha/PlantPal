from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user_info

router = APIRouter(prefix="/api/v1/users", tags=["users"])

@router.get("/me", response_model=schemas.User)
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

@router.post("/", response_model=schemas.User)
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

@router.post("/test")
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
            detail=f"Error creating test user: {str(e)}"
        )