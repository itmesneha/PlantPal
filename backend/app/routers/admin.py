"""
Admin endpoints for database management and maintenance
WARNING: These endpoints should be protected and used with caution
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app import models
from app.auth import get_current_user_info

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post("/clear-database")
def clear_database(
    confirmation: str,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    """
    Clear all data from the database (DESTRUCTIVE OPERATION)
    Requires confirmation string "YES_DELETE_ALL_DATA"
    """
    if confirmation != "YES_DELETE_ALL_DATA":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid confirmation. Must send 'YES_DELETE_ALL_DATA'"
        )
    
    try:
        # Check which tables exist
        table_check_query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        result = db.execute(table_check_query)
        existing_tables = [row[0] for row in result]
        
        deleted_counts = {}
        
        # Clear data in order to respect foreign key constraints
        tables_to_clear = [
            'user_coupons',
            'user_achievements',
            'plant_scans',
            'achievements',
            'plants',
            'users'
        ]
        
        for table in tables_to_clear:
            if table in existing_tables:
                result = db.execute(text(f"DELETE FROM {table}"))
                deleted_counts[table] = result.rowcount
        
        db.commit()
        
        return {
            "success": True,
            "message": "Database cleared successfully",
            "deleted_counts": deleted_counts,
            "existing_tables": existing_tables
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear database: {str(e)}"
        )


@router.post("/drop-table")
def drop_table(
    table_name: str,
    confirmation: str,
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    """
    Drop a specific table from the database (DESTRUCTIVE OPERATION)
    Requires confirmation string "YES_DROP_TABLE"
    """
    if confirmation != "YES_DROP_TABLE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid confirmation. Must send 'YES_DROP_TABLE'"
        )
    
    # Whitelist of tables that can be dropped
    allowed_tables = ['plant_species']
    
    if table_name not in allowed_tables:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Table '{table_name}' is not in the allowed list for dropping"
        )
    
    try:
        # Check if table exists
        table_check_query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = :table_name
            )
        """)
        
        result = db.execute(table_check_query, {"table_name": table_name})
        table_exists = result.scalar()
        
        if not table_exists:
            return {
                "success": True,
                "message": f"Table '{table_name}' does not exist, nothing to drop",
                "table_existed": False
            }
        
        # Drop the table
        db.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
        db.commit()
        
        return {
            "success": True,
            "message": f"Table '{table_name}' dropped successfully",
            "table_existed": True
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to drop table: {str(e)}"
        )


@router.get("/list-tables")
def list_tables(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    """
    List all tables in the database
    """
    try:
        table_query = text("""
            SELECT table_name, 
                   (SELECT COUNT(*) FROM information_schema.columns 
                    WHERE table_name = t.table_name AND table_schema = 'public') as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        result = db.execute(table_query)
        tables = [{"name": row[0], "column_count": row[1]} for row in result]
        
        # Get row counts for each table
        for table in tables:
            count_query = text(f"SELECT COUNT(*) FROM {table['name']}")
            result = db.execute(count_query)
            table['row_count'] = result.scalar()
        
        return {
            "success": True,
            "tables": tables,
            "total_tables": len(tables)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tables: {str(e)}"
        )


@router.post("/seed-achievements")
def seed_achievements(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    """
    Seed the database with default achievements
    """
    try:
        # Check if achievements already exist
        existing_count = db.query(models.Achievement).count()
        
        if existing_count > 0:
            return {
                "success": True,
                "message": f"Achievements already exist ({existing_count} found)",
                "seeded": False,
                "existing_count": existing_count
            }
        
        # Define default achievements
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
        
        # Create achievements
        for achievement_data in default_achievements:
            achievement = models.Achievement(**achievement_data)
            db.add(achievement)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Successfully seeded {len(default_achievements)} achievements",
            "seeded": True,
            "count": len(default_achievements)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to seed achievements: {str(e)}"
        )


@router.post("/initialize-user-achievements")
def initialize_user_achievements_endpoint(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    """
    Initialize achievements for the current user (or all users)
    Useful after seeding achievements for existing users
    """
    from app.routers.achievements import initialize_user_achievements
    
    try:
        # Get current user
        user = db.query(models.User).filter(
            models.User.cognito_user_id == user_info["cognito_user_id"]
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check how many achievements exist
        achievement_count = db.query(models.Achievement).filter(
            models.Achievement.is_active == True
        ).count()
        
        if achievement_count == 0:
            return {
                "success": False,
                "message": "No achievements found in database. Run seed-achievements first.",
                "achievement_count": 0
            }
        
        # Check if user already has achievements initialized
        existing_user_achievements = db.query(models.UserAchievement).filter(
            models.UserAchievement.user_id == user.id
        ).count()
        
        if existing_user_achievements > 0:
            return {
                "success": True,
                "message": f"User already has {existing_user_achievements} achievements initialized",
                "already_initialized": True,
                "user_achievement_count": existing_user_achievements
            }
        
        # Initialize achievements for user
        initialize_user_achievements(user.id, db)
        
        # Get count after initialization
        new_count = db.query(models.UserAchievement).filter(
            models.UserAchievement.user_id == user.id
        ).count()
        
        return {
            "success": True,
            "message": f"Successfully initialized {new_count} achievements for user",
            "initialized": True,
            "user_achievement_count": new_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize user achievements: {str(e)}"
        )


@router.post("/delete-test-users")
def delete_test_users(
    user_info: dict = Depends(get_current_user_info),
    db: Session = Depends(get_db)
):
    """
    Delete all users that have 'User' in their name
    Useful for cleaning up test accounts
    """
    try:
        # Find users with 'User' in their name
        users_to_delete = db.query(models.User).filter(
            models.User.name.ilike('%User%')
        ).all()
        
        if not users_to_delete:
            return {
                "success": True,
                "message": "No users with 'User' in their name found",
                "deleted_count": 0
            }
        
        deleted_count = 0
        deleted_names = []
        
        for user in users_to_delete:
            deleted_names.append(user.name)
            
            # Delete related data first (to respect foreign key constraints)
            # Delete user coupons
            db.query(models.UserCoupon).filter(
                models.UserCoupon.user_id == user.id
            ).delete()
            
            # Delete user achievements
            db.query(models.UserAchievement).filter(
                models.UserAchievement.user_id == user.id
            ).delete()
            
            # Delete plant scans
            db.query(models.PlantScan).filter(
                models.PlantScan.user_id == user.id
            ).delete()
            
            # Delete plants
            db.query(models.Plant).filter(
                models.Plant.user_id == user.id
            ).delete()
            
            # Finally, delete the user
            db.delete(user)
            deleted_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Successfully deleted {deleted_count} test users",
            "deleted_count": deleted_count,
            "deleted_users": deleted_names
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete test users: {str(e)}"
        )
