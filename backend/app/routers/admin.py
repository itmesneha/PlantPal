"""
Admin endpoints for database management and maintenance
WARNING: These endpoints should be protected and used with caution
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
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
