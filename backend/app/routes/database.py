from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional
from ..database import db
from ..middleware.auth import get_current_user

router = APIRouter(
    prefix="/database",
    tags=["database"]
)

class DatabaseConfig(BaseModel):
    host: str
    user: str
    password: str
    database: str

class ToggleExternalDatabaseRequest(BaseModel):
    enabled: bool
    config: Optional[DatabaseConfig] = None

@router.post("/test-connection")
async def test_database_connection(
    config: DatabaseConfig,
    _: Dict = Depends(get_current_user)
):
    """
    Test connection to an external database
    
    Args:
        config: Database configuration
        
    Returns:
        Connection test result
    """
    result = await db.test_connection({
        "host": config.host,
        "user": config.user,
        "password": config.password,
        "database": config.database
    })
    
    if not result["success"]:
        return {
            "success": False,
            "message": result["message"]
        }
    
    return {
        "success": True,
        "message": "Connection successful"
    }

@router.post("/toggle")
async def toggle_external_database(
    request: ToggleExternalDatabaseRequest,
    _: Dict = Depends(get_current_user)
):
    """
    Toggle external database connection
    
    Args:
        request: Toggle request with enabled flag and optional config
        
    Returns:
        Operation result
    """
    if request.enabled and not request.config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database configuration required when enabling external database"
        )
    
    config = None
    if request.config:
        config = {
            "host": request.config.host,
            "user": request.config.user,
            "password": request.config.password,
            "database": request.config.database
        }
    
    success = await db.switch_to_external(request.enabled, config)
    
    if not success:
        return {
            "success": False,
            "message": "Failed to switch database configuration"
        }
    
    return {
        "success": True,
        "message": f"Successfully switched to {'external' if request.enabled else 'local'} database"
    }

@router.get("/status")
async def get_database_status(_: Dict = Depends(get_current_user)):
    """
    Get current database connection status
    
    Returns:
        Database connection information
    """
    return {
        "using_external_db": db.use_external_db,
        "connected": db.connected,
        "ext_config": {
            "host": db.ext_db_config.get("host", ""),
            "user": db.ext_db_config.get("user", ""),
            "database": db.ext_db_config.get("database", "")
        } if db.use_external_db else None
    }
