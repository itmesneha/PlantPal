#!/usr/bin/env python3
"""
Clear all data from PlantPal database while preserving schema.
This script safely removes all user data, plants, and scans using raw SQL.
"""

import os
import sys
from sqlalchemy import create_engine, text

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import DATABASE_URL

def clear_database():
    """Clear all data from the database using raw SQL"""
    print("🗑️ Clearing PlantPal database...")
    print(f"🔗 Using database: {DATABASE_URL}")
    
    try:
        # Create engine and connect
        engine = create_engine(DATABASE_URL)
        
        with engine.begin() as conn:  # Use begin() to auto-handle transaction
            # First, check which tables exist
            print("🔍 Checking which tables exist...")
            
            table_check_query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            
            existing_tables = []
            result = conn.execute(table_check_query)
            for row in result:
                existing_tables.append(row[0])
            
            print(f"📋 Found tables: {existing_tables}")
            
            deleted_counts = {}
            
            # Clear data in order to respect foreign key constraints
            # Based on the tables found, let's clear the relevant ones
            
            # Clear dependent tables first
            tables_to_clear = [
                'user_achievements',
                'health_reports', 
                'plant_care_logs',
                'scan_sessions',
                'achievements',
                'plants',
                'users',
                'plant_species'
            ]
            
            for table in tables_to_clear:
                if table in existing_tables:
                    print(f"🗑️ Deleting from {table}...")
                    result = conn.execute(text(f"DELETE FROM {table}"))
                    deleted_counts[table] = result.rowcount
                    print(f"   ✓ Deleted {result.rowcount} rows from {table}")
                else:
                    print(f"ℹ️ {table} table doesn't exist, skipping...")
                    deleted_counts[table] = 0
            
            print(f"\n✅ Database cleared successfully!")
            print("📊 Summary:")
            for table, count in deleted_counts.items():
                if count > 0:
                    print(f"   - Deleted {count} rows from {table}")
            
            # Verify tables are empty
            print("\n🔍 Verifying tables are empty...")
            verification_counts = {}
            
            for table in tables_to_clear:
                if table in existing_tables:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    verification_counts[table] = count
                    if count > 0:
                        print(f"   ⚠️ {table}: {count} rows remaining")
                    else:
                        print(f"   ✅ {table}: empty")
            
            remaining_total = sum(verification_counts.values())
            if remaining_total == 0:
                print("\n✅ All tables are now empty!")
                return True
            else:
                print(f"\n⚠️ {remaining_total} total rows still remain across tables")
                return False
                
    except Exception as e:
        print(f"❌ Error clearing database: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚨 WARNING: This will delete ALL data from your PlantPal database!")
    print("This includes all users, plants, and scan history.")
    print("\nAre you sure you want to continue? (yes/no): ", end="")
    
    confirmation = input().lower().strip()
    if confirmation in ['yes', 'y']:
        success = clear_database()
        if success:
            print("\n🎉 Database cleared successfully!")
        else:
            print("\n❌ Failed to clear database")
            sys.exit(1)
    else:
        print("❌ Operation cancelled")
        sys.exit(0)