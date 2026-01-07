# PlantPal Backend - Code Explanation

## Overview
PlantPal backend is a FastAPI application that provides plant identification, health tracking, achievement systems, and gamification features. Built with PostgreSQL database on AWS RDS and uses external AI APIs for plant analysis.

---

## Architecture & Tech Stack

**Core Technologies:**
- FastAPI (Python async web framework)
- SQLAlchemy ORM (database operations)
- PostgreSQL (AWS RDS database)
- AWS Cognito (JWT authentication)
- Alembic (database migrations)

**External APIs:**
- Plant.Net API - Plant species identification
- HuggingFace - Disease detection model
- OpenRouter API - AI care recommendations (Google Gemma model)

**Deployment:**
- Docker containerization
- AWS ECS on EC2 (t2.micro)
- AWS ECR (Docker image registry)

---

## Database Schema

### Core Models (`models.py`)

**1. User**
```python
users:
  - id (UUID primary key)
  - cognito_user_id (unique, indexed)
  - email (unique, indexed)
  - name
  - created_at, updated_at
```
**Purpose:** Stores user profile synced from AWS Cognito.

**2. Plant**
```python
plants:
  - id (UUID)
  - user_id (FK → users)
  - name (user-given name)
  - species (scientific name)
  - current_health_score (0-100)
  - streak_days (consecutive check-ins)
  - last_check_in (timestamp)
  - plant_icon (emoji/icon string)
```
**Purpose:** User's plant collection with health tracking.

**3. PlantScan**
```python
plant_scans:
  - id (UUID)
  - plant_id (FK → plants, nullable)
  - user_id (FK → users)
  - scan_date (timestamp)
  - health_score (0-100)
  - care_notes (text)
  - disease_detected (string, nullable)
  - is_healthy (boolean)
```
**Purpose:** History of plant health scans. `plant_id` is nullable to support initial species identification scans.

**4. Achievement**
```python
achievements:
  - id (UUID)
  - name, description, icon
  - achievement_type (streak/plants_count/scans_count)
  - requirement_value (target to unlock)
  - points_awarded (score for leaderboard)
  - is_active (boolean)
```
**Purpose:** Master list of unlockable achievements (seeded via admin).

**5. UserAchievement**
```python
user_achievements:
  - id (UUID)
  - user_id (FK → users)
  - achievement_id (FK → achievements)
  - current_progress (integer)
  - is_completed (boolean)
  - completed_at (timestamp, nullable)
```
**Purpose:** Tracks individual user progress toward each achievement.

**6. UserCoupon**
```python
user_coupons:
  - id (UUID)
  - user_id (FK → users)
  - store_id, store_name
  - discount_percent (5/10/20)
  - cost_coins (50/100/150)
  - code (unique coupon code)
  - redeemed (boolean)
  - expires_at (timestamp)
```
**Purpose:** Purchased discount coupons using earned coins.

---

## API Router Structure

### 1. Authentication (`auth.py`)

**Purpose:** JWT token validation and user extraction.

**Key Functions:**
- `get_cognito_public_keys()`: Fetches JWKS from Cognito
- `verify_cognito_token(token)`: Validates JWT signature and extracts claims
- `get_current_user_info()`: FastAPI dependency for protected routes

**Flow:**
```python
Request with Authorization: Bearer <token>
  ↓
extract_token_from_header()
  ↓
verify_cognito_token() → Validates against Cognito public keys
  ↓
Returns: {cognito_user_id, email, name}
```

**Security:**
- RS256 algorithm validation
- Issuer verification (Cognito URL)
- Token expiration checks
- Public key caching with `@lru_cache()`

---

### 2. User Router (`users.py`)

**Endpoints:**

**GET /api/v1/users/me**
- Returns current user profile
- Auto-creates user if doesn't exist (JWT → Database sync)
- Initializes achievements for new users

**POST /api/v1/users/**
- Manual user creation (legacy, mostly unused)
- Called after Cognito signup

**POST /api/v1/users/test**
- Creates test user for development
- Email: `testuser@plantpal.com`

**Key Logic:**
```python
get_current_user():
  user = query by cognito_user_id
  if not user:
    user = create from JWT claims
    initialize_user_achievements(user.id)
  return user
```

---

### 3. Scan Router (`scan.py`) - Most Complex

**Main Endpoint: POST /api/v1/scan**

**Purpose:** Plant identification + disease detection + care recommendations.

**Workflow:**
```
1. Receive image upload (multipart/form-data)
2. Optional plant_id (for rescanning existing plant)
3. Image preprocessing:
   - Validate size/format
   - Compress if >1MB using PIL
   - Convert to base64 for API calls
4. Parallel API calls:
   - Plant.Net API (species identification)
   - HuggingFace Model (disease detection)
5. Parse responses
6. Generate AI care recommendations (OpenRouter)
7. Create PlantScan record
8. If rescan: update Plant health score
9. Update achievements (scans_count, streak)
10. Return ScanResult to frontend
```

**Key Functions:**

**`query_plantnet_api_async()`**
```python
POST https://my-api.plantnet.org/v2/identify/all
Headers: API-Key
Body: {images: [base64], organs: ["leaf"]}
Returns: List of species matches with confidence scores
```

**`query_huggingface_model_async()`**
```python
POST https://api-inference.huggingface.co/models/...
Headers: Authorization
Body: base64 image
Returns: Disease predictions with confidence
Handles: Model loading delays (503 retry logic)
```

**`get_care_recommendations()`**
```python
POST https://openrouter.ai/api/v1/chat/completions
Model: google/gemma-3-27b-it:free
Prompt: "Give me 4 sentences short actionable care 
         instructions for {species} with {disease}"
Returns: Parsed list of care tips (cleans markdown, numbering)
```

**Disease Detection Logic:**
```python
parse_disease_predictions():
  - Filters predictions > 20% confidence
  - Excludes "healthy" class
  - Returns highest confidence disease or None
  - Calculates health_score: 100 - (disease_confidence * 100)
```

**Image Compression:**
```python
compress_image():
  if size > 1MB:
    - Open with PIL
    - Resize maintaining aspect ratio (max 1024x1024)
    - Save as JPEG with quality=85
    - Convert to base64
```

---

### 4. Plants Router (`plants.py`)

**GET /api/v1/plants**
- Lists all plants for authenticated user
- Supports pagination (skip/limit)

**POST /api/v1/plants/add-to-garden**
- Creates new Plant entry
- Associates initial PlantScan if scan data provided
- Updates `plants_count` achievement
- Returns plant ID for frontend

**Request Schema:**
```python
AddToGardenRequest:
  - plant_name (user's custom name)
  - species (from scan)
  - health_score (from scan)
  - plant_icon (emoji)
  - disease_detected (optional)
  - care_notes (optional)
```

**Achievement Update:**
```python
total_plants = count user's plants
update_achievement_progress(user_id, "plants_count", total_plants)
→ Unlocks achievements at 1, 3, 5, 10 plants
```

---

### 5. Garden Router (in `plants.py`)

**PUT /api/v1/garden/{plant_id}**
- Updates plant name or health score
- Editable fields: `name`, `current_health_score`

**DELETE /api/v1/garden/{plant_id}**
- Removes plant from user's garden
- Cascades delete to plant_scans (FK constraint)

**GET /api/v1/garden**
- Returns plants formatted for dashboard
- Includes health score, streak, last check-in

---

### 6. Achievements Router (`achievements.py`)

**GET /api/v1/achievements**
- Returns all achievements with user's progress
- Shows completed and in-progress

**GET /api/v1/achievements/stats**
- Summary: total, completed, in-progress counts

**POST /api/v1/achievements/check-streaks**
- Recalculates user's streak
- Updates streak-based achievements

**Helper Functions:**

**`calculate_user_streak(user_id, db)`**
```python
Algorithm:
1. Get all user's scans ordered by date DESC
2. Extract unique scan dates
3. Start from today, count backwards
4. Break if date gap > 1 day
5. Return consecutive day count
```

**`update_achievement_progress(user_id, type, value, db)`**
```python
Parameters:
  - type: "streak", "plants_count", "scans_count", etc.
  - value: Current user's value (e.g., 5 plants)

Logic:
1. Query all achievements of given type
2. For each matching UserAchievement:
   - Update current_progress = value
   - If value >= requirement_value:
     - Mark is_completed = True
     - Set completed_at = now
3. Return list of newly completed achievements
```

**Achievement Types:**
- `streak_3`, `streak_7`, `streak_30` - Consecutive scan days
- `plants_count_1`, `plants_count_5`, `plants_count_10` - Total plants
- `scans_count_10`, `scans_count_50` - Total scans performed
- `healthy_plants_3`, `healthy_plants_10` - Plants with health ≥80

---

### 7. Storefront Router (`storefront.py`)

**GET /api/v1/storefront/balance**
- Calculates coin balance

**Formula:**
```python
coins_earned = 30 (base)
             + (completed_achievements * 20)
             + (current_streak * 5)
             
coins_spent = sum(UserCoupon.cost_coins)
coins_remaining = max(0, earned - spent)
```

**POST /api/v1/storefront/purchase**
- Validates sufficient coins
- Creates UserCoupon with unique code
- Deducts coins (tracked via spent calculation)

**Coupon Tiers:**
- 5% off: 50 coins
- 10% off: 100 coins
- 20% off: 150 coins

**Coupon Generation:**
```python
generate_coupon_code(length=12):
  - Random uppercase letters + digits
  - Example: "A3K9LM2Q7P1X"
  - Expires in 30 days
```

---

### 8. Dashboard Router (`dashboard.py`)

**GET /api/v1/dashboard**
- Aggregates user statistics
- Recent plants (top 5)
- Recent achievements (top 5)

**GET /api/v1/leaderboard**
- Ranks users by achievement score
- Calculates: `sum(completed_achievements.points_awarded)`
- Includes total plants, achievements completed
- Returns top N users (default 10)

**Leaderboard Algorithm:**
```python
For each user:
  1. Get completed achievements
  2. Sum points_awarded from each achievement
  3. Count total_plants, achievements_completed
  4. Calculate final score

Sort users by score DESC
Assign ranks (1, 2, 3, ...)
Return LeaderboardEntry[]
```

---

### 9. Admin Router (`admin.py`)

**Protected Endpoints (JWT required):**

**POST /api/v1/admin/clear-database**
- Deletes all data (requires `YES_DELETE_ALL_DATA`)
- Respects FK constraints (deletes in order)

**POST /api/v1/admin/seed-achievements**
- Populates Achievement table with predefined achievements
- Idempotent (checks for duplicates)

**POST /api/v1/admin/initialize-user-achievements**
- Creates UserAchievement records for all users
- Links users to all active achievements

**POST /api/v1/admin/delete-test-users**
- Finds users with "User" in name (case-insensitive)
- Deletes in FK order: coupons → achievements → scans → plants → user
- Returns deleted count and names

**GET /api/v1/admin/list-tables**
- Shows all database tables and row counts

---

## Database Management

### Alembic Migrations (`alembic/`)

**Purpose:** Version control for database schema changes.

**Migration History:**
1. `17856973d7f9` - Initial schema (all tables)
2. `0a8e4d7ed3d1` - Add plant_icon column
3. `cb5efb5f6219` - Simplify structure (removed unused tables)
4. `a33d08e24a60` - Make plant_id nullable in plant_scans
5. `d0acb61cdf34` - Remove care_notes from plants table

**Commands:**
```bash
alembic upgrade head  # Apply migrations
alembic downgrade -1  # Rollback one migration
alembic revision --autogenerate -m "message"  # Create migration
```

### Database Setup (`init_db.py`)

**Purpose:** Initialize database with seed data.

**Seeds:**
- 12 achievements across 4 types
- Creates tables if not exist
- Safe to run multiple times

### Management Script (`manage_db_api.py`)

**CLI tool for admin operations:**
```bash
python manage_db_api.py seed-achievements
python manage_db_api.py clear-database
python manage_db_api.py delete-test-users
python manage_db_api.py list-tables
```

**Auth:** Requires `PLANTPAL_AUTH_TOKEN` environment variable.

---

## Request/Response Schemas (`schemas.py`)

**Pydantic Models for validation:**

**Request Schemas:**
- `UserCreate` - New user data
- `PlantCreate` - New plant data
- `AddToGardenRequest` - Plant from scan
- `PlantUpdate` - Edit plant fields
- `PurchaseCouponRequest` - Buy coupon

**Response Schemas:**
- `User`, `Plant`, `PlantScan` - Database models
- `ScanResult` - Scan API response
- `DashboardResponse` - Aggregated dashboard data
- `LeaderboardResponse` - Ranked users
- `CoinBalance` - Earned/spent/remaining
- `AchievementWithProgress` - Achievement + user progress

**Benefits:**
- Automatic validation
- Type hints for IDE support
- OpenAPI docs generation
- JSON serialization

---

## Authentication Flow

### JWT Validation Process

**1. Frontend Login:**
```
User clicks "Sign In" 
  → Cognito Hosted UI
  → User enters credentials
  → Cognito issues ID token + Access token
  → Redirect to /callback with tokens
```

**2. Backend Validation:**
```python
Request: Authorization: Bearer <ID_TOKEN>
  ↓
get_current_user_info() dependency
  ↓
verify_cognito_token():
  - Fetch Cognito public keys (JWKS)
  - Extract kid from token header
  - Find matching public key
  - Verify signature with RS256
  - Validate issuer URL
  - Check expiration
  ↓
Extract claims:
  - cognito_user_id = payload["sub"]
  - email = payload["email"]
  - name = payload["cognito:username"]
  ↓
Return user_info dict
```

**3. User Sync:**
```python
/api/v1/users/me endpoint:
  - Lookup user by cognito_user_id
  - If not exists: create from JWT claims
  - Initialize achievements for new users
  - Return User object
```

**Token Structure (Cognito ID Token):**
```json
{
  "sub": "uuid-cognito-user-id",
  "email": "user@example.com",
  "cognito:username": "username",
  "exp": 1700000000,
  "iss": "https://cognito-idp.region.amazonaws.com/poolid"
}
```

---

## Error Handling Patterns

**HTTP Status Codes:**
- `200` - Success
- `400` - Bad request (validation errors)
- `401` - Unauthorized (invalid/expired token)
- `404` - Resource not found
- `500` - Internal server error
- `503` - Service unavailable (external API down)

**Exception Handling:**
```python
try:
    # Database operation
    db.commit()
except Exception as e:
    db.rollback()
    raise HTTPException(
        status_code=500,
        detail=f"Operation failed: {str(e)}"
    )
```

**External API Retries:**
```python
# HuggingFace model loading
if response.status == 503:
    print("Model loading, waiting...")
    await asyncio.sleep(10)
    # Retry request
```

---

## Performance Optimizations

**1. Database Indexing:**
- `cognito_user_id` (unique, indexed) - Fast user lookup
- `email` (unique, indexed) - Login queries
- Foreign keys automatically indexed

**2. Query Optimization:**
```python
# Eager loading with joins
plants = db.query(Plant).options(
    joinedload(Plant.plant_scans)
).filter(Plant.user_id == user_id).all()
```

**3. Caching:**
- Cognito public keys cached with `@lru_cache()`
- Reduces JWKS endpoint calls

**4. Async Operations:**
```python
# Parallel API calls
plantnet_response, hf_response = await asyncio.gather(
    query_plantnet_api_async(image),
    query_huggingface_model_async(image)
)
```

**5. Image Compression:**
- Reduces bandwidth for external APIs
- Max 1MB after compression
- Quality balance (85%)

---

## Environment Configuration

**Required Variables (.env):**
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# AWS Cognito
COGNITO_REGION=ap-southeast-1
COGNITO_USER_POOL_ID=ap-southeast-1_xxxxx
COGNITO_CLIENT_ID=xxxxx

# External APIs
PLANTNET_API_KEY=xxxxx
HUGGINGFACE_API_KEY=xxxxx
OPENROUTER_API_KEY=xxxxx

# CORS
CORS_ORIGINS=http://localhost:3000,https://plantpal.example.com
```

---

## Deployment

### Docker Configuration (`Dockerfile`)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["./start.sh"]
```

### Startup Script (`start.sh`)

```bash
#!/bin/bash
# Run database migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### AWS ECS Deployment

**Infrastructure:**
- ECS Cluster: `fastapi-cluster`
- Service: `fastapi-service`
- Task Definition: `plantpal-task`
- Container Port: 8000
- Health Check: `GET /health`

**CI/CD (GitHub Actions):**
```yaml
1. Build Docker image
2. Push to AWS ECR
3. Register new task definition
4. Update ECS service
5. Wait for service stable
```

---

## API Documentation

**Auto-generated by FastAPI:**
- Swagger UI: `http://api-url/docs`
- ReDoc: `http://api-url/redoc`
- OpenAPI JSON: `http://api-url/openapi.json`

**Includes:**
- All endpoints with parameters
- Request/response schemas
- Authentication requirements
- Try-it-out functionality

---

## Key Workflows

### 1. New User Registration
```
Cognito signup → JWT issued → /users/me called
  → User created in DB
  → initialize_user_achievements()
  → 12 UserAchievement records created
  → User can start using app
```

### 2. Plant Scanning (New Plant)
```
Upload image → /scan endpoint
  → Plant.Net identifies species
  → HuggingFace detects disease
  → OpenRouter generates care tips
  → PlantScan record created (plant_id = null)
  → Return ScanResult to frontend
  → User clicks "Add to Garden"
  → /plants/add-to-garden
  → Plant record created
  → PlantScan linked to Plant
  → plants_count achievement updated
```

### 3. Rescanning Existing Plant
```
Upload image with plant_id → /scan endpoint
  → Same AI analysis
  → Update Plant.current_health_score
  → Create new PlantScan record (linked to plant_id)
  → Update streak if scan on new day
  → Update achievements (scans_count, streak)
  → Return updated health data
```

### 4. Achievement Unlock
```
User action (scan, add plant) triggers:
  → update_achievement_progress(type, current_value)
  → Check if value >= requirement
  → Mark is_completed = True
  → completed_at = now()
  → Points added to user score
  → Coins calculation updated
  → Frontend shows unlock animation
```

### 5. Coupon Purchase
```
User clicks "Buy 10% off for 100 coins"
  → /storefront/purchase
  → Calculate coins_remaining
  → If insufficient: return error
  → If sufficient:
    → generate_coupon_code()
    → Create UserCoupon record
    → Return coupon with code
  → Frontend shows coupon modal
```

---

## Testing & Debugging

**Test Endpoints:**
- `GET /api/v1/scan-test` - Verify scan router works
- `POST /api/v1/users/test` - Create test user
- `GET /health` - Basic health check

**Logging:**
- Prints with emoji prefixes (✅, ❌, 🔍, 🌱)
- SQL queries logged by SQLAlchemy
- External API responses logged

**Database Inspection:**
```bash
# Connect to RDS
psql -h plantpal-postgres...rds.amazonaws.com -U plantpal_admin -d plantpal

# Query data
SELECT * FROM users;
SELECT * FROM plants WHERE user_id = 'uuid';
SELECT * FROM user_achievements WHERE is_completed = true;
```

---

## Security Considerations

**1. Authentication:**
- JWT validation on all protected routes
- No API keys stored in database
- Cognito handles password security

**2. SQL Injection Prevention:**
- SQLAlchemy ORM (parameterized queries)
- No raw SQL with user input

**3. CORS Configuration:**
- Whitelist specific origins
- No wildcard in production

**4. Rate Limiting:**
- External APIs have built-in limits
- No explicit rate limiting implemented (future enhancement)

**5. Data Validation:**
- Pydantic schemas validate all inputs
- Type checking prevents malformed data

---

## Future Enhancements

- WebSocket support for real-time updates
- Redis caching for leaderboard
- Background tasks with Celery
- S3 integration for plant images
- Push notifications (FCM/SNS)
- Advanced analytics (PostgreSQL window functions)
- GraphQL API option
- Rate limiting with Redis
- API versioning (v2 routes)

---

## Dependencies (`requirements.txt`)

**Core:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `sqlalchemy` - ORM
- `psycopg2-binary` - PostgreSQL driver
- `alembic` - Migrations

**Auth:**
- `python-jose[cryptography]` - JWT validation
- `python-multipart` - File uploads

**External APIs:**
- `aiohttp` - Async HTTP client
- `requests` - Sync HTTP client
- `Pillow` - Image processing

**Utilities:**
- `python-dotenv` - Environment variables
- `pydantic` - Data validation

---

## Troubleshooting Common Issues

**Issue: "User not found" errors**
- Solution: Ensure JWT has correct `sub` claim
- Check user created via `/users/me` on first login

**Issue: Achievement progress not updating**
- Solution: Call `check-streaks` endpoint
- Verify `update_achievement_progress()` called after actions

**Issue: External API timeouts**
- Solution: Check API keys in .env
- HuggingFace model may need warmup time (503 retry)

**Issue: Database connection errors**
- Solution: Verify DATABASE_URL in .env
- Check RDS security group allows EC2 connections

**Issue: CORS errors**
- Solution: Add frontend URL to CORS_ORIGINS
- Ensure protocol (http/https) matches

---

## Monitoring & Logs

**Application Logs:**
```bash
# View ECS logs
aws logs tail /ecs/plantpal-task --follow

# Docker logs locally
docker logs <container-id> -f
```

**Database Monitoring:**
- RDS CloudWatch metrics
- Query performance insights
- Connection pool monitoring

**API Metrics:**
- Request count by endpoint
- Average response time
- Error rate tracking
