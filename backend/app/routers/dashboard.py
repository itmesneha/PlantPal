from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user_info

router = APIRouter(prefix="/api/v1", tags=["dashboard"])

@router.get("/dashboard", response_model=schemas.DashboardResponse)
def get_dashboard(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    """Get dashboard data for the user"""
    # Lookup user
    user = db.query(models.User).filter(
        models.User.cognito_user_id == user_info["cognito_user_id"]
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Get user's plants
    plants = db.query(models.Plant).filter(
        models.Plant.user_id == user.id
    ).all()

    # Calculate stats
    total_plants = len(plants)
    healthy_plants = len([p for p in plants if p.current_health_score >= 70])
    plants_needing_care = total_plants - healthy_plants

    # Get user achievements
    user_achievements = db.query(models.UserAchievement).filter(
        models.UserAchievement.user_id == user.id,
        models.UserAchievement.is_completed == True
    ).limit(5).all()

    # Build dashboard response
    stats = schemas.DashboardStats(
        total_plants=total_plants,
        healthy_plants=healthy_plants,
        plants_needing_care=plants_needing_care,
        current_streak=max([p.streak_days for p in plants], default=0),
        total_scans=0,  # TODO: track scan sessions
        achievements_earned=len(user_achievements)
    )

    dashboard_plants = [
        schemas.DashboardPlant(
            id=plant.id,
            name=plant.name,
            species=plant.species,
            health_score=plant.current_health_score,
            streak_days=plant.streak_days,
            last_check_in=plant.last_check_in,
            image_url=plant.image_url,
            needs_attention=plant.current_health_score < 70
        )
        for plant in plants[:5]
    ]

    return schemas.DashboardResponse(
        user=user,
        stats=stats,
        recent_plants=dashboard_plants,
        recent_achievements=user_achievements
    )