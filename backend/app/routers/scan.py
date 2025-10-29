from fastapi import APIRouter, HTTPException, Depends, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os
import requests
import base64
import asyncio
import aiohttp
import json
import io
import time
import datetime
from typing import List, Optional
from PIL import Image
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user_info
from app.routers.achievements import update_achievement_progress, calculate_user_streak

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

@router.post("/care-recommendations")
async def get_care_recommendations(
    request: dict,
    user_info: dict = Depends(get_current_user_info)
):
    """Get AI-powered care recommendations for plants using OpenRouter API"""
    try:
        # Extract plant details from request
        plant_species = request.get("species", "plant")
        disease = request.get("disease", None)
        
        # Build the prompt based on available information
        if disease:
            prompt = f"Give me 4 sentences short actionable care instructions for taking care of a {plant_species} with {disease}."
        else:
            prompt = f"Give me 4 sentences short actionable care instructions for taking care of a {plant_species}."
        
        # OpenRouter API configuration
        openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        if not openrouter_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenRouter API key not configured"
            )
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openrouter_api_key}"
        }
         
        payload = {
            "model": "google/gemma-3-27b-it:free",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        
        print(f"🤖 Requesting care recommendations for: {prompt}")
        
        # Make API call to OpenRouter
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            ) as response:
                response.raise_for_status()
                result = await response.json()
                
                # Extract the care recommendations from response
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content']
                    
                    # Clean up the content - remove extra whitespace and formatting
                    content = content.strip()
                    
                    # Import regex at the top of this section
                    import re
                    
                    # First, handle line breaks and normalize whitespace
                    content = re.sub(r'\n+', '\n', content)  # Normalize multiple line breaks
                    
                    # Look for numbered lists (1., 2., 3.) or bullet points
                    recommendations = []
                    
                    # Split by lines first to handle numbered/bulleted lists
                    lines = [line.strip() for line in content.split('\n') if line.strip()]
                    
                    for line in lines:
                        # Skip obvious header/intro lines but be more specific
                        line_lower = line.lower().strip()
                        
                        # More specific patterns for intro lines to skip
                        should_skip = False
                        
                        # Skip if it's clearly an introductory sentence (starts with these patterns)
                        intro_starts = [
                            'okay, here are',
                            'here are 4 short',
                            'here are 3 short', 
                            'here are some',
                            'below are 4',
                            'below are 3',
                            'here is a list',
                            'these are the'
                        ]
                        
                        for intro in intro_starts:
                            if line_lower.startswith(intro):
                                should_skip = True
                                break
                        
                        # Skip standalone notes or empty lines
                        if (line_lower.startswith('important note:') or 
                            line_lower.startswith('note:') or
                            line_lower.startswith('**important note') or
                            len(line.strip()) < 5):
                            should_skip = True
                        
                        if should_skip:
                            continue
                            
                        # Clean up numbered lists (1., 2., 3.) and bullet points
                        cleaned_line = line
                        
                        # Remove numbering patterns
                        cleaned_line = re.sub(r'^\d+\.\s*', '', cleaned_line)  # Remove "1. "
                        cleaned_line = re.sub(r'^\*+\s*', '', cleaned_line)    # Remove "* "
                        cleaned_line = re.sub(r'^\-+\s*', '', cleaned_line)    # Remove "- "
                        
                        # Enhanced markdown formatting cleanup
                        # Remove bold formatting but preserve emphasis with plain text
                        cleaned_line = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned_line)  # **text** -> text
                        cleaned_line = re.sub(r'\*(.*?)\*', r'\1', cleaned_line)      # *text* -> text
                        
                        # Clean up various markdown artifacts
                        cleaned_line = re.sub(r'`([^`]+)`', r'\1', cleaned_line)     # `code` -> code
                        cleaned_line = re.sub(r'_{2,}', '', cleaned_line)            # Remove multiple underscores
                        cleaned_line = re.sub(r'\*{3,}', '', cleaned_line)           # Remove multiple asterisks
                        
                        # Handle special characters and formatting
                        cleaned_line = re.sub(r'&amp;', '&', cleaned_line)           # Fix HTML entities
                        cleaned_line = re.sub(r'&lt;', '<', cleaned_line)
                        cleaned_line = re.sub(r'&gt;', '>', cleaned_line)
                        
                        # Clean up excessive punctuation and spacing
                        cleaned_line = re.sub(r'\s+', ' ', cleaned_line)             # Multiple spaces -> single space
                        cleaned_line = re.sub(r'([.!?]){2,}', r'\1', cleaned_line)   # Multiple punctuation -> single
                        
                        # Handle title-like formatting (preserve colons for clarity)
                        cleaned_line = re.sub(r'^([^:]+):\s*', r'\1: ', cleaned_line)
                        
                        # Remove trailing/leading special characters
                        cleaned_line = cleaned_line.strip(' *-_~')
                        
                        if cleaned_line and len(cleaned_line) > 10:  # Only include substantial recommendations
                            recommendations.append(cleaned_line)
                    
                    # If we didn't find structured recommendations, fall back to sentence splitting
                    if not recommendations:
                        # Clean the content first
                        clean_content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  # Remove bold
                        clean_content = re.sub(r'\*(.*?)\*', r'\1', clean_content)  # Remove italic
                        clean_content = re.sub(r'`([^`]+)`', r'\1', clean_content)  # Remove code
                        clean_content = re.sub(r'\s+', ' ', clean_content)          # Normalize spaces
                        
                        # Remove common introductory phrases more aggressively but more specifically
                        intro_patterns = [
                            r'(?i)^.*?okay,?\s*here are \d+.*?:',
                            r'(?i)^.*?here are \d+ short.*?:',
                            r'(?i)^.*?below are \d+.*?:',
                            r'(?i)^.*?here is a list.*?:',
                            r'(?i)^.*?these are the.*?:',
                            r'(?i)^\s*important note:.*$',
                            r'(?i)^\s*\*\*important note.*$'
                        ]
                        
                        for pattern in intro_patterns:
                            clean_content = re.sub(pattern, '', clean_content).strip()
                        
                        recommendations = [
                            sentence.strip() 
                            for sentence in clean_content.split('.') 
                            if sentence.strip() and len(sentence.strip()) > 10
                        ]
                    
                    # Final cleanup pass on all recommendations
                    cleaned_recommendations = []
                    for rec in recommendations:
                        # One final cleanup
                        final_rec = rec.strip()
                        final_rec = re.sub(r'\s+', ' ', final_rec)  # Normalize spaces
                        
                        # Ensure proper sentence ending
                        if final_rec and not final_rec.endswith(('.', '!', '?')):
                            final_rec += '.'
                            
                        if final_rec and len(final_rec) > 10:
                            cleaned_recommendations.append(final_rec)
                    
                    # Use cleaned recommendations or fallback
                    recommendations = cleaned_recommendations if cleaned_recommendations else [content.strip()]
                    
                    print(f"✅ Generated {len(recommendations)} care recommendations")
                    
                    return {
                        "species": plant_species,
                        "disease": disease,
                        "care_recommendations": recommendations[:5],  # Limit to 5 recommendations
                        "source": "AI-powered by OpenRouter"
                    }
                else:
                    print("❌ No content in OpenRouter response")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Invalid response from AI service"
                    )
                    
    except aiohttp.ClientError as e:
        print(f"❌ OpenRouter API error: {str(e)}")
        # Fallback to generic recommendations
        return {
            "species": request.get("species", "plant"),
            "disease": request.get("disease"),
            "care_recommendations": [
                "Ensure proper watering - soil should be moist but not waterlogged",
                "Provide adequate light conditions for your plant species",
                "Monitor for pests and diseases regularly and treat promptly"
            ],
            "source": "Fallback recommendations (AI service unavailable)"
        }
        
    except Exception as e:
        print(f"❌ Error getting care recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get care recommendations: {str(e)}"
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
    API_URL = "https://router.huggingface.co/hf-inference/models/linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification"
    # API_URL = "https://api-inference.huggingface.co/models/linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification"
    
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

def query_huggingface_model(image_data: bytes, max_retries: int = 2) -> dict:
    """Query the Hugging Face plant disease detection model with retry logic"""
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
    
    for attempt in range(max_retries + 1):
        try:
            timeout = 60 if attempt == 0 else 30  # Longer timeout on first attempt
            print(f"🔄 HuggingFace API attempt {attempt + 1}/{max_retries + 1} (timeout: {timeout}s)")
            
            response = requests.post(API_URL, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            
            # Check if response indicates model is still loading
            response_data = response.json()
            if isinstance(response_data, dict) and response_data.get('error'):
                error_msg = response_data.get('error', '')
                if 'loading' in error_msg.lower():
                    print(f"⏳ Model is loading, waiting 10 seconds...")
                    if attempt < max_retries:
                        time.sleep(10)
                        continue
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Hugging Face model is still loading, please try again in a few minutes"
                        )
            
            print("✅ Hugging Face API response received")
            return response_data
            
        except requests.exceptions.Timeout as e:
            print(f"⏰ HuggingFace API timeout on attempt {attempt + 1}")
            if attempt < max_retries:
                print(f"🔄 Retrying in 5 seconds...")
                time.sleep(5)
                continue
            else:
                print("❌ All HuggingFace API attempts failed due to timeout")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Hugging Face API timeout after {max_retries + 1} attempts"
                )
        except requests.exceptions.RequestException as e:
            print(f"❌ HuggingFace API error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries:
                print(f"🔄 Retrying in 3 seconds...")
                time.sleep(3)
                continue
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Error calling Hugging Face API: {str(e)}"
                )

async def parse_disease_predictions_for_rescan_async(hf_response: List[dict], image_data: bytes, known_species: str) -> schemas.ScanResult:
    """Parse Hugging Face response for rescan (skip species detection, use known species)"""
    if not hf_response or not isinstance(hf_response, list):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid response from disease detection model"
        )
    
    # Use the known species instead of detecting it
    species = known_species
    print(f"🔄 Using known species for rescan: {species}")
    
    # Find the highest-scoring disease prediction
    best_prediction = max(hf_response, key=lambda x: x.get('score', 0))
    
    # Extract disease information
    label = best_prediction.get('label', '').lower()
    confidence = best_prediction.get('score', 0.0)
    
    print(f"🔍 Disease analysis - Label: {label}, Confidence: {confidence:.3f}")
    
    # Determine if plant is healthy and extract disease
    is_healthy = True
    disease = None
    health_score = 85.0  # Default healthy score
    
    if 'healthy' not in label and confidence > 0.5:  # Use same threshold as new plant scans
        is_healthy = False
        
        # Parse disease name from label - extract only the disease part
        formatted_label = label.replace('_', ' ').title()
        
        # For rescans, we want just the disease name, not the full "Plant With Disease" format
        if ' With ' in formatted_label:
            # Extract disease after "With" (e.g., "Bell Pepper With Bacterial Spot" -> "Bacterial Spot")
            disease = formatted_label.split(' With ', 1)[1]
        elif ' ' in formatted_label and any(word in formatted_label.lower() for word in ['spot', 'rot', 'blight', 'mold', 'wilt', 'burn', 'rust', 'scab']):
            # Handle cases where disease is in the label but not in "With" format
            # Try to extract disease-specific terms
            words = formatted_label.split()
            disease_words = []
            found_disease_term = False
            
            for word in words:
                if word.lower() in ['spot', 'rot', 'blight', 'mold', 'wilt', 'burn', 'rust', 'scab', 'bacterial', 'fungal', 'viral']:
                    found_disease_term = True
                    disease_words.append(word)
                elif found_disease_term:
                    disease_words.append(word)
                elif word.lower() in ['bacterial', 'fungal', 'viral', 'early', 'late', 'common', 'southern']:
                    disease_words.append(word)
            
            if disease_words:
                disease = ' '.join(disease_words)
            else:
                disease = formatted_label  # Fallback to full label
        else:
            disease = formatted_label
            
        # Scale health score based on confidence (inverse relationship)
        health_score = max(30.0, 85.0 - (confidence * 55.0))
    else:
        # Plant appears healthy - use same logic as new plant scans
        health_score = 100.0
    
    print(f"🏥 Health assessment - Healthy: {is_healthy}, Disease: {disease}, Score: {health_score:.1f}")
    
    # Get AI care recommendations using the existing get_care_recommendations function
    care_recommendations = []
    
    # For healthy plants, use generic recommendations without API call
    if is_healthy:
        care_recommendations = [
            "Continue current care routine",
            "Monitor regularly for any changes", 
            "Maintain proper watering and light conditions"
        ]
        print(f"✅ Using generic recommendations for healthy {species}")
    else:
        # Only call API for diseased plants
        try:
            # Use the existing get_care_recommendations function which has proper parsing
            care_request = {
                "species": species,
                "disease": disease
            }
            
            # Create a mock user_info dict (not used in get_care_recommendations but required by signature)
            mock_user_info = {"cognito_user_id": "rescan_user"}
            
            print(f"🤖 Getting care recommendations for diseased rescan using existing function: {species}, disease: {disease}")
            
            # Call the existing get_care_recommendations function
            care_response = await get_care_recommendations(care_request, mock_user_info)
            
            if care_response and 'care_recommendations' in care_response:
                care_recommendations = care_response['care_recommendations']
                print(f"✅ Got {len(care_recommendations)} care recommendations from existing function")
            
        except Exception as e:
            print(f"⚠️ Failed to get AI care recommendations for diseased rescan: {e}")
    
    # Fallback recommendations if API call failed
    if not care_recommendations:
        if is_healthy:
            care_recommendations = [
                f"Continue current care routine for your {species}",
                "Monitor for any changes in leaf color or texture",
                "Maintain consistent watering schedule",
                "Ensure adequate light conditions"
            ]
        else:
            care_recommendations = [
                f"Your {species} shows signs of {disease}",
                "Isolate from other plants if possible",
                "Adjust watering frequency",
                "Consider consulting plant care resources"
            ]
    
    return schemas.ScanResult(
        species=species,
        confidence=1.0,  # We know the species with certainty for rescans
        is_healthy=is_healthy,
        disease=disease,
        health_score=health_score,
        care_recommendations=care_recommendations
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
    has_disease = 'healthy' not in prediction_label and confidence > 0.50
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
    plant_id: Optional[str] = Form(None, description="Optional plant ID to associate scan with existing plant"),
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    """Scan a plant for identification and health analysis using Hugging Face AI (optimized)"""
    print("🚀 Starting scan_plant function...")
    
    try:
        print(f"🔍 User info: {user_info}")
        print(f"🌱 Plant ID provided: {plant_id}")
        
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
        
        # Check if this is a rescan of existing plant
        existing_plant = None
        if plant_id:
            existing_plant = db.query(models.Plant).filter(
                models.Plant.id == plant_id,
                models.Plant.user_id == user.id
            ).first()
            
            if not existing_plant:
                print(f"❌ Plant not found for ID: {plant_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Plant not found"
                )
            
            print(f"🔄 Rescanning existing plant: {existing_plant.name} ({existing_plant.species})")
        
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
            if existing_plant:
                # For rescans, use known species and focus on health analysis
                scan_result = schemas.ScanResult(
                    species=existing_plant.species,  # Use existing species
                    confidence=1.0,  # We know the species with certainty
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
            else:
                # New plant scan - need species identification
                scan_result = schemas.ScanResult(
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
        else:
            if existing_plant:
                # For rescans, skip species identification and focus only on health analysis
                print(f"🔄 Rescanning - skipping species identification, focusing on health analysis for {existing_plant.species}")
                try:
                    # Only call disease detection, not species identification
                    hf_response = await query_huggingface_model_async(compressed_image_data)
                    
                    # Parse health analysis results using known species
                    scan_result = await parse_disease_predictions_for_rescan_async(
                        hf_response, 
                        compressed_image_data, 
                        existing_plant.species
                    )
                    
                except Exception as e:
                    print(f"❌ Health analysis failed for rescan: {str(e)}")
                    # Fallback for rescans
                    scan_result = schemas.ScanResult(
                        species=existing_plant.species,
                        confidence=1.0,
                        is_healthy=True,
                        disease=None,
                        health_score=85.0,
                        care_recommendations=[
                            "Health analysis temporarily unavailable",
                            "Continue with regular care routine",
                            "Monitor plant visually for changes",
                            "Try scanning again in a few minutes"
                        ]
                    )
            else:
                # New plant scan - call both APIs concurrently for species identification and health
                print("🚀 New plant scan - calling APIs for species identification and health analysis...")
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
                    # Last resort: provide a fallback response with basic plant care advice
                    print("🛡️ Using fallback response due to API failures")
                    
                    # Try to extract plant info from filename if available
                    filename = image.filename or "unknown"
                    species_guess = "Houseplant"
                    
                    # Simple filename-based species detection
                    filename_lower = filename.lower()
                    if any(word in filename_lower for word in ['monstera', 'deliciosa']):
                        species_guess = "Monstera deliciosa"
                    elif any(word in filename_lower for word in ['philodendron', 'philo']):
                        species_guess = "Philodendron"
                    elif any(word in filename_lower for word in ['pothos', 'devil', 'ivy']):
                        species_guess = "Pothos"
                    elif any(word in filename_lower for word in ['snake', 'sansevieria']):
                        species_guess = "Snake Plant"
                    elif any(word in filename_lower for word in ['ficus', 'fiddle', 'leaf']):
                        species_guess = "Fiddle Leaf Fig"
                    
                    # Assume plant is healthy if we can't analyze it
                    scan_result = schemas.ScanResult(
                        species=species_guess,
                        confidence=0.75,
                        is_healthy=True,
                        disease=None,
                        health_score=85.0,
                        care_recommendations=[
                            "Provide bright, indirect light",
                            "Water when top inch of soil is dry",
                            "Maintain moderate humidity (40-60%)",
                            "Monitor for pests and diseases regularly",
                            "AI analysis temporarily unavailable - manual inspection recommended"
                        ]
                    )
                else:
                    # Parse and return result using async function
                    scan_result = await parse_disease_predictions_async(hf_response, compressed_image_data)
        
        # 💾 SAVE TO DATABASE ONLY IF SCANNING EXISTING PLANT
        if plant_id:
            print("💾 Saving scan results to database for existing plant...")
            
            try:
                # Create PlantScan record for existing plants in garden
                plant_scan = models.PlantScan(
                    user_id=user.id,
                    plant_id=plant_id,
                    health_score=scan_result.health_score,
                    care_notes="; ".join(scan_result.care_recommendations) if scan_result.care_recommendations else None,
                    disease_detected=scan_result.disease,
                    is_healthy=scan_result.is_healthy
                )
                
                db.add(plant_scan)
                
                # 🔄 UPDATE PLANTS TABLE WITH NEW HEALTH SCORE
                if existing_plant:
                    existing_plant.current_health_score = scan_result.health_score
                    db.add(existing_plant)  # Ensure the plant is tracked for updates
                    print(f"🔄 Updated plant current_health_score: {existing_plant.name} -> {scan_result.health_score}")
                
                db.commit()
                db.refresh(plant_scan)
                if existing_plant:
                    db.refresh(existing_plant)  # Refresh the plant object too                
            except Exception as db_error:
                print(f"❌ Database error: {db_error}")
                db.rollback()
                # Continue without failing the whole request - user still gets scan results
                print("⚠️ Continuing without database storage...")
        else:
            print("ℹ️ Species identification scan - not saving to database (will save when added to garden)")
        
        try:                    
            # Update streak
            user_id = user.id
            
            # Calculate current streak across all scans
            current_streak = calculate_user_streak(user_id, db)

            # Persist streak metadata on the scanned plant so dashboard/storefront stay in sync
            if plant_id:
                try:
                    plant_for_update = existing_plant or db.query(models.Plant).filter(
                        models.Plant.id == plant_id,
                        models.Plant.user_id == user_id
                    ).first()
                    if plant_for_update:
                        plant_for_update.streak_days = current_streak
                        plant_for_update.last_check_in = datetime.datetime.utcnow()
                        db.add(plant_for_update)
                        db.commit()
                        db.refresh(plant_for_update)
                except Exception as plant_update_error:
                    print(f"⚠️ Failed to persist streak metadata on plant {plant_id}: {plant_update_error}")
                    db.rollback()

            # Calculate and update streak achievements
            newly_completed_streak = update_achievement_progress(
                user_id,
                "streak",
                current_streak,
                db
            )
                    
            if newly_completed_streak:
                print(f"🔥 {len(newly_completed_streak)} streak achievement(s) unlocked!")
                    
            # Count total scans for this user
            total_scans = db.query(models.PlantScan).filter(
                models.PlantScan.user_id == user_id
            ).count()
            if not existing_plant:
                total_scans += 1
                    
            # Update scans_count achievements
            newly_completed_scans = update_achievement_progress(
                user_id,
                "scans_count",
                total_scans,
                db
            )
                    
            if newly_completed_scans:
                print(f"📸 {len(newly_completed_scans)} scan achievement(s) unlocked!")
                   
            # Track all newly completed achievements
            all_newly_completed = newly_completed_streak + newly_completed_scans
                  
            if all_newly_completed:
                # You can return these in the response if needed
                print(f"✨ Total {len(all_newly_completed)} achievement(s) unlocked this scan!")
                        
        except Exception as e:
            print(f"⚠️ Error updating achievements: {str(e)}")
            print(f"✅ PlantScan created and plant health updated: {plant_scan.id}")
        
        return scan_result
        
    except Exception as e:
        # Log the full error for debugging
        print(f"❌ ERROR in plant scan: {str(e)}")
        print(f"❌ ERROR type: {type(e).__name__}")
        import traceback
        print(f"❌ ERROR traceback: {traceback.format_exc()}")
        
        # Rollback any pending database changes
        try:
            db.rollback()
        except:
            pass
        
        # If this is an HTTP exception, re-raise it
        if isinstance(e, HTTPException):
            # For service unavailable errors, provide a user-friendly fallback
            if e.status_code == 503:
                return schemas.ScanResult(
                    species="Plant (AI Analysis Unavailable)",
                    confidence=0.5,
                    is_healthy=True,
                    disease=None,
                    health_score=75.0,
                    care_recommendations=[
                        "AI plant analysis is temporarily unavailable",
                        "Please inspect your plant visually for:",
                        "- Yellow or brown leaves",
                        "- Unusual spots or discoloration", 
                        "- Pest activity or webbing",
                        "Continue with regular care routine",
                        "Try scanning again in a few minutes"
                    ]
                )
            raise e
        
        # For other errors, provide a generic fallback
        return schemas.ScanResult(
            species="Unknown Plant",
            confidence=0.3,
            is_healthy=True,
            disease=None,
            health_score=70.0,
            care_recommendations=[
                "Unable to analyze plant image at this time",
                "Ensure image is clear and well-lit",
                "Try taking photo from different angle",
                "Check that plant is main subject in image",
                "Manual inspection recommended"
            ]
        )
    finally:
        # Clean up
        try:
            image.file.close()
        except:
            pass


@router.get("/latest-health/{plant_id}")
async def get_latest_plant_health(
    plant_id: str,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    """Get the latest health information for a specific plant"""
    print(f"🔍 Getting latest health info for plant: {plant_id}")
    
    # Lookup user
    user = db.query(models.User).filter(
        models.User.cognito_user_id == user_info["cognito_user_id"]
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get plant to verify ownership
    plant = db.query(models.Plant).filter(
        models.Plant.id == plant_id,
        models.Plant.user_id == user.id
    ).first()
    
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant not found or not owned by user"
        )
    
    # Get latest plant scan
    latest_scan = db.query(models.PlantScan).filter(
        models.PlantScan.plant_id == plant_id,
        models.PlantScan.user_id == user.id
    ).order_by(models.PlantScan.scan_date.desc()).first()
    
    if not latest_scan:
        # Return default healthy status if no scans exist yet
        return {
            "plant_id": plant_id,
            "disease_detected": None,
            "is_healthy": True,
            "care_notes": "No scan data available yet. Perform a scan to get health information.",
            "health_score": plant.current_health_score,
            "scan_date": None
        }
    
    print(f"✅ Found latest scan for plant {plant_id}: {latest_scan.id}")
    
    return {
        "plant_id": plant_id,
        "disease_detected": latest_scan.disease_detected,
        "is_healthy": latest_scan.is_healthy,
        "care_notes": latest_scan.care_notes or "No care notes available",
        "health_score": latest_scan.health_score,
        "scan_date": latest_scan.scan_date
    }


@router.get("/latest/{plant_id}", response_model=schemas.PlantScan)
async def get_latest_plant_scan(
    plant_id: str,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    """Get the latest scan data for a specific plant"""
    print(f"🔍 Getting latest scan for plant: {plant_id}")
    
    # Lookup user
    user = db.query(models.User).filter(
        models.User.cognito_user_id == user_info["cognito_user_id"]
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get plant to verify ownership
    plant = db.query(models.Plant).filter(
        models.Plant.id == plant_id,
        models.Plant.user_id == user.id
    ).first()
    
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant not found or not owned by user"
        )
    
    # Get latest plant scan
    latest_scan = db.query(models.PlantScan).filter(
        models.PlantScan.plant_id == plant_id,
        models.PlantScan.user_id == user.id
    ).order_by(models.PlantScan.scan_date.desc()).first()
    
    if not latest_scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No scans found for this plant"
        )
    
    print(f"✅ Found latest scan for plant {plant_id}: {latest_scan.id}")
    
    return latest_scan


@router.get("/history/{plant_id}", response_model=List[schemas.PlantScan])
async def get_plant_scan_history(
    plant_id: str,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    """Get scan history for a specific plant"""
    print(f"🔍 Getting scan history for plant: {plant_id}")
    
    # Lookup user
    user = db.query(models.User).filter(
        models.User.cognito_user_id == user_info["cognito_user_id"]
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get plant to verify ownership
    plant = db.query(models.Plant).filter(
        models.Plant.id == plant_id,
        models.Plant.user_id == user.id
    ).first()
    
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant not found or not owned by user"
        )
    
    # Get plant scans for this plant
    plant_scans = db.query(models.PlantScan).filter(
        models.PlantScan.plant_id == plant_id,
        models.PlantScan.user_id == user.id
    ).order_by(models.PlantScan.scan_date.desc()).limit(10).all()
    
    print(f"✅ Found {len(plant_scans)} plant scans for plant {plant_id}")
    
    return plant_scans
