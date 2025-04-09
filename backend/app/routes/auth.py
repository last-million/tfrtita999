from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from jose import JWTError, jwt

from ..config import settings
from ..database import db
from ..security.password import verify_password, get_password_hash

# Create router
router = APIRouter()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# Schema models
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    is_admin: bool

class UserInfo(BaseModel):
    id: int
    username: str
    is_admin: bool
    is_active: bool

# Token validation function
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id", 0)
        if username is None:
            raise credentials_exception
        
        # For hardcoded users (bypass database lookup)
        if username == "hamza" and user_id == 1:
            return {"id": 1, "username": "hamza", "is_admin": True, "is_active": True}
        
        if username == "admin" and user_id == 0:
            return {"id": 0, "username": "admin", "is_admin": True, "is_active": True}
            
        # Try to fetch from database for other users
        try:
            query = "SELECT id, username, is_admin, is_active FROM users WHERE id = %s"
            users = await db.execute(query, (user_id,))
            if not users:
                raise credentials_exception
            user = users[0]
            return user
        except Exception:
            # If database fails, fall back to token info for minimal functionality
            return {
                "id": user_id,
                "username": username,
                "is_admin": payload.get("is_admin", False),
                "is_active": True
            }
    except JWTError:
        raise credentials_exception

# Get current user info endpoint
@router.get("/api/auth/me", response_model=UserInfo)
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current authenticated user info"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user

# Login endpoint (only used as a fallback if the main.py direct endpoint fails)
@router.post("/api/auth/token", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """API login endpoint"""
    # This is just a fallback route - main implementation is in main.py
    raise HTTPException(
        status_code=501,
        detail="Login should be handled by main.py endpoint"
    )
