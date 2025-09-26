from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from app.database import engine
from app.models import Base
from app.routers import users, plants, scan, dashboard, debug

# Load environment variables
load_dotenv()

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PlantPal API",
    description="Plant identification and care tracking API.",
    version="1.0.0"
)

# CORS configuration
origins = os.getenv(
    "CORS_ORIGINS", 
    "http://localhost:3000,http://plantpal-frontend-bucket.s3-website-ap-southeast-1.amazonaws.com"
).split(",")

# Strip whitespace from origins
origins = [origin.strip() for origin in origins]

print(f"🌐 CORS Origins configured: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Root endpoints
@app.get("/")
def read_root():
    return {
        "message": "Welcome to PlantPal API! 🌱",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "PlantPal API is running"}

# Include routers
app.include_router(users.router)
app.include_router(plants.router)
app.include_router(scan.router)
app.include_router(dashboard.router)
app.include_router(debug.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)