#!/usr/bin/env python3
"""
Manage PlantPal database via admin API endpoints
This script calls the API running on EC2 which has access to RDS
"""

import requests
import sys
import os

# API Configuration
API_URL = "http://54.251.32.63:8000"

# You'll need to get a JWT token from your authenticated frontend session
# Look in browser dev tools > Application > Local Storage or Session Storage
# Or intercept the Authorization header from any authenticated API call
AUTH_TOKEN = os.getenv("PLANTPAL_AUTH_TOKEN", "")

if not AUTH_TOKEN:
    print("❌ Error: PLANTPAL_AUTH_TOKEN environment variable not set")
    print("\nTo get your auth token:")
    print("1. Log into PlantPal frontend")
    print("2. Open browser DevTools (F12)")
    print("3. Go to Network tab")
    print("4. Make any API request (scan a plant, view dashboard, etc.)")
    print("5. Look for 'Authorization: Bearer <token>' in request headers")
    print("6. Copy the token and run:")
    print("   export PLANTPAL_AUTH_TOKEN='your_token_here'")
    print("   python manage_db_api.py <command>")
    sys.exit(1)

headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}

def list_tables():
    """List all database tables and their row counts"""
    print("📋 Fetching database tables...")
    try:
        response = requests.get(f"{API_URL}/api/v1/admin/list-tables", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Found {data['total_tables']} tables:\n")
            for table in data['tables']:
                print(f"   📊 {table['name']:<25} {table['row_count']:>6} rows  ({table['column_count']} columns)")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.json())
    except Exception as e:
        print(f"❌ Request failed: {e}")

def clear_database():
    """Clear all data from the database"""
    print("\n🚨 WARNING: This will delete ALL data from your PlantPal database!")
    print("This includes all users, plants, and scan history.\n")
    
    confirmation = input("Type 'YES_DELETE_ALL_DATA' to confirm: ")
    
    if confirmation != "YES_DELETE_ALL_DATA":
        print("❌ Operation cancelled")
        return
    
    print("\n🗑️  Clearing database...")
    try:
        response = requests.post(
            f"{API_URL}/api/v1/admin/clear-database",
            headers=headers,
            params={"confirmation": "YES_DELETE_ALL_DATA"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Database cleared successfully!\n")
            print("📊 Deleted rows:")
            for table, count in data['deleted_counts'].items():
                if count > 0:
                    print(f"   - {table}: {count} rows")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.json())
    except Exception as e:
        print(f"❌ Request failed: {e}")

def drop_plant_species():
    """Drop the plant_species table"""
    print("\n🚨 WARNING: This will drop the plant_species table!")
    print("This action cannot be undone.\n")
    
    confirmation = input("Type 'YES_DROP_TABLE' to confirm: ")
    
    if confirmation != "YES_DROP_TABLE":
        print("❌ Operation cancelled")
        return
    
    print("\n🗑️  Dropping plant_species table...")
    try:
        response = requests.post(
            f"{API_URL}/api/v1/admin/drop-table",
            headers=headers,
            params={
                "table_name": "plant_species",
                "confirmation": "YES_DROP_TABLE"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ {data['message']}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.json())
    except Exception as e:
        print(f"❌ Request failed: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python manage_db_api.py <command>")
        print("\nCommands:")
        print("  list          - List all tables and their row counts")
        print("  clear         - Clear all data from database (requires confirmation)")
        print("  drop-species  - Drop the plant_species table (requires confirmation)")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_tables()
    elif command == "clear":
        clear_database()
    elif command == "drop-species":
        drop_plant_species()
    else:
        print(f"❌ Unknown command: {command}")
        print("Valid commands: list, clear, drop-species")
        sys.exit(1)

if __name__ == "__main__":
    main()
