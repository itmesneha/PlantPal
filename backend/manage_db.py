#!/usr/bin/env python3
"""
Database Management Script for PlantPal
Usage:
    python manage_db.py migrate    # Run pending migrations
    python manage_db.py rollback   # Rollback last migration
    python manage_db.py current    # Show current revision
    python manage_db.py history    # Show migration history
"""

import sys
import subprocess
import os
from pathlib import Path

def run_alembic_command(command_args):
    """Run alembic command with proper error handling"""
    try:
        result = subprocess.run(
            ["python", "-m", "alembic"] + command_args,
            cwd=Path(__file__).parent,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print("Warnings:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running alembic command: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False

def migrate():
    """Run all pending migrations"""
    print("🔄 Running database migrations...")
    if run_alembic_command(["upgrade", "head"]):
        print("✅ Migrations completed successfully!")
    else:
        print("❌ Migration failed!")
        sys.exit(1)

def rollback():
    """Rollback the last migration"""
    print("⏪ Rolling back last migration...")
    if run_alembic_command(["downgrade", "-1"]):
        print("✅ Rollback completed successfully!")
    else:
        print("❌ Rollback failed!")
        sys.exit(1)

def current():
    """Show current database revision"""
    print("📊 Current database revision:")
    run_alembic_command(["current"])

def history():
    """Show migration history"""
    print("📜 Migration history:")
    run_alembic_command(["history"])

def create_migration():
    """Create a new migration"""
    if len(sys.argv) < 3:
        print("❌ Please provide a migration message")
        print("Usage: python manage_db.py create 'migration message'")
        sys.exit(1)
    
    message = sys.argv[2]
    print(f"📝 Creating new migration: {message}")
    if run_alembic_command(["revision", "--autogenerate", "-m", message]):
        print("✅ Migration created successfully!")
    else:
        print("❌ Failed to create migration!")
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "migrate":
        migrate()
    elif command == "rollback":
        rollback()
    elif command == "current":
        current()
    elif command == "history":
        history()
    elif command == "create":
        create_migration()
    else:
        print(f"❌ Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()