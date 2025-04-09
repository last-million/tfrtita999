from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from ..database import db
from ..middleware.auth import get_current_user
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/calls/{call_sid}/actions")
async def get_call_actions(
    call_sid: str = Path(..., description="The call SID to fetch actions for"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get all actions performed during a call.
    
    Args:
        call_sid: Call SID
        current_user: Authenticated user info
        
    Returns:
        List of actions performed during the call
    """
    logger.info(f"Getting actions for call {call_sid}")
    
    # Check if call exists and user has access to it
    call_query = "SELECT * FROM calls WHERE call_sid = %s"
    call = await db.fetch_one(call_query, (call_sid,))
    
    if not call:
        logger.error(f"Call {call_sid} not found")
        raise HTTPException(status_code=404, detail="Call not found")
    
    # Get actions
    query = """
        SELECT id, call_sid, action_type, action_data, created_at
        FROM call_actions
        WHERE call_sid = %s
        ORDER BY created_at DESC
    """
    
    results = await db.fetch_all(query, (call_sid,))
    
    actions = []
    for row in results:
        try:
            action_data = json.loads(row["action_data"]) if row["action_data"] else {}
        except:
            action_data = {}
            
        actions.append({
            "id": row["id"],
            "call_sid": row["call_sid"],
            "action_type": row["action_type"],
            "action_data": action_data,
            "created_at": row["created_at"].isoformat() if isinstance(row["created_at"], datetime) else row["created_at"]
        })
    
    return {
        "success": True,
        "actions": actions
    }

@router.post("/calls/{call_sid}/actions")
async def record_call_action(
    call_sid: str = Path(..., description="The call SID to record an action for"),
    action_data: Dict[str, Any] = Body(..., description="Action data to record"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Record a new action performed during a call.
    
    Args:
        call_sid: Call SID
        action_data: Action data to record
        current_user: Authenticated user info
        
    Returns:
        Recorded action
    """
    logger.info(f"Recording action for call {call_sid}")
    
    # Check if call exists
    call_query = "SELECT * FROM calls WHERE call_sid = %s"
    call = await db.fetch_one(call_query, (call_sid,))
    
    if not call:
        logger.error(f"Call {call_sid} not found")
        raise HTTPException(status_code=404, detail="Call not found")
    
    # Extract action details
    action_type = action_data.get("action_type")
    if not action_type:
        logger.error("Missing action_type in request body")
        raise HTTPException(status_code=400, detail="Missing action_type in request body")
        
    # Convert action data to JSON
    try:
        action_data_json = json.dumps(action_data)
    except Exception as e:
        logger.error(f"Error serializing action data: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid action data format: {str(e)}")
    
    # Insert action
    query = """
        INSERT INTO call_actions (call_sid, action_type, action_data, created_at)
        VALUES (%s, %s, %s, NOW())
    """
    
    try:
        action_id = await db.execute(query, (call_sid, action_type, action_data_json))
    except Exception as e:
        logger.error(f"Error recording call action: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error recording call action: {str(e)}")
    
    # Return result
    return {
        "success": True,
        "action_id": action_id,
        "message": "Action recorded successfully"
    }

@router.get("/dashboard/action_metrics")
async def get_action_metrics(
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get metrics on actions performed during calls for the dashboard.
    
    Args:
        date_from: Start date for filtering
        date_to: End date for filtering
        current_user: Authenticated user info
        
    Returns:
        Action metrics for dashboard
    """
    logger.info(f"Getting action metrics from {date_from} to {date_to}")
    
    # Construct date filter clause
    date_clause = ""
    params = []
    
    if date_from:
        date_clause += " AND created_at >= %s"
        params.append(date_from)
    
    if date_to:
        date_clause += " AND created_at <= %s"
        params.append(date_to + " 23:59:59")
    
    # Get action type distribution
    action_type_query = f"""
        SELECT action_type, COUNT(*) as count
        FROM call_actions
        WHERE 1=1 {date_clause}
        GROUP BY action_type
        ORDER BY count DESC
    """
    
    action_type_results = await db.fetch_all(action_type_query, params)
    
    # Get action counts by day
    action_trend_query = f"""
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as count
        FROM call_actions
        WHERE 1=1 {date_clause}
        GROUP BY DATE(created_at)
        ORDER BY date
    """
    
    action_trend_results = await db.fetch_all(action_trend_query, params)
    
    # Get most common search queries (if applicable)
    search_query = f"""
        SELECT 
            JSON_UNQUOTE(JSON_EXTRACT(action_data, '$.query')) as search_query,
            COUNT(*) as count
        FROM call_actions
        WHERE action_type = 'search' {date_clause}
        GROUP BY search_query
        ORDER BY count DESC
        LIMIT 5
    """
    
    search_results = await db.fetch_all(search_query, params)
    
    # Format results
    action_types = {}
    for row in action_type_results:
        action_types[row["action_type"]] = row["count"]
    
    action_trends = []
    for row in action_trend_results:
        if isinstance(row["date"], datetime):
            date_str = row["date"].strftime("%Y-%m-%d")
        else:
            date_str = str(row["date"])
            
        action_trends.append({
            "date": date_str,
            "count": row["count"]
        })
    
    top_searches = []
    for row in search_results:
        if row["search_query"] and row["search_query"] not in ["null", "undefined"]:
            top_searches.append({
                "query": row["search_query"],
                "count": row["count"]
            })
    
    return {
        "success": True,
        "metrics": {
            "action_type_distribution": action_types,
            "action_trends": action_trends,
            "top_searches": top_searches
        }
    }
