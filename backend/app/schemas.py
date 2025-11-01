from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

# Base schemas
class UserBase(BaseModel):
    email: EmailStr
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

class PlantCreate(PlantBase):
    pass

class AddToGardenRequest(BaseModel):
    plant_name: str  # User's custom name for the plant
    species: str  # From scan result
    health_score: Optional[float] = 100.0  # From scan result
    plant_icon: Optional[str] = None  # User-selected emoji icon
    
    # Scan data (optional - from recent scan results)
    disease_detected: Optional[str] = None
    is_healthy: Optional[bool] = True
    care_notes: Optional[str] = None

class PlantUpdate(BaseModel):
    name: Optional[str] = None
    current_health_score: Optional[float] = None

class Plant(PlantBase):
    id: str
    user_id: str
    current_health_score: float
    streak_days: int
    last_check_in: Optional[datetime]
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

# Plant Scan schemas (replaces ScanSession and HealthReport)
class PlantScanCreate(BaseModel):
    plant_id: str
    health_score: float
    care_notes: Optional[str] = None
    disease_detected: Optional[str] = None
    is_healthy: bool = True

class PlantScan(BaseModel):
    id: str
    plant_id: Optional[str]
    user_id: str
    scan_date: datetime
    health_score: float
    care_notes: Optional[str]
    disease_detected: Optional[str]
    is_healthy: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class ScanResult(BaseModel):
    species: str
    confidence: float
    is_healthy: bool
    disease: Optional[str] = None
    health_score: float
    care_recommendations: List[str]
    
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
    coins_earned: int

class DashboardPlant(BaseModel):
    id: str
    name: str
    species: str
    health_score: float
    streak_days: int
    last_check_in: Optional[datetime]
    needs_attention: bool

class DashboardResponse(BaseModel):
    user: User
    stats: DashboardStats
    recent_plants: List[DashboardPlant]
    recent_achievements: List[UserAchievement]

# Leaderboard schemas
class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    name: str
    email: str
    score: int
    total_plants: int
    achievements_completed: int
    
    class Config:
        from_attributes = True

class LeaderboardResponse(BaseModel):
    leaderboard: List[LeaderboardEntry]
    current_user_rank: Optional[int] = None

# Storefront schemas
class CoinBalance(BaseModel):
    coins_earned: int
    coins_spent: int
    coins_remaining: int

class Coupon(BaseModel):
    id: str
    store_id: str
    store_name: str
    discount_percent: int
    cost_coins: int
    code: str
    redeemed: bool
    expires_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class PurchaseCouponRequest(BaseModel):
    store_id: str
    store_name: str
    discount_percent: int  # 10, 20, 35
    cost_coins: int        # 50, 100, 200

class PurchaseCouponResponse(BaseModel):
    success: bool
    message: str
    coupon: Optional[Coupon]

# API Response schemas
class PlantIdentificationRequest(BaseModel):
    image_base64: Optional[str] = None
    image_url: Optional[str] = None
    
    @validator('image_base64', 'image_url')
    def validate_image_input(cls, v, values):
        # This validator runs after image_base64, so we can check both fields
        if not values.get('image_base64') and not v:
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