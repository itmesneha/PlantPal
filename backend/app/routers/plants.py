from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List
import base64
import boto3
import os
import uuid
from datetime import datetime

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

# @router.post("/", response_model=schemas.Plant)
# def create_plant(
#     plant: schemas.PlantCreate,
#     user_info: dict = Depends(get_current_user_info),
#     db: Session = Depends(get_db)
# ):
#     """Add a new plant to user's garden"""
#     user = db.query(models.User).filter(
#         models.User.cognito_user_id == user_info["cognito_user_id"]
#     ).first()
    
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )
    
#     db_plant = models.Plant(**plant.dict(), user_id=user.id)
#     db.add(db_plant)
#     db.commit()
#     db.refresh(db_plant)
    
#     return db_plant

@router.post("/add-to-garden", response_model=schemas.AddToGardenResponse)
def add_to_garden(
    request: schemas.AddToGardenRequest,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    """Add a plant to user's garden from scan results"""
    # Lookup user
    user = db.query(models.User).filter(
        models.User.cognito_user_id == user_info["cognito_user_id"]
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Handle image upload to S3 if provided
        image_url = None
        # if request.image_data:
        #     image_url = upload_plant_image(request.image_data, user.id)
        
        # Create new plant record
        db_plant = models.Plant(
            user_id=user.id,
            name=request.plant_name,
            species=request.species,
            common_name=request.common_name,
            location=request.location,
            care_notes=request.care_notes,
            current_health_score=request.health_score or 100.0,
            plant_icon=request.plant_icon or "🌱",  # Default to seedling emoji
            streak_days=1,  # Start with day 1
            last_check_in=func.now(),
            image_url=image_url,
            created_at=func.now(),
            updated_at=func.now()
        )
        
        db.add(db_plant)
        db.commit()
        db.refresh(db_plant)
        
        return schemas.AddToGardenResponse(
            success=True,
            plant_id=db_plant.id,
            message=f"Successfully added '{request.plant_name}' to your garden!",
            plant=db_plant  # Pydantic will handle the conversion
        )
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error adding plant to garden: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add plant to garden. Please try again."
        )

# def upload_plant_image(base64_image: str, user_id: str) -> str:
#     """Upload plant image to S3 and return the URL"""
#     try:
#         # Initialize S3 client
#         s3_client = boto3.client(
#             's3',
#             aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
#             aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
#             region_name=os.getenv('AWS_REGION', 'us-east-1')
#         )
        
#         bucket_name = os.getenv('S3_BUCKET_NAME', 'plantpal-images')
        
#         # Decode base64 image
#         image_data = base64.b64decode(base64_image)
        
#         # Generate unique filename
#         filename = f"plants/{user_id}/{uuid.uuid4()}.jpg"
        
#         # Upload to S3
#         s3_client.put_object(
#             Bucket=bucket_name,
#             Key=filename,
#             Body=image_data,
#             ContentType='image/jpeg'
#         )
        
#         # Return S3 URL
#         image_url = f"https://{bucket_name}.s3.amazonaws.com/{filename}"
#         print(f"✅ Plant image uploaded: {image_url}")
#         return image_url
        
#     except Exception as e:
#         print(f"❌ Failed to upload plant image: {str(e)}")
#         # Return None if upload fails - plant can still be added without image
#         return None