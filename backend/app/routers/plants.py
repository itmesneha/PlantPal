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
        # image_url = None
        # if request.image_data:
        #     image_url = upload_plant_image(request.image_data, user.id)
        
        # Create new plant record
        db_plant = models.Plant(
            user_id=user.id,
            name=request.plant_name,
            species=request.species,
            current_health_score=request.health_score or 100.0,
            plant_icon=request.plant_icon or "🌱",  # Default to seedling emoji
            streak_days=1,  # Start with day 1
            last_check_in=func.now()
        )
        
        db.add(db_plant)
        db.flush()  # Get the plant ID without committing yet
        
        # Create initial PlantScan record if scan data is provided
        if request.care_notes or request.disease_detected is not None:
            print(f"📊 Creating initial scan record for new plant")
            
            plant_scan = models.PlantScan(
                user_id=user.id,
                plant_id=db_plant.id,
                health_score=request.health_score or 100.0,
                care_notes=request.care_notes,
                disease_detected=request.disease_detected,
                is_healthy=request.is_healthy if request.is_healthy is not None else True
            )
            
            db.add(plant_scan)
            print(f"✅ Initial scan record created for plant: {db_plant.id}")
        
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

@router.put("/{plant_id}", response_model=schemas.Plant)
def update_plant(
    plant_id: str,
    plant_update: schemas.PlantUpdate,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    """Update plant information (currently only name)"""
    print(f"🔄 UPDATE request for plant_id: {plant_id}")
    print(f"🔍 User info: {user_info}")
    print(f"📝 Update data: {plant_update}")
    
    # Lookup user
    user = db.query(models.User).filter(
        models.User.cognito_user_id == user_info["cognito_user_id"]
    ).first() 
    
    if not user:
        print(f"❌ User not found for cognito_user_id: {user_info['cognito_user_id']}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Find the plant with user ownership check
    plant = db.query(models.Plant).filter(
        models.Plant.id == plant_id,
        models.Plant.user_id == user.id
    ).first()
    
    if not plant:
        print(f"❌ Plant {plant_id} not found or user doesn't own it")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant not found or you don't have permission to edit it"
        )
    
    try:
        # Update only the provided fields
        update_data = plant_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(plant, field, value)
        
        plant.updated_at = func.now()  # Update timestamp
        
        db.commit()
        db.refresh(plant)
        
        print(f"✅ Plant updated successfully: {plant.name}")
        return plant
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error updating plant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update plant. Please try again."
        )

@router.delete("/{plant_id}", response_model=schemas.DeletePlantResponse)
def delete_plant(
    plant_id: str,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    """Delete a plant from user's garden"""
    print(f"🗑️ DELETE request for plant_id: {plant_id}")
    print(f"🔍 User info: {user_info}")
    
    # Lookup user
    user = db.query(models.User).filter(
        models.User.cognito_user_id == user_info["cognito_user_id"]
    ).first()
    
    if not user:
        print(f"❌ User not found for cognito_user_id: {user_info['cognito_user_id']}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    print(f"✅ User found: {user.email} (ID: {user.id})")
    
    # Debug: List all plants for this user
    user_plants = db.query(models.Plant).filter(
        models.Plant.user_id == user.id
    ).all()
    print(f"🌱 User has {len(user_plants)} plants:")
    for p in user_plants:
        print(f"  - {p.id}: {p.name} ({p.species})")
    
    # First, check if plant exists at all
    plant_exists = db.query(models.Plant).filter(
        models.Plant.id == plant_id
    ).first()
    
    if not plant_exists:
        print(f"❌ Plant with ID {plant_id} does not exist in database")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plant with ID {plant_id} not found"
        )
    
    print(f"🌱 Plant exists: {plant_exists.name} (Owner ID: {plant_exists.user_id})")
    
    # Find the plant with user ownership check
    plant = db.query(models.Plant).filter(
        models.Plant.id == plant_id,
        models.Plant.user_id == user.id  # Ensure user owns the plant
    ).first()
    
    if not plant:
        print(f"❌ Plant {plant_id} exists but user {user.id} doesn't own it (actual owner: {plant_exists.user_id})")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant not found or you don't have permission to delete it"
        )
    
    print(f"✅ User owns the plant, proceeding with deletion")
    
    try:
        plant_name = plant.name  # Store name for response message
        plant_id_to_delete = plant.id  # Store ID for logging
        
        print(f"🗑️ About to delete plant: {plant_name} (ID: {plant_id_to_delete})")
        
        # First, handle related records to avoid foreign key constraint issues
        
        # 1. Delete related plant scans
        plant_scans = db.query(models.PlantScan).filter(
            models.PlantScan.plant_id == plant_id_to_delete
        ).all()
        for scan in plant_scans:
            db.delete(scan)
        print(f"🗑️ Deleted {len(plant_scans)} plant scans")
        
        # 2. Now delete the plant
        db.delete(plant)
        print(f"🗑️ Plant marked for deletion in session")
        
        # Commit the transaction
        db.commit()
        print(f"🗑️ Database transaction committed")
        
        # Verify deletion by trying to query the plant again
        deleted_plant_check = db.query(models.Plant).filter(
            models.Plant.id == plant_id_to_delete
        ).first()
        
        if deleted_plant_check is None:
            print(f"✅ Plant successfully deleted from database")
        else:
            print(f"❌ WARNING: Plant still exists in database after deletion!")
            print(f"❌ Plant found: {deleted_plant_check.name} (ID: {deleted_plant_check.id})")
        
        return schemas.DeletePlantResponse(
            success=True,
            message=f"Successfully removed '{plant_name}' from your garden!",
            deleted_plant_id=plant_id
        )
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error deleting plant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete plant. Please try again."
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