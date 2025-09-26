from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user_info

router = APIRouter(prefix="/api/v1/plants", tags=["plants"])

@router.get("/", response_model=List[schemas.Plant])
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

@router.post("/", response_model=schemas.Plant)
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