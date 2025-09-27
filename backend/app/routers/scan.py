from fastapi import APIRouter, HTTPException, Depends, status, File, UploadFile
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os
import requests
import base64
import asyncio
import aiohttp
import json
import io
from typing import List, Optional
from PIL import Image
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user_info

load_dotenv()

router = APIRouter(prefix="/api/v1", tags=["scan"])

@router.get("/scan-test")
async def scan_test():
    """Simple test endpoint to check if scan route is working"""
    return {"message": "Scan route is working!", "status": "ok"}

@router.post("/scan-simple", response_model=schemas.ScanResult)
async def scan_simple(
    image: UploadFile = File(...),
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    """Simplified scan endpoint for debugging"""
    return schemas.ScanResult(
        species="Test Plant",
        confidence=0.95,
        is_healthy=True,
        disease=None,
        health_score=100.0,
        care_recommendations=["This is a test response"]
    )

def compress_image(image_data: bytes, max_size_kb: int = 800, quality: int = 85) -> bytes:
    """Compress image to reduce API call payload size"""
    try:
        # Open the image
        img = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary (for JPEG compatibility)
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Calculate target size
        original_size = len(image_data)
        target_size = max_size_kb * 1024
        
        if original_size <= target_size:
            return image_data  # No compression needed
        
        # Resize if image is too large
        max_dimension = 1024
        if max(img.size) > max_dimension:
            ratio = max_dimension / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Compress with quality adjustment
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        compressed_data = output.getvalue()
        
        # If still too large, reduce quality further
        while len(compressed_data) > target_size and quality > 20:
            quality -= 10
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            compressed_data = output.getvalue()
        
        print(f"🗜️ Image compressed: {original_size/1024:.1f}KB → {len(compressed_data)/1024:.1f}KB (quality: {quality})")
        return compressed_data
        
    except Exception as e:
        print(f"❌ Image compression failed: {str(e)}")
        return image_data  # Return original if compression fails

async def query_plantnet_api_async(image_data: bytes) -> dict:
    """Query the PlantNet API for plant species identification (async)"""
    plantnet_api_key = os.getenv('PLANTNET_API_KEY')
    if not plantnet_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PlantNet API key not configured"
        )
    
    api_endpoint = f"https://my-api.plantnet.org/v2/identify/all?api-key={plantnet_api_key}"
    
    try:
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('images', image_data, filename='plant_image.jpg', content_type='image/jpeg')
            
            async with session.post(api_endpoint, data=data, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    raise aiohttp.ClientError(f"PlantNet API returned status {response.status}")
                return await response.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error calling PlantNet API: {str(e)}"
        )

async def query_huggingface_model_async(image_data: bytes) -> dict:
    """Query the Hugging Face plant disease detection model (async)"""
    API_URL = "https://api-inference.huggingface.co/models/linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification"
    
    headers = {
        "Authorization": f"Bearer {os.getenv('HF_TOKEN')}",
        "Content-Type": "application/json"
    }
    
    # Convert image to base64
    image_base64 = base64.b64encode(image_data).decode()
    payload = {"inputs": image_base64}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    raise aiohttp.ClientError(f"Hugging Face API returned status {response.status}")
                result = await response.json()
                print("✅ Hugging Face API response received (async)")
                return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error calling Hugging Face API: {str(e)}"
        )

# Synchronous versions for fallback
def query_plantnet_api(image_data: bytes) -> dict:
    """Query the PlantNet API for plant species identification"""
    plantnet_api_key = os.getenv('PLANTNET_API_KEY')
    if not plantnet_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PlantNet API key not configured"
        )
    
    api_endpoint = f"https://my-api.plantnet.org/v2/identify/all?api-key={plantnet_api_key}"
    
    try:
        files = [('images', ('plant_image.jpg', image_data, 'image/jpeg'))]
        
        response = requests.post(api_endpoint, files=files, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error calling PlantNet API: {str(e)}"
        )

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
        print("✅ Hugging Face API response received")
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error calling Hugging Face API: {str(e)}"
        )

async def parse_disease_predictions_async(hf_response: List[dict], image_data: bytes = None) -> schemas.ScanResult:
    """Parse Hugging Face response into our ScanResult format (async with caching)"""
    if not hf_response or not isinstance(hf_response, list):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid response from disease detection model"
        )
    
    # Always get species from PlantNet API first
    species = "Unknown Plant Species"
    if image_data:
        try:
            plantnet_response = await query_plantnet_api_async(image_data)
            if plantnet_response.get('results') and len(plantnet_response['results']) > 0:
                top_result = plantnet_response['results'][0]
                species_info = top_result['species']
                
                # Get common name (preferred) or scientific name
                common_names = species_info.get('commonNames', [])
                if common_names:
                    species = common_names[0]
                else:
                    species = species_info.get('scientificNameWithoutAuthor', 'Unknown Plant Species')
        except Exception as e:
            print(f"❌ PlantNet API error: {str(e)}")
            # Fallback to extracting from Hugging Face labels if PlantNet fails
            for prediction in hf_response:
                label = prediction.get('label', '').lower()
                if 'healthy' in label:
                    formatted_healthy = prediction.get('label', '').replace('_', ' ').title()
                    if 'Healthy' in formatted_healthy and 'Plant' in formatted_healthy:
                        parts = formatted_healthy.replace('Healthy ', '').replace(' Plant', '')
                        species = parts.strip()
                        break
                elif ' with ' in label:
                    formatted_label = label.replace('_', ' ').title()
                    if ' With ' in formatted_label:
                        species = formatted_label.split(' With ', 1)[0]
                        break
    
    # Get the top prediction for disease analysis
    top_prediction = max(hf_response, key=lambda x: x.get('score', 0))
    prediction_label = top_prediction.get('label', '').lower()
    confidence = top_prediction.get('score', 0.0)
    
    # Determine if plant is healthy and has disease (only if confidence > 50%)
    has_disease = 'healthy' not in prediction_label and confidence > 0.5
    is_healthy = not has_disease
    
    if is_healthy:
        disease = None
        health_score = 100
        care_recommendations = [
            "Continue current care routine",
            "Monitor regularly for any changes",
            "Maintain proper watering and light conditions"
        ]
    else:
        # Parse disease from label (confidence > 50%)
        formatted_label = prediction_label.replace('_', ' ').title()
        
        if ' With ' in formatted_label:
            parts = formatted_label.split(' With ', 1)
            disease = parts[1]
        else:
            disease = formatted_label
            
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

def parse_disease_predictions(hf_response: List[dict], image_data: bytes = None) -> schemas.ScanResult:
    """Parse Hugging Face response into our ScanResult format"""
    if not hf_response or not isinstance(hf_response, list):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid response from disease detection model"
        )
    
    # Always get species from PlantNet API first
    species = "Unknown Plant Species"
    if image_data:
        try:
            plantnet_response = query_plantnet_api(image_data)
            if plantnet_response.get('results') and len(plantnet_response['results']) > 0:
                top_result = plantnet_response['results'][0]
                species_info = top_result['species']
                
                # Get common name (preferred) or scientific name
                common_names = species_info.get('commonNames', [])
                if common_names:
                    species = common_names[0]
                else:
                    species = species_info.get('scientificNameWithoutAuthor', 'Unknown Plant Species')
        except Exception as e:
            print(f"❌ PlantNet API error: {str(e)}")
            # Fallback to extracting from Hugging Face labels if PlantNet fails
            for prediction in hf_response:
                label = prediction.get('label', '').lower()
                if 'healthy' in label:
                    formatted_healthy = prediction.get('label', '').replace('_', ' ').title()
                    if 'Healthy' in formatted_healthy and 'Plant' in formatted_healthy:
                        parts = formatted_healthy.replace('Healthy ', '').replace(' Plant', '')
                        species = parts.strip()
                        break
                elif ' with ' in label:
                    formatted_label = label.replace('_', ' ').title()
                    if ' With ' in formatted_label:
                        species = formatted_label.split(' With ', 1)[0]
                        break
    
    # Get the top prediction for disease analysis
    top_prediction = max(hf_response, key=lambda x: x.get('score', 0))
    prediction_label = top_prediction.get('label', '').lower()
    confidence = top_prediction.get('score', 0.0)
    
    # Determine if plant is healthy and has disease (only if confidence > 50%)
    has_disease = 'healthy' not in prediction_label and confidence > 0.5
    is_healthy = not has_disease
    
    if is_healthy:
        disease = None
        health_score = 100
        care_recommendations = [
            "Continue current care routine",
            "Monitor regularly for any changes",
            "Maintain proper watering and light conditions"
        ]
    else:
        # Parse disease from label (confidence > 50%)
        formatted_label = prediction_label.replace('_', ' ').title()
        
        if ' With ' in formatted_label:
            parts = formatted_label.split(' With ', 1)
            disease = parts[1]
        else:
            disease = formatted_label
            
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
async def scan_plant(
    image: UploadFile = File(..., description="Plant image for disease detection"),
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    """Scan a plant for identification and health analysis using Hugging Face AI (optimized)"""
    print("🚀 Starting scan_plant function...")
    
    try:
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
        
        print(f"✅ User found: {user.email}")
        
        # Validate image file
        print(f"📎 Image details: filename={image.filename}, content_type={image.content_type}, size={image.size}")
        
        if not image.content_type or not image.content_type.startswith('image/'):
            print(f"❌ Invalid content type: {image.content_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
        
        # Check file size (limit to 10MB)
        if image.size and image.size > 10 * 1024 * 1024:
            print(f"❌ File too large: {image.size} bytes")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image file too large (max 10MB)"
            )
        
        print("📸 Starting image processing...")
        
        # Read and compress image data
        original_image_data = image.file.read()
        print(f"📸 Image read successfully: {len(original_image_data)/1024:.1f}KB")
        
        # Compress image to reduce API payload size
        print("🗜️ Compressing image...")
        compressed_image_data = compress_image(original_image_data)
        print(f"🗜️ Image compressed: {len(compressed_image_data)/1024:.1f}KB")
        
        # Check API keys
        hf_token = os.getenv('HF_TOKEN')
        plantnet_key = os.getenv('PLANTNET_API_KEY')
        print(f"🔑 HF_TOKEN: {'Present' if hf_token else 'MISSING'}")
        print(f"🔑 PLANTNET_API_KEY: {'Present' if plantnet_key else 'MISSING'}")
        
        # Check if HF_TOKEN is available
        if not hf_token:
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
        
        # Call both APIs concurrently for better performance
        print("🚀 Calling APIs concurrently...")
        try:
            plantnet_task = query_plantnet_api_async(compressed_image_data)
            hf_task = query_huggingface_model_async(compressed_image_data)
            
            plantnet_response, hf_response = await asyncio.gather(
                plantnet_task, hf_task, return_exceptions=True
            )
            
            # Handle exceptions from concurrent calls
            if isinstance(plantnet_response, Exception):
                print(f"❌ PlantNet API failed: {plantnet_response}")
                plantnet_response = {"results": []}  # Empty fallback
            
            if isinstance(hf_response, Exception):
                print(f"❌ Hugging Face API failed: {hf_response}")
                # Fallback to sync call or mock data
                try:
                    hf_response = query_huggingface_model(compressed_image_data)
                except:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="All AI services are currently unavailable"
                    )
        
        except Exception as e:
            print(f"❌ Error in concurrent API calls: {str(e)}")
            # Fallback to synchronous calls
            try:
                plantnet_response = query_plantnet_api(compressed_image_data)
            except:
                plantnet_response = {"results": []}
            
            hf_response = query_huggingface_model(compressed_image_data)
        
        # Parse and return result using async function
        result = await parse_disease_predictions_async(hf_response, compressed_image_data)
        
        return result
        
    except Exception as e:
        # Log the full error for debugging
        print(f"❌ ERROR in plant scan: {str(e)}")
        print(f"❌ ERROR type: {type(e).__name__}")
        import traceback
        print(f"❌ ERROR traceback: {traceback.format_exc()}")
        
        # Return detailed error information in development
        return schemas.ScanResult(
            species="Error Plant",
            confidence=0.0,
            is_healthy=False,
            disease="Processing Error",
            health_score=0.0,
            care_recommendations=[
                f"Error occurred: {str(e)[:200]}",
                "Please try again with a different image",
                "If problem persists, contact support"
            ]
        )
    finally:
        # Clean up
        try:
            image.file.close()
        except:
            pass