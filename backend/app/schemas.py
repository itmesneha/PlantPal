from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

# Base schemas
class UserBase(BaseModel):
    email: str
    name: str

class UserCreate(UserBase):
    cognito_user_id: str

class UserUpdate(BaseModel):
    name: Optional[str] = None

class User(UserBase):
    id: str
    cognito_user_id: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Plant schemas
class PlantBase(BaseModel):
    name: str
    species: str
    common_name: Optional[str] = None
    location: Optional[str] = None
    care_notes: Optional[str] = None

class PlantCreate(PlantBase):
    pass

class AddToGardenRequest(BaseModel):
    plant_name: str  # User's custom name for the plant
    species: str  # From scan result
    common_name: Optional[str] = None  # From scan result
    location: Optional[str] = None  # Where they keep the plant
    care_notes: Optional[str] = None  # Initial notes
    health_score: Optional[float] = 100.0  # From scan result
    image_data: Optional[str] = None  # Base64 encoded image (optional)
    plant_icon: Optional[str] = None  # User-selected emoji icon

class PlantUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    care_notes: Optional[str] = None
    current_health_score: Optional[float] = None

class Plant(PlantBase):
    id: str
    user_id: str
    current_health_score: float
    streak_days: int
    last_check_in: Optional[datetime]
    image_url: Optional[str]
    plant_icon: Optional[str] = "🌱"
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class AddToGardenResponse(BaseModel):
    success: bool
    plant_id: str
    message: str
    plant: Plant

class DeletePlantResponse(BaseModel):
    success: bool
    message: str
    deleted_plant_id: str

# Scan Session schemas
class ScanSessionCreate(BaseModel):
    original_image_url: str
    plant_id: Optional[str] = None

class ScanResult(BaseModel):
    species: str
    confidence: float
    is_healthy: bool
    disease: Optional[str] = None
    health_score: float
    care_recommendations: List[str]

class ScanSession(BaseModel):
    id: str
    user_id: str
    plant_id: Optional[str]
    original_image_url: str
    identified_species: Optional[str]
    confidence_score: Optional[float]
    is_healthy: bool
    disease_detected: Optional[str]
    health_score: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Health Report schemas
class HealthReportCreate(BaseModel):
    scan_session_id: str
    plant_id: str
    overall_health_score: float
    leaf_condition: Optional[str] = None
    pest_issues: Optional[List[Dict[str, Any]]] = []
    disease_indicators: Optional[List[Dict[str, Any]]] = []
    care_recommendations: Optional[List[str]] = []
    
    # Care recommendations
    watering_recommendation: Optional[str] = None
    light_recommendation: Optional[str] = None
    humidity_recommendation: Optional[str] = None
    fertilizer_recommendation: Optional[str] = None

class HealthReport(BaseModel):
    id: str
    scan_session_id: str
    plant_id: str
    overall_health_score: float
    leaf_condition: Optional[str]
    pest_issues: Optional[List[Dict[str, Any]]]
    disease_indicators: Optional[List[Dict[str, Any]]]
    care_recommendations: Optional[List[str]]
    watering_recommendation: Optional[str]
    light_recommendation: Optional[str]
    humidity_recommendation: Optional[str]
    fertilizer_recommendation: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Achievement schemas
class AchievementBase(BaseModel):
    name: str
    description: str
    icon: Optional[str] = None
    achievement_type: str
    requirement_value: int
    points_awarded: int = 10

class AchievementCreate(AchievementBase):
    pass

class Achievement(AchievementBase):
    id: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserAchievementCreate(BaseModel):
    achievement_id: str
    current_progress: int = 0

class UserAchievement(BaseModel):
    id: str
    user_id: str
    achievement_id: str
    current_progress: int
    is_completed: bool
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    achievement: Achievement
    
    class Config:
        from_attributes = True

# Plant Species schemas
class PlantSpeciesBase(BaseModel):
    scientific_name: str
    common_names: Optional[List[str]] = []
    family: Optional[str] = None
    care_difficulty: Optional[str] = None
    light_requirements: Optional[str] = None
    water_frequency: Optional[str] = None
    description: Optional[str] = None

class PlantSpeciesCreate(PlantSpeciesBase):
    pass

class PlantSpecies(PlantSpeciesBase):
    id: str
    characteristics: Optional[Dict[str, Any]]
    reference_images: Optional[List[str]]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Care Log schemas
class PlantCareLogCreate(BaseModel):
    plant_id: str
    activity_type: str
    notes: Optional[str] = None
    scheduled_date: Optional[datetime] = None

class PlantCareLog(BaseModel):
    id: str
    plant_id: str
    user_id: str
    activity_type: str
    notes: Optional[str]
    scheduled_date: Optional[datetime]
    completed_date: Optional[datetime]
    is_completed: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Dashboard response schemas
class DashboardStats(BaseModel):
    total_plants: int
    healthy_plants: int
    plants_needing_care: int
    current_streak: int
    total_scans: int
    achievements_earned: int

class DashboardPlant(BaseModel):
    id: str
    name: str
    species: str
    health_score: float
    streak_days: int
    last_check_in: Optional[datetime]
    image_url: Optional[str]
    needs_attention: bool

class DashboardResponse(BaseModel):
    user: User
    stats: DashboardStats
    recent_plants: List[DashboardPlant]
    recent_achievements: List[UserAchievement]

# API Response schemas
class PlantIdentificationRequest(BaseModel):
    image_base64: Optional[str] = None
    image_url: Optional[str] = None
    
    @validator('image_base64', 'image_url')
    def validate_image_input(cls, v, values):
        if not values.get('image_base64') and not values.get('image_url'):
            raise ValueError('Either image_base64 or image_url must be provided')
        return v

class PlantIdentificationResponse(BaseModel):
    species: str
    common_name: str
    confidence: float
    care_difficulty: str
    care_recommendations: List[str]

# Error response schema
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None