"""
Achievement tracking router for PlantPal
Handles achievement progress tracking, unlocking, and retrieval
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func 
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user_info

router = APIRouter(prefix="/api/v1/achievements", tags=["achievements"])


# Helper Functions

def get_user_by_cognito_id(cognito_user_id: str, db: Session) -> models.User:
    """Get user by cognito_user_id, raise 404 if not found"""
    user = db.query(models.User).filter(
        models.User.cognito_user_id == cognito_user_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


def initialize_user_achievements(user_id: str, db: Session) -> None:
    """
    Initialize all active achievements for a new user.
    Called when user is created via auth.
    """
    try:
        # Get all active achievements
        achievements = db.query(models.Achievement).filter(
            models.Achievement.is_active == True
        ).all()
        
        if not achievements:
            print("⚠️ No active achievements to initialize")
            return
        
        # Create UserAchievement for each achievement
        for achievement in achievements:
            # Check if already exists (prevent duplicates)
            existing = db.query(models.UserAchievement).filter(
                models.UserAchievement.user_id == user_id,
                models.UserAchievement.achievement_id == achievement.id
            ).first()
            
            if not existing:
                user_achievement = models.UserAchievement(
                    user_id=user_id,
                    achievement_id=achievement.id,
                    current_progress=0,
                    is_completed=False
                )
                db.add(user_achievement)
        
        db.commit()
        print(f"✅ Initialized {len(achievements)} achievements for user {user_id}")
        
    except Exception as e:
        print(f"❌ Error initializing achievements: {str(e)}")
        db.rollback()


def calculate_user_streak(user_id: str, db: Session) -> int:
    """
    Calculate user's current streak based on consecutive days with scans.
    Returns number of consecutive days including today.
    """
    try:
        # Get all scans for user, ordered by date DESC
        scans = db.query(models.PlantScan).filter(
            models.PlantScan.user_id == user_id
        ).order_by(models.PlantScan.scan_date.desc()).all()
        
        if not scans:
            return 0
        
        # Start with today's date
        streak = 0
        current_date = datetime.utcnow().date()
        
        # Get unique dates with scans
        scan_dates = sorted(set(scan.scan_date.date() if hasattr(scan.scan_date, 'date') else scan.scan_date for scan in scans), reverse=True)
        
        if not scan_dates:
            return 0
        
        # Check if latest scan is today or yesterday (to allow for timezone differences)
        latest_scan_date = scan_dates[0]
        if (current_date - latest_scan_date).days > 1:
            return 0  # Streak broken
        
        # Count consecutive days
        for scan_date in scan_dates:
            if scan_date == current_date or (current_date - scan_date).days == streak:
                streak += 1
            else:
                break
        
        return streak
        
    except Exception as e:
        print(f"❌ Error calculating streak: {str(e)}")
        return 0


def update_achievement_progress(
    user_id: str,
    achievement_type: str,
    new_value: int,
    db: Session
) -> List[models.UserAchievement]:
    """
    Update achievement progress and check for completions.
    
    Args:
        user_id: User ID
        achievement_type: Type of achievement ("plants_count", "scans_count", "streak")
        new_value: New progress value
        db: Database session
        
    Returns:
        List of newly completed achievements
    """
    newly_completed = []
    
    try:
        # Get all achievements of this type that are not completed
        achievements = db.query(models.Achievement).filter(
            models.Achievement.achievement_type == achievement_type,
            models.Achievement.is_active == True
        ).all()

        if not achievements:
            print(f"⚠️ No achievements present")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Achievements not found"
            )

        for achievement in achievements:                
            # Get user's achievement progress
            user_achievement = db.query(models.UserAchievement).filter(
                models.UserAchievement.user_id == user_id,
                models.UserAchievement.achievement_id == achievement.id
            ).first()

            if not user_achievement:
                print(f"⚠️ {achievement.id}: \'{achievement.name}\' achievement not found for user {user_id}")
                continue
            
            # Skip if already completed
            if user_achievement.is_completed:
                print(f"⏭️ Skipping {achievement.name} (already completed)")
                continue
            
            # Update progress
            old_progress = user_achievement.current_progress
            user_achievement.current_progress = new_value
            
            # Check if achievement just completed
            if new_value >= achievement.requirement_value:
                user_achievement.is_completed = True
                user_achievement.completed_at = datetime.utcnow()
                newly_completed.append(user_achievement)
                
                print(f"🏆 Achievement Unlocked: {achievement.name} ({achievement.points_awarded} pts)")
        
        db.commit()
        return newly_completed
        
    except Exception as e:
        print(f"❌ Error updating achievement progress: {str(e)}")
        db.rollback()
        return []


# API Endpoints

@router.get("/", response_model=List[schemas.Achievement])
def get_all_achievements(db: Session = Depends(get_db)):
    """
    Get all active achievements in the system.
    No authentication required - public endpoint.
    """
    try:
        achievements = db.query(models.Achievement).filter(
            models.Achievement.is_active == True
        ).all()
        
        if not achievements:
            print(f"⚠️ No achievements present")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Achievements not found"
            )
        
        return achievements
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching achievements: {str(e)}"
        )


@router.get("/user", response_model=List[schemas.UserAchievement])
def get_user_achievements(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    """
    Get current user's achievement progress (all achievements, not just completed).
    Shows progress toward each achievement.
    """
    try:
        user = get_user_by_cognito_id(user_info["cognito_user_id"], db)
        
        # Get all user achievements with achievement details
        user_achievements = db.query(models.UserAchievement).filter(
            models.UserAchievement.user_id == user.id
        ).all()

        if not user_achievements:
            print(f"⚠️ No achievements found for user")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Achievements not found for user"
            )

        return user_achievements
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user achievements: {str(e)}"
        )


@router.get("/user/completed", response_model=List[schemas.UserAchievement])
def get_completed_achievements(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    """
    Get only completed achievements for the user.
    Used for dashboard display.
    """
    try:
        user = get_user_by_cognito_id(user_info["cognito_user_id"], db)
        
        user_achievements = db.query(models.UserAchievement).filter(
            models.UserAchievement.user_id == user.id,
            models.UserAchievement.is_completed == True
        ).order_by(models.UserAchievement.completed_at.desc()).all()
        
        return user_achievements
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching completed achievements: {str(e)}"
        )


@router.get("/user/stats")
def get_achievement_stats(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    """
    Get achievement statistics for the user.
    Returns: total, completed, in_progress, and total_points
    """
    try:
        user = get_user_by_cognito_id(user_info["cognito_user_id"], db)
        
        # Get all user achievements
        user_achievements = db.query(models.UserAchievement).filter(
            models.UserAchievement.user_id == user.id
        ).all()
        
        total = len(user_achievements)
        completed = len([ua for ua in user_achievements if ua.is_completed])
        in_progress = total - completed
        
        # Calculate total points earned
        total_points = 0
        for ua in user_achievements:
            if ua.is_completed and ua.achievement:
                total_points += ua.achievement.points_awarded
        
        return {
            "total_achievements": total,
            "completed": completed,
            "in_progress": in_progress,
            "total_points_earned": total_points,
            "completion_percentage": int((completed / total * 100) if total > 0 else 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching achievement stats: {str(e)}"
        )

@router.get("/user/streak")
def get_current_streak(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    try:
        user = get_user_by_cognito_id(user_info["cognito_user_id"], db)

        current_streak = calculate_user_streak(user.id, db)

        return {
            "current_streak": current_streak
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user's current streak: {str(e)}"
        )
    
@router.post("/user/check-streaks")
def check_and_update_streaks(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    """
    Check and update streak achievements for the user.
    Should be called periodically or when user logs in.
    """
    try:
        user = get_user_by_cognito_id(user_info["cognito_user_id"], db)
        
        # Calculate current streak
        current_streak = calculate_user_streak(user.id, db)
        
        # Update streak achievements
        newly_completed = update_achievement_progress(
            user.id,
            "streak",
            current_streak,
            db
        )
        
        return {
            "current_streak": current_streak,
            "newly_completed": len(newly_completed),
            "message": f"Streak updated to {current_streak} days"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking streaks: {str(e)}"
        )
