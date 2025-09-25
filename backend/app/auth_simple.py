"""
Simple authentication utilities for development
For production, implement proper JWT validation
"""
from fastapi import HTTPException, status, Depends, Header
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

async def get_current_user_info(authorization: Optional[str] = Header(None)):
    """
    Extract user information from Authorization header
    For development: accepts any token and returns mock user info
    For production: should implement proper JWT validation
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    token = authorization.replace("Bearer ", "")
    
    # For development: return mock user info that matches our test user
    # In production: decode and validate the JWT token
    return {
        "cognito_user_id": "test-user-20240115",
        "email": "testuser@plantpal.com",
        "name": "Sarah Green",
        "username": "sarahgreen"
    }

# For production, use this function with proper JWT validation:
"""
async def get_current_user_info_production(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Implement JWT validation here
        # 1. Get Cognito public keys
        # 2. Verify token signature
        # 3. Check token expiry
        # 4. Extract user claims
        
        payload = validate_jwt_token(token)
        
        return {
            "cognito_user_id": payload["sub"],
            "email": payload.get("email"),
            "name": payload.get("name", payload.get("cognito:username")),
            "username": payload.get("cognito:username")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
"""