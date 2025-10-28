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
    plant_scans = relationship("PlantScan", back_populates="user")
    achievements = relationship("UserAchievement", back_populates="user")

class Plant(Base):
    __tablename__ = "plants"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)  # User-given name like "My Monstera"
    species = Column(String, nullable=False)  # Scientific name
    
    # Health tracking
    current_health_score = Column(Float, default=100.0)
    streak_days = Column(Integer, default=0)
    last_check_in = Column(DateTime(timezone=True))
    
    # Plant details
    plant_icon = Column(String, default="🌱")  # User-selected emoji icon
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="plants")
    plant_scans = relationship("PlantScan", back_populates="plant")

class PlantScan(Base):
    __tablename__ = "plant_scans"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    plant_id = Column(String, ForeignKey("plants.id"), nullable=True)  # Nullable for species identification scans
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Scan results
    scan_date = Column(DateTime(timezone=True), server_default=func.now())
    health_score = Column(Float, nullable=False)
    care_notes = Column(Text)
    
    # Health analysis
    disease_detected = Column(String)  # What disease was found (if any)
    is_healthy = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="plant_scans")
    plant = relationship("Plant", back_populates="plant_scans")

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

class PlantSpecies(Base):
    __tablename__ = "plant_species"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scientific_name = Column(String, unique=True, nullable=False)
    common_names = Column(JSON)
    family = Column(String)
    care_difficulty = Column(String)
    light_requirements = Column(String)
    water_frequency = Column(String)
    humidity_preference = Column(String)
    temperature_range = Column(String)
    description = Column(Text)
    characteristics = Column(JSON)
    reference_images = Column(JSON)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
