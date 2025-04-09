# backend/app/middleware/auth.py

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from ..config import settings
from ..database import db
import logging

# Configure security scheme
security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)

# Load JWT configuration from settings
SECRET_KEY = settings.jwt_secret
ALGORITHM = settings.jwt_algorithm

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Verify JWT token and return the user information.
    This function is used as a dependency in protected routes.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Verify that the user exists and is active
        query = "SELECT id, username, is_admin, is_active FROM users WHERE username = %s"
        users = await db.execute(query, (username,))
        
        if not users:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        user = users[0]
        
        # Check if user is active
        if not user.get('is_active', True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Return user information from payload and database
        return {
            "sub": username,
            "user_id": user["id"],
            "is_admin": bool(user.get("is_admin", False))
        }
        
    except JWTError as e:
        logger.error(f"JWT validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating credentials: {str(e)}",
        )

async def admin_required(current_user: dict = Security(verify_token)):
    """
    Additional dependency that ensures the user is an admin.
    Use this for admin-only routes.
    """
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user
