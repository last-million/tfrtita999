from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from typing import Dict, List, Optional
from ..database import db
from ..services.call_analyzer_service import call_analyzer_service
from ..middleware.auth import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/calls/{call_sid}/analysis")
async def get_call_analysis(
    call_sid: str = Path(..., description="The call SID to analyze"),
    force_refresh: bool = Query(False, description="Whether to force a new analysis"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get analysis for a specific call.
    
    Args:
        call_sid: Call SID to analyze
        force_refresh: Whether to force a new analysis even if one exists
        current_user: Authenticated user info
        
    Returns:
        Call analysis information
    """
    logger.info(f"Getting call analysis for {call_sid}, force_refresh={force_refresh}")
    
    # Check if call exists and user has access to it
    call_query = "SELECT * FROM calls WHERE call_sid = %s"
    call = await db.fetch_one(call_query, (call_sid,))
    
    if not call:
        logger.error(f"Call {call_sid} not found")
        raise HTTPException(status_code=404, detail="Call not found")
    
    # Get call analysis
    result = await call_analyzer_service.analyze_call(call_sid, force_refresh)
    
    if not result.get("success", False):
        logger.error(f"Error analyzing call {call_sid}: {result.get('error', 'Unknown error')}")
        return {
            "success": False,
            "error": result.get("error", "Failed to analyze call")
        }
    
    return {
        "success": True,
        "analysis": result.get("analysis", {})
    }

@router.post("/calls/{call_sid}/reanalyze")
async def reanalyze_call(
    call_sid: str = Path(..., description="The call SID to reanalyze"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Force a new analysis of a call.
    
    Args:
        call_sid: Call SID to reanalyze
        current_user: Authenticated user info
        
    Returns:
        Updated call analysis
    """
    logger.info(f"Reanalyzing call {call_sid}")
    
    # Check if call exists and user has access to it
    call_query = "SELECT * FROM calls WHERE call_sid = %s"
    call = await db.fetch_one(call_query, (call_sid,))
    
    if not call:
        logger.error(f"Call {call_sid} not found")
        raise HTTPException(status_code=404, detail="Call not found")
    
    # Reanalyze call (force refresh)
    result = await call_analyzer_service.analyze_call(call_sid, force_refresh=True)
    
    if not result.get("success", False):
        logger.error(f"Error reanalyzing call {call_sid}: {result.get('error', 'Unknown error')}")
        return {
            "success": False,
            "error": result.get("error", "Failed to reanalyze call")
        }
    
    return {
        "success": True,
        "analysis": result.get("analysis", {})
    }

@router.get("/dashboard/analytics")
async def get_call_analytics(
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get aggregated call analytics for the dashboard.
    
    Args:
        date_from: Start date for filtering
        date_to: End date for filtering
        current_user: Authenticated user info
        
    Returns:
        Aggregated call analytics
    """
    logger.info(f"Getting call analytics from {date_from} to {date_to}")
    
    # Construct date filter clause
    date_clause = ""
    params = []
    
    if date_from:
        date_clause += " AND created_at >= %s"
        params.append(date_from)
    
    if date_to:
        date_clause += " AND created_at <= %s"
        params.append(date_to + " 23:59:59")
    
    # Get sentiment distribution
    sentiment_query = f"""
        SELECT 
            JSON_UNQUOTE(JSON_EXTRACT(analysis, '$.sentiment.sentiment')) as sentiment,
            COUNT(*) as count
        FROM call_analysis
        WHERE 1=1 {date_clause}
        GROUP BY sentiment
    """
    
    sentiment_results = await db.fetch_all(sentiment_query, params)
    
    # Get intent distribution
    intent_query = f"""
        SELECT 
            JSON_UNQUOTE(JSON_EXTRACT(analysis, '$.intent.primary.name')) as intent,
            COUNT(*) as count
        FROM call_analysis
        WHERE 1=1 {date_clause}
        GROUP BY intent
        ORDER BY count DESC
        LIMIT 5
    """
    
    intent_results = await db.fetch_all(intent_query, params)
    
    # Get average sentiment score
    score_query = f"""
        SELECT 
            AVG(CAST(JSON_EXTRACT(analysis, '$.sentiment.score') AS DECIMAL(10,2))) as avg_score
        FROM call_analysis
        WHERE 1=1 {date_clause}
    """
    
    score_result = await db.fetch_one(score_query, params)
    
    # Format results
    sentiments = {}
    for row in sentiment_results:
        if row["sentiment"] and row["sentiment"] not in ["null", "undefined"]:
            sentiments[row["sentiment"]] = row["count"]
    
    intents = {}
    for row in intent_results:
        if row["intent"] and row["intent"] not in ["null", "undefined"]:
            intents[row["intent"]] = row["count"]
    
    avg_sentiment = score_result["avg_score"] if score_result and score_result["avg_score"] else 0
    
    return {
        "success": True,
        "analytics": {
            "sentiment_distribution": sentiments,
            "top_intents": intents,
            "average_sentiment": float(avg_sentiment)
        }
    }
