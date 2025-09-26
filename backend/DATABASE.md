# Database Management with Alembic

This directory contains Alembic migration files for managing database schema changes in PlantPal.

## Prerequisites

- PostgreSQL database running
- Environment variables configured (`.env` file)
- Python dependencies installed (`pip install -r requirements.txt`)

## Quick Start

### Using the Management Script (Recommended)

```bash
# Run all pending migrations
python manage_db.py migrate

# Show current database revision
python manage_db.py current

# Show migration history
python manage_db.py history

# Create a new migration after model changes
python manage_db.py create "Add new column to plants table"

# Rollback last migration (be careful!)
python manage_db.py rollback
```

### Direct Alembic Commands

```bash
# Run migrations
python -m alembic upgrade head

# Create new migration
python -m alembic revision --autogenerate -m "Migration message"

# Show current revision
python -m alembic current

# Show history
python -m alembic history
```

## Deployment

### Local Development
1. Make model changes in `app/models.py`
2. Create migration: `python manage_db.py create "Description of changes"`
3. Run migration: `python manage_db.py migrate`

### Production Deployment
Migrations run automatically during container startup via `start.sh`:
1. Container starts
2. `start.sh` runs `alembic upgrade head`
3. FastAPI server starts

## Migration Files

- **`alembic/versions/`**: Contains all migration files
- **`alembic.ini`**: Alembic configuration
- **`alembic/env.py`**: Runtime configuration and database connection

## Important Notes

⚠️ **Always backup your production database before running migrations**

✅ **Test migrations on a staging environment first**

🔄 **Commit migration files to version control**

## Troubleshooting

### "ImportError: cannot import name..."
Make sure you're running commands from the backend directory and all dependencies are installed.

### Migration conflicts
If you have migration conflicts, you may need to resolve them manually or create a merge migration.

### Database connection issues
Check your `.env` file and ensure `DATABASE_URL` is correctly configured.