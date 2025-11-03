from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user_info
from app.routers.achievements import calculate_user_streak

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
    current_streak = calculate_user_streak(user.id, db)
    coins_earned = 30 + (len(user_achievements) * 20) + (current_streak * 5)
    stats = schemas.DashboardStats(
        total_plants=total_plants,
        healthy_plants=healthy_plants,
        plants_needing_care=plants_needing_care,
        current_streak=current_streak,
        total_scans=0,  # TODO: track scan sessions
        achievements_earned=len(user_achievements),
        coins_earned=coins_earned
    )

    dashboard_plants = [
        schemas.DashboardPlant(
            id=plant.id,
            name=plant.name,
            species=plant.species,
            health_score=plant.current_health_score,
            streak_days=plant.streak_days,
            last_check_in=plant.last_check_in,
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

@router.get("/leaderboard", response_model=schemas.LeaderboardResponse)
def get_leaderboard(
    limit: int = 10,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    """Get leaderboard of top users ranked by achievement points"""
    try:
        # Get all users
        all_users = db.query(models.User).all()
        
        leaderboard_entries = []
        
        for user in all_users:
            # Get user's completed achievements
            completed_achievements = db.query(models.UserAchievement).filter(
                models.UserAchievement.user_id == user.id,
                models.UserAchievement.is_completed == True
            ).all()
            
            # Calculate total score from completed achievements
            total_score = 0
            for ua in completed_achievements:
                # Get the achievement to access points_awarded
                achievement = db.query(models.Achievement).filter(
                    models.Achievement.id == ua.achievement_id
                ).first()
                if achievement:
                    total_score += achievement.points_awarded
            
            # Add scan-based points: 5 per scan, +10 per healthy scan
            scans_count = db.query(models.PlantScan).filter(
                models.PlantScan.user_id == user.id
            ).count()
            healthy_scans_count = db.query(models.PlantScan).filter(
                models.PlantScan.user_id == user.id,
                models.PlantScan.is_healthy == True
            ).count()
            scan_points = (scans_count * 5) + (healthy_scans_count * 10)
            total_score += scan_points
            
            # Get user's total plants count
            plants_count = db.query(models.Plant).filter(
                models.Plant.user_id == user.id
            ).count()
            
            # Create leaderboard entry
            entry = schemas.LeaderboardEntry(
                rank=0,  # Will be set after sorting
                user_id=user.id,
                name=user.name,
                email=user.email,
                score=total_score,
                total_plants=plants_count,
                achievements_completed=len(completed_achievements)
            )
            
            leaderboard_entries.append(entry)
        
        # Sort by score (descending)
        leaderboard_entries.sort(key=lambda x: x.score, reverse=True)
        
        # Assign ranks with ties (same score -> same rank, next rank uses competition ranking)
        previous_score = None
        previous_rank = 0
        for idx, entry in enumerate(leaderboard_entries):
            if entry.score == previous_score:
                entry.rank = previous_rank
            else:
                entry.rank = idx + 1
                previous_score = entry.score
                previous_rank = entry.rank
        
        # Get current user's rank
        current_user = db.query(models.User).filter(
            models.User.cognito_user_id == user_info["cognito_user_id"]
        ).first()
        
        current_user_rank = None
        current_user_entry = None
        if current_user:
            for idx, entry in enumerate(leaderboard_entries):
                if entry.user_id == current_user.id:
                    current_user_rank = entry.rank
                    current_user_entry = entry
                    break
        
        # Limit results
        limited_entries = leaderboard_entries[:limit]

        # Ensure current user appears even if outside the top limit
        if current_user_entry and current_user_rank and current_user_rank > limit:
            limited_entries = limited_entries + [current_user_entry]
        
        return schemas.LeaderboardResponse(
            leaderboard=limited_entries,
            current_user_rank=current_user_rank
        )
        
    except Exception as e:
        print(f"❌ Error fetching leaderboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch leaderboard: {str(e)}"
        )
