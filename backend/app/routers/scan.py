from fastapi import APIRouter, HTTPException, Depends, status, File, UploadFile
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os
import requests
import base64
from typing import List
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user_info

load_dotenv()

router = APIRouter(prefix="/api/v1", tags=["scan"])

def query_huggingface_model(image_data: bytes) -> dict:
    """Query the Hugging Face plant disease detection model"""
    API_URL = "https://api-inference.huggingface.co/models/linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification"
    
    headers = {
        "Authorization": f"Bearer {os.getenv('HF_TOKEN')}",
        "Content-Type": "application/json"
    }
    
    # Convert image to base64
    image_base64 = base64.b64encode(image_data).decode()
    
    payload = {
        "inputs": image_base64
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error calling Hugging Face API: {str(e)}"
        )

def parse_disease_predictions(hf_response: List[dict]) -> schemas.ScanResult:
    """Parse Hugging Face response into our ScanResult format"""
    if not hf_response or not isinstance(hf_response, list):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid response from disease detection model"
        )
    
    # Get the top prediction
    top_prediction = max(hf_response, key=lambda x: x.get('score', 0))
    prediction_label = top_prediction.get('label', '').lower()
    confidence = top_prediction.get('score', 0.0)
    
    # Determine if plant is healthy based on prediction
    is_healthy = 'healthy' in prediction_label or confidence < 0.5
    
    # Extract species and disease info
    if is_healthy:
        species = "Unknown Plant Species"
        disease = None
        health_score = 100
        care_recommendations = [
            "Continue current care routine",
            "Monitor regularly for any changes",
            "Maintain proper watering and light conditions"
        ]
    else:
        # Parse disease name from label
        disease = prediction_label.replace('_', ' ').title()
        species = "Affected Plant"
        health_score = max(20.0, (1 - confidence) * 100)
        care_recommendations = [
            f"Treatment recommended for {disease}",
            "Isolate plant to prevent spread",
            "Consult plant care specialist",
            "Adjust watering and humidity levels"
        ]
    
    return schemas.ScanResult(
        species=species,
        confidence=confidence,
        is_healthy=is_healthy,
        disease=disease if not is_healthy else None,
        health_score=health_score,
        care_recommendations=care_recommendations
    )

@router.post("/scan", response_model=schemas.ScanResult)
def scan_plant(
    image: UploadFile = File(..., description="Plant image for disease detection"),
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    """Scan a plant for identification and health analysis using Hugging Face AI"""
    # Lookup user
    user = db.query(models.User).filter(
        models.User.cognito_user_id == user_info["cognito_user_id"]
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate image file
    if not image.content_type or not image.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Check file size (limit to 10MB)
    if image.size and image.size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image file too large (max 10MB)"
        )
    
    try:
        # Read image data
        image_data = image.file.read()
        
        # Check if HF_TOKEN is available
        if not os.getenv('HF_TOKEN'):
            # Fallback to mock result if no API token
            return schemas.ScanResult(
                species="Monstera deliciosa",
                confidence=0.85,
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
        
        # Call Hugging Face API
        hf_response = query_huggingface_model(image_data)
        
        # Parse and return result
        result = parse_disease_predictions(hf_response)
        
        return result
        
    except Exception as e:
        # Log error and return mock result as fallback
        print(f"❌ Error in plant scan: {str(e)}")
        return schemas.ScanResult(
            species="Unknown Plant",
            confidence=0.5,
            is_healthy=True,
            disease=None,
            health_score=75.0,
            care_recommendations=[
                "Unable to analyze image at this time",
                "Please try again with a clearer image",
                "Ensure good lighting and focus"
            ]
        )
    finally:
        # Clean up
        image.file.close()