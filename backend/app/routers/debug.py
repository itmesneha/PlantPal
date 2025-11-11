from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models

router = APIRouter(prefix="/api/v1", tags=["debug"])

@router.get("/test")
def test_endpoint():
    """Test endpoint to verify API is working"""
    return {"message": "PlantPal API is working!", "timestamp": "2024-01-15T10:00:00Z"}
