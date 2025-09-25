"""
Database initialization script for PlantPal
Run this script to create all tables and seed initial data
"""

from sqlalchemy import create_engine
from app.database import Base, DATABASE_URL
from app.models import *  # Import all models
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_tables():
    """Create all database tables"""
    engine = create_engine(DATABASE_URL)
    
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully!")

def seed_achievements():
    """Seed the database with default achievements"""
    from app.database import SessionLocal
    
    db = SessionLocal()
    
    # Check if achievements already exist
    existing_achievements = db.query(Achievement).count()
    if existing_achievements > 0:
        print("⚠️ Achievements already exist, skipping seed...")
        db.close()
        return
    
    default_achievements = [
        {
            "name": "First Scan",
            "description": "Complete your first plant scan",
            "icon": "🌱",
            "achievement_type": "scans_count",
            "requirement_value": 1,
            "points_awarded": 10
        },
        {
            "name": "Green Thumb",
            "description": "Add your first plant to the garden",
            "icon": "👍",
            "achievement_type": "plants_count",
            "requirement_value": 1,
            "points_awarded": 10
        },
        {
            "name": "Plant Parent",
            "description": "Maintain a 7-day care streak",
            "icon": "🌿",
            "achievement_type": "streak",
            "requirement_value": 7,
            "points_awarded": 25
        },
        {
            "name": "Green Garden",
            "description": "Collect 5 plants in your garden",
            "icon": "🌳",
            "achievement_type": "plants_count",
            "requirement_value": 5,
            "points_awarded": 50
        },
        {
            "name": "Plant Expert",
            "description": "Maintain a 30-day care streak",
            "icon": "🌺",
            "achievement_type": "streak",
            "requirement_value": 30,
            "points_awarded": 100
        },
        {
            "name": "Scanner Pro",
            "description": "Complete 25 plant scans",
            "icon": "📱",
            "achievement_type": "scans_count",
            "requirement_value": 25,
            "points_awarded": 75
        },
        {
            "name": "Jungle Master",
            "description": "Collect 15 plants in your garden",
            "icon": "🌴",
            "achievement_type": "plants_count",
            "requirement_value": 15,
            "points_awarded": 150
        },
        {
            "name": "Plant Whisperer",
            "description": "Maintain a 100-day care streak",
            "icon": "🏆",
            "achievement_type": "streak",
            "requirement_value": 100,
            "points_awarded": 500
        }
    ]
    
    print("Seeding achievements...")
    for achievement_data in default_achievements:
        achievement = Achievement(**achievement_data)
        db.add(achievement)
    
    db.commit()
    print(f"✅ Seeded {len(default_achievements)} achievements!")
    db.close()

def seed_plant_species():
    """Seed the database with common plant species"""
    from app.database import SessionLocal
    
    db = SessionLocal()
    
    # Check if plant species already exist
    existing_species = db.query(PlantSpecies).count()
    if existing_species > 0:
        print("⚠️ Plant species already exist, skipping seed...")
        db.close()
        return
    
    common_plants = [
        {
            "scientific_name": "Monstera deliciosa",
            "common_names": ["Monstera", "Swiss Cheese Plant", "Split-leaf Philodendron"],
            "family": "Araceae",
            "care_difficulty": "Easy",
            "description": "Popular houseplant with large, glossy leaves that develop characteristic splits and holes as they mature."
        },
        {
            "scientific_name": "Sansevieria trifasciata",
            "common_names": ["Snake Plant", "Mother-in-Law's Tongue", "Viper's Bowstring Hemp"],
            "family": "Asparagaceae",
            "care_difficulty": "Easy",
            "description": "Extremely hardy plant with upright, sword-like leaves with yellow edges. Perfect for beginners."
        },
        {
            "scientific_name": "Epipremnum aureum",
            "common_names": ["Golden Pothos", "Devil's Ivy", "Money Plant"],
            "family": "Araceae",
            "care_difficulty": "Easy",
            "description": "Trailing vine with heart-shaped leaves, often variegated with yellow. Very forgiving and fast-growing."
        },
        {
            "scientific_name": "Ficus lyrata",
            "common_names": ["Fiddle Leaf Fig", "Banjo Fig"],
            "family": "Moraceae",
            "care_difficulty": "Moderate",
            "description": "Statement plant with large, violin-shaped leaves. Requires consistent care and stable conditions."
        },
        {
            "scientific_name": "Spathiphyllum wallisii",
            "common_names": ["Peace Lily", "Spath"],
            "family": "Araceae",
            "care_difficulty": "Easy",
            "description": "Elegant plant with dark green leaves and white flower spathes. Great air purifier."
        }
    ]
    
    print("Seeding plant species...")
    for plant_data in common_plants:
        plant_species = PlantSpecies(**plant_data)
        db.add(plant_species)
    
    db.commit()
    print(f"✅ Seeded {len(common_plants)} plant species!")
    db.close()

if __name__ == "__main__":
    print("🌱 Initializing PlantPal Database...")
    
    # Create tables
    create_tables()
    
    # Seed initial data
    seed_achievements()
    seed_plant_species()
    
    print("✅ Database initialization complete!")
    print("\nNext steps:")
    print("1. Start the FastAPI server: uvicorn app.main:app --reload")
    print("2. Test your API at: http://localhost:8000/docs")