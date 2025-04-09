import os
import logging
import json
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from jose import jwt, JWTError
from typing import List, Optional, Dict, Any, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JWT settings
JWT_SECRET = "strong-secret-key-for-jwt-tokens"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120  # Extended token lifetime

# Create app
app = FastAPI(
    title="Voice Call AI API",
    description="API for Voice Call AI application",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
class LoginRequest(BaseModel):
    username: str
    password: str

class UserInfo(BaseModel):
    id: int
    username: str
    is_admin: bool
    is_active: bool

class ServiceStatus(BaseModel):
    name: str
    status: str
    message: Optional[str] = None

# --- Helper Functions ---
async def get_current_user_from_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id", 0)
        
        # Special handling for hardcoded hamza user
        if username == "hamza" and user_id == 1:
            return {
                "id": 1,
                "username": "hamza",
                "is_admin": True,
                "is_active": True
            }
        
        # Special handling for admin user
        if username == "admin" and user_id == 0:
            return {
                "id": 0,
                "username": "admin",
                "is_admin": True,
                "is_active": True
            }
        
        # For other users, return basic info from token
        return {
            "id": user_id,
            "username": username,
            "is_admin": payload.get("is_admin", False),
            "is_active": True
        }
    except JWTError as e:
        logger.error(f"JWT error: {e}")
        return None
    except Exception as e:
        logger.error(f"Error in get_current_user_from_token: {e}")
        return None

def create_access_token(data: dict, expires_delta: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ")[1]
    user = await get_current_user_from_token(token)
    return user

# --- Basic API Endpoints ---
@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Voice Call AI API is running",
        "version": "1.0.0",
        "environment": os.getenv("ENV", "production"),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api")
async def api_root():
    return {"status": "ok", "message": "API service is running"}

# --- Authentication Endpoints ---
@app.post("/api/auth/token")
async def login_direct(request_data: LoginRequest):
    """Direct login endpoint"""
    logger.info(f"Login attempt for user: {request_data.username}")
    try:
        if request_data.username == "hamza" and request_data.password == "AFINasahbi@-11":
            logger.info("Login successful for hamza")
            token_data = {
                "sub": request_data.username,
                "user_id": 1,
                "is_admin": True
            }
            access_token = create_access_token(token_data)
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "username": request_data.username,
                "is_admin": True
            }
        elif request_data.username == "admin" and request_data.password == "admin":
            logger.info("Login successful for admin")
            token_data = {
                "sub": "admin",
                "user_id": 0,
                "is_admin": True
            }
            access_token = create_access_token(token_data)
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "username": "admin",
                "is_admin": True
            }
        else:
            logger.warning(f"Invalid login attempt for user: {request_data.username}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid username or password"}
            )
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error during authentication: {str(e)}"}
        )

@app.get("/api/auth/me", response_model=UserInfo)
async def get_current_user_info(request: Request):
    """Get current authenticated user info"""
    logger.info("Auth/me endpoint called")
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning("Missing or invalid Authorization header")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Not authenticated"},
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = auth_header.split(" ")[1]
    user = await get_current_user_from_token(token)
    
    if not user:
        logger.warning("Invalid token or user not found")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or expired token"},
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    logger.info(f"User authenticated: {user.get('username')}")
    return user

@app.post("/api/auth/logout")
async def logout():
    """Logout endpoint - doesn't need to do much since JWT tokens are stateless"""
    return {"success": True, "message": "Logged out successfully"}

# --- Dashboard Endpoints ---
@app.get("/api/dashboard/stats")
async def get_dashboard_stats(request: Request):
    """Get dashboard statistics data"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    
    return {
        "total_calls": 0,
        "active_services": 0,
        "total_documents": 0,
        "ai_accuracy": 85,
    }

@app.get("/api/dashboard/recent-activities")
async def get_recent_activities(request: Request):
    """Get recent activities for dashboard"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    
    return {
        "activities": []
    }

@app.get("/api/dashboard/call-capacity")
async def get_call_capacity(request: Request, use_live_data: bool = False):
    """Get call capacity data"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    
    # Return an empty dataset
    return {
        "capacity": {
            "total": 1000,
            "used": 0,
            "available": 1000
        },
        "usage_over_time": [
            {"date": "2025-03-01", "used": 0},
            {"date": "2025-03-02", "used": 0},
            {"date": "2025-03-03", "used": 0}
        ]
    }

# --- Service Endpoints ---
@app.get("/api/services/status")
async def get_services_status(request: Request):
    """Get status of all connected services"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    
    return {
        "services": [
            {"name": "Twilio", "status": "disconnected", "message": "API key missing or invalid"},
            {"name": "Supabase", "status": "disconnected", "message": "Connection failed"},
            {"name": "Google Calendar", "status": "disconnected", "message": "Not configured"},
            {"name": "Ultravox", "status": "disconnected", "message": "API key required"},
            {"name": "Database", "status": "healthy", "message": "Connected"}
        ]
    }

@app.get("/api/services/{service_name}/status")
async def get_service_status(service_name: str, request: Request):
    """Get status of a specific service"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    
    services = {
        "twilio": {"status": "disconnected", "message": "API key missing or invalid"},
        "supabase": {"status": "disconnected", "message": "Connection failed"},
        "google_calendar": {"status": "disconnected", "message": "Not configured"},
        "ultravox": {"status": "disconnected", "message": "API key required"},
        "database": {"status": "healthy", "message": "Connected"}
    }
    
    if service_name.lower() not in services:
        return JSONResponse(status_code=404, content={"detail": "Service not found"})
    
    return services[service_name.lower()]

# --- Supabase Endpoints ---
@app.get("/api/supabase/tables")
async def get_supabase_tables(request: Request):
    """Get Supabase tables - stub endpoint"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    
    return {
        "status": "success", 
        "tables": []  # Empty array since Supabase isn't connected
    }

@app.get("/api/supabase/tables/{table_id}/data")
async def get_supabase_table_data(table_id: str, request: Request):
    """Get data from a Supabase table - stub endpoint"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    
    return {
        "status": "error",
        "message": "Supabase connection not configured"
    }

# --- Google Drive Endpoints ---
@app.get("/api/google/drive/files")
async def get_google_drive_files(request: Request):
    """Get Google Drive files - stub endpoint"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    
    return {
        "status": "success",
        "files": []  # Empty array since Google Drive isn't connected
    }

@app.get("/api/google/drive/files/{file_id}")
async def get_google_drive_file(file_id: str, request: Request):
    """Get a specific Google Drive file - stub endpoint"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    
    return {
        "status": "error",
        "message": "Google Drive connection not configured"
    }

# --- Calls Endpoints ---
@app.get("/api/calls")
async def get_calls(request: Request):
    """Get all calls"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    
    return {
        "calls": [
            {
                "id": 1,
                "from": "+1555789012",
                "to": "+1987654321",
                "status": "completed",
                "duration": 120,
                "timestamp": "2025-03-01T12:00:00Z"
            }
        ]
    }

@app.get("/api/calls/{call_id}")
async def get_call(call_id: int, request: Request):
    """Get a specific call"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    
    return {
        "id": call_id,
        "from": "+1555789012",
        "to": "+1987654321",
        "status": "completed",
        "duration": 120,
        "timestamp": "2025-03-01T12:00:00Z",
        "transcription": "This is a sample transcription."
    }

# --- Knowledge Base Endpoints ---
@app.get("/api/knowledge")
async def get_knowledge_documents(request: Request):
    """Get all knowledge documents"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    
    return {
        "documents": []
    }

@app.post("/api/knowledge")
async def create_knowledge_document(request: Request):
    """Create a new knowledge document"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    
    return {
        "status": "success",
        "document_id": 1
    }

# --- Admin Endpoints ---
@app.get("/api/admin/config")
async def get_admin_config(request: Request):
    """Get admin configuration - only accessible to admin users"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    
    if not user.get("is_admin"):
        return JSONResponse(
            status_code=403, 
            content={"detail": "You don't have permission to access this resource"}
        )
    
    return {
        "config": {
            "system_name": "Voice Call AI",
            "max_calls_per_day": 1000,
            "default_language": "en-US"
        }
    }

@app.get("/api/admin/users")
async def get_admin_users(request: Request):
    """Get all users - only accessible to admin users"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    
    if not user.get("is_admin"):
        return JSONResponse(
            status_code=403, 
            content={"detail": "You don't have permission to access this resource"}
        )
    
    return {
        "users": [
            {
                "id": 1,
                "username": "hamza",
                "is_admin": True,
                "is_active": True
            },
            {
                "id": 0,
                "username": "admin",
                "is_admin": True,
                "is_active": True
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
