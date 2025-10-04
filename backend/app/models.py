from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    cognito_user_id = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    plants = relationship("Plant", back_populates="owner")
    scan_sessions = relationship("ScanSession", back_populates="user")
    achievements = relationship("UserAchievement", back_populates="user")

class Plant(Base):
    __tablename__ = "plants"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)  # User-given name like "My Monstera"
    species = Column(String, nullable=False)  # Scientific name
    common_name = Column(String)  # Common name like "Monstera Deliciosa"
    
    # Health tracking
    current_health_score = Column(Float, default=100.0)
    streak_days = Column(Integer, default=0)
    last_check_in = Column(DateTime(timezone=True))
    
    # Plant details
    image_url = Column(String)  # S3 URL for plant image
    care_notes = Column(Text)
    plant_icon = Column(String, default="🌱")  # User-selected emoji icon
    
    # Location and environment
    location = Column(String)  # Indoor/Outdoor, Room name, etc.
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="plants")
    scan_sessions = relationship("ScanSession", back_populates="plant")
    health_reports = relationship("HealthReport", back_populates="plant")

class ScanSession(Base):
    __tablename__ = "scan_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    plant_id = Column(String, ForeignKey("plants.id"), nullable=True)  # Null for new plant identification
    
    # Scan results
    original_image_url = Column(String, nullable=False)  # S3 URL
    identified_species = Column(String)
    confidence_score = Column(Float)
    
    # Health analysis
    is_healthy = Column(Boolean, default=True)
    disease_detected = Column(String)
    health_score = Column(Float)
    
    # AI/ML results
    ai_model_version = Column(String)
    processing_time_ms = Column(Integer)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="scan_sessions")
    plant = relationship("Plant", back_populates="scan_sessions")
    health_report = relationship("HealthReport", back_populates="scan_session", uselist=False)

class HealthReport(Base):
    __tablename__ = "health_reports"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_session_id = Column(String, ForeignKey("scan_sessions.id"), nullable=False)
    plant_id = Column(String, ForeignKey("plants.id"), nullable=False)
    
    # Health metrics
    overall_health_score = Column(Float, nullable=False)
    leaf_condition = Column(String)  # Healthy, Yellowing, Brown spots, etc.
    pest_issues = Column(JSON)  # Array of detected pest issues
    disease_indicators = Column(JSON)  # Array of disease indicators
    
    # Care recommendations from LLM
    care_recommendations = Column(JSON)  # Array of specific recommendations
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    scan_session = relationship("ScanSession", back_populates="health_report")
    plant = relationship("Plant", back_populates="health_reports")

class Achievement(Base):
    __tablename__ = "achievements"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    icon = Column(String)  # Emoji or icon identifier
    
    # Achievement criteria
    achievement_type = Column(String, nullable=False)  # streak, plants_count, scans_count, etc.
    requirement_value = Column(Integer, nullable=False)
    points_awarded = Column(Integer, default=10)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user_achievements = relationship("UserAchievement", back_populates="achievement")

class UserAchievement(Base):
    __tablename__ = "user_achievements"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(String, ForeignKey("achievements.id"), nullable=False)
    
    # Progress tracking
    current_progress = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")

class PlantCareLog(Base):
    __tablename__ = "plant_care_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    plant_id = Column(String, ForeignKey("plants.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Care activity
    activity_type = Column(String, nullable=False)  # watered, fertilized, pruned, repotted
    notes = Column(Text)
    image_url = Column(String)  # Optional photo of care activity
    
    # Scheduling
    scheduled_date = Column(DateTime(timezone=True))
    completed_date = Column(DateTime(timezone=True))
    is_completed = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships would be added here if needed

# Plant Species Database (for plant identification reference)
class PlantSpecies(Base):
    __tablename__ = "plant_species"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scientific_name = Column(String, nullable=False, unique=True, index=True)
    common_names = Column(JSON)  # Array of common names
    family = Column(String)
    
    # Care information
    care_difficulty = Column(String)  # Easy, Moderate, Difficult
    
    # Description and characteristics
    description = Column(Text)
    characteristics = Column(JSON)  # Key identifying features
    
    # Reference images
    reference_images = Column(JSON)  # Array of image URLs
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())