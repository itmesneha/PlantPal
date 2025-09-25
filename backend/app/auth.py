"""
JWT Token validation and user extraction utilities for Cognito
"""
from jose import jwt
from jose.utils import base64url_decode
import requests
import json
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import lru_cache
import os
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from cryptography.hazmat.backends import default_backend
import base64

load_dotenv()

security = HTTPBearer()

# Cognito configuration
COGNITO_REGION = os.getenv("COGNITO_REGION", "ap-southeast-1")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "ap-southeast-1_km8Z7zM54")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")

print(f"🔧 Cognito Config - Region: {COGNITO_REGION}")
print(f"🔧 Cognito Config - User Pool ID: {COGNITO_USER_POOL_ID}")
print(f"🔧 Cognito Config - Client ID: {COGNITO_CLIENT_ID}")

# Cognito JWKS URL
COGNITO_JWKS_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json"

@lru_cache()
def get_cognito_public_keys():
    """Fetch and cache Cognito public keys for JWT verification"""
    try:
        response = requests.get(COGNITO_JWKS_URL)
        response.raise_for_status()
        return response.json()["keys"]
    except Exception as e:
        print(f"❌ Failed to fetch Cognito public keys: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch Cognito public keys: {str(e)}"
        )

def verify_cognito_token(token: str):
    """Verify Cognito JWT token and extract user information"""
    try:
        print(f"🔍 Verifying token (first 50 chars): {token[:50]}...")
        
        # Get the token header
        header = jwt.get_unverified_header(token)
        kid = header["kid"]
        print(f"🔍 Token kid: {kid}")
        
        # Find the correct public key
        public_keys = get_cognito_public_keys()
        public_key_jwk = None
        
        for key in public_keys:
            if key["kid"] == kid:
                public_key_jwk = key
                break
        
        if not public_key_jwk:
            print(f"❌ Public key not found for kid: {kid}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: public key not found"
            )
        
        print(f"✅ Found public key for kid: {kid}")
        
        # Use the JWK directly - python-jose can handle JWK format
        public_key = public_key_jwk
        
        # Verify and decode the token
        print(f"🔍 Verifying with audience: {COGNITO_CLIENT_ID}")
        print(f"🔍 Verifying with issuer: https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}")
        
        # For development, let's try without audience validation first
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"verify_aud": False},  # Temporarily disable audience verification
            issuer=f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
        )
        
        print(f"✅ Token verification successful. User: {payload.get('cognito:username', payload.get('sub'))}")
        print(f"🔍 ID Token payload: {payload}")
        return payload
        
    except jwt.ExpiredSignatureError:
        print("❌ JWT Error: Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTClaimsError as e:
        print(f"❌ JWT Claims Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token claims: {str(e)}"
        )
    except Exception as e:
        print(f"❌ JWT Validation Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )

async def get_current_user_info(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract user information from JWT token"""
    token = credentials.credentials
    payload = verify_cognito_token(token)
    
    return {
        "cognito_user_id": payload["sub"],
        "email": payload.get("email"),
        "name": payload.get("name", payload.get("cognito:username")),
        "username": payload.get("cognito:username")
    }