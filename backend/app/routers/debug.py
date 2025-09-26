from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models

router = APIRouter(prefix="/api/v1", tags=["debug"])

@router.get("/test")
def test_endpoint():
    """Test endpoint to verify API is working"""
    return {"message": "PlantPal API is working!", "timestamp": "2024-01-15T10:00:00Z"}

@router.delete("/debug/clear-test-user")
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