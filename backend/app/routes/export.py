from fastapi import APIRouter, HTTPException, Depends, Body, Query, status
from typing import List, Dict, Any, Optional
from ..middleware.auth import verify_token
from ..database import db
import logging
from ..services.google_service import GoogleService
from ..services.supabase_service import SupabaseService
from ..services.airtable_service import AirtableService
from ..services.transcript_analyzer import TranscriptAnalyzer
from datetime import datetime
import asyncio
import json

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
google_service = GoogleService()
supabase_service = SupabaseService()
airtable_service = AirtableService()
transcript_analyzer = TranscriptAnalyzer()

# Default field mappings for automatic setup
DEFAULT_FIELD_MAPPINGS = {
    "call_sid": "Call SID",
    "from_number": "From Number",
    "to_number": "To Number",
    "direction": "Direction",
    "status": "Status",
    "start_time": "Start Time",
    "end_time": "End Time",
    "duration": "Duration (seconds)",
    "recording_url": "Recording URL",
    "transcription": "Transcription",
    "cost": "Cost",
    "ultravox_cost": "Ultravox Cost",
    "hang_up_by": "Hung Up By",
    "created_at": "Created At"
}

class CallExportOptions:
    """Helper class for call export options"""
    def __init__(self, data):
        self.service = data.get("service")
        self.destination = data.get("destination")
        self.create_new = data.get("createNew", False)
        self.field_mapping = data.get("fieldMapping", {})
        self.call_data = data.get("callData", [])
        self.sync_enabled = data.get("syncEnabled", False)

    def is_valid(self):
        return (
            self.service in ["google_sheets", "supabase", "airtable"] and
            self.destination and
            isinstance(self.field_mapping, dict)
        )

@router.post("/api/export/calls")
async def export_calls(
    options: Dict[str, Any] = Body(...),
    current_user: dict = Depends(verify_token)
):
    """
    Export call data to Google Sheets, Supabase, or Airtable
    """
    export_options = CallExportOptions(options)
    
    if not export_options.is_valid():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid export options provided"
        )
    
    try:
        # Fetch all call data if not provided in request
        if not export_options.call_data:
            query = """
                SELECT 
                    call_sid, from_number, to_number, direction, 
                    status, start_time, end_time, duration, 
                    recording_url, transcription, cost, ultravox_cost,
                    hang_up_by, created_at
                FROM calls
                ORDER BY created_at DESC
                LIMIT 1000
            """
            export_options.call_data = await db.execute(query)
        
        # Get user credentials
        user_id = current_user.get("user_id")
        credentials = await get_service_credentials(user_id, export_options.service)
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{export_options.service} credentials not found"
            )
        
        # Process call data to extract client information from transcriptions
        processed_call_data = transcript_analyzer.process_call_data(export_options.call_data)
        
        # Format data for export based on field mapping
        formatted_data = format_data_for_export(processed_call_data, export_options.field_mapping)
        
        # Export to the selected service
        if export_options.service == "google_sheets":
            result = await export_to_google_sheets(credentials, export_options, formatted_data)
        elif export_options.service == "supabase":
            result = await export_to_supabase(credentials, export_options, formatted_data)
        elif export_options.service == "airtable":
            result = await export_to_airtable(credentials, export_options, formatted_data)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid service selected"
            )
            
        # Set up real-time sync if enabled
        if export_options.sync_enabled:
            await setup_sync_job(current_user, export_options)
            
        return {
            "success": True,
            "message": f"Successfully exported {len(export_options.call_data)} records to {export_options.service}",
            "destination": export_options.destination,
            "service": export_options.service,
            "details": result
        }
    except Exception as e:
        logger.error(f"Error exporting calls: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting calls: {str(e)}"
        )

@router.get("/api/credentials/status")
async def check_credentials_status(current_user: dict = Depends(verify_token)):
    """
    Check the status of service credentials for the current user
    """
    try:
        user_id = current_user.get("user_id")
        
        # Get credentials for each service
        google_creds = await get_service_credentials(user_id, "google_sheets")
        supabase_creds = await get_service_credentials(user_id, "supabase")
        airtable_creds = await get_service_credentials(user_id, "airtable")
        
        return {
            "google_sheets": {
                "connected": google_creds is not None,
                "credentials": google_creds
            },
            "supabase": {
                "connected": supabase_creds is not None,
                "credentials": supabase_creds
            },
            "airtable": {
                "connected": airtable_creds is not None,
                "credentials": airtable_creds
            }
        }
    except Exception as e:
        logger.error(f"Error checking credentials status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking credentials status: {str(e)}"
        )

@router.get("/api/google/sheets")
async def list_google_sheets(current_user: dict = Depends(verify_token)):
    """
    List available Google Sheets for the current user
    """
    try:
        user_id = current_user.get("user_id")
        credentials = await get_service_credentials(user_id, "google_sheets")
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google Sheets credentials not found"
            )
            
        sheets = await google_service.list_sheets(credentials)
        return sheets
    except Exception as e:
        logger.error(f"Error listing Google Sheets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing Google Sheets: {str(e)}"
        )

@router.get("/api/google/sheets/{sheet_id}/fields")
async def get_google_sheet_fields(
    sheet_id: str,
    current_user: dict = Depends(verify_token)
):
    """
    Get the fields (column headers) for a specific Google Sheet
    """
    try:
        user_id = current_user.get("user_id")
        credentials = await get_service_credentials(user_id, "google_sheets")
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google Sheets credentials not found"
            )
            
        fields = await google_service.get_sheet_columns(credentials, sheet_id)
        
        # Format field data
        formatted_fields = [{"name": field, "label": field} for field in fields]
        
        return formatted_fields
    except Exception as e:
        logger.error(f"Error getting Google Sheet fields: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting Google Sheet fields: {str(e)}"
        )

@router.get("/api/supabase/tables")
async def list_supabase_tables(current_user: dict = Depends(verify_token)):
    """
    List available Supabase tables for the current user
    """
    try:
        user_id = current_user.get("user_id")
        credentials = await get_service_credentials(user_id, "supabase")
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supabase credentials not found"
            )
            
        tables = await supabase_service.list_tables(credentials)
        return tables
    except Exception as e:
        logger.error(f"Error listing Supabase tables: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing Supabase tables: {str(e)}"
        )

@router.get("/api/supabase/tables/{table_name}/fields")
async def get_supabase_table_fields(
    table_name: str,
    current_user: dict = Depends(verify_token)
):
    """
    Get the fields (columns) for a specific Supabase table
    """
    try:
        user_id = current_user.get("user_id")
        credentials = await get_service_credentials(user_id, "supabase")
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supabase credentials not found"
            )
        
        # This would be implemented in the supabase_service
        fields = await get_supabase_table_schema(credentials, table_name)
        return fields
    except Exception as e:
        logger.error(f"Error getting Supabase table fields: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting Supabase table fields: {str(e)}"
        )

@router.get("/api/airtable/tables")
async def list_airtable_tables(current_user: dict = Depends(verify_token)):
    """
    List available Airtable bases and tables for the current user
    """
    try:
        user_id = current_user.get("user_id")
        credentials = await get_service_credentials(user_id, "airtable")
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Airtable credentials not found"
            )
        
        # This would be implemented in the airtable_service
        tables = await get_airtable_tables(credentials)
        return tables
    except Exception as e:
        logger.error(f"Error listing Airtable tables: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing Airtable tables: {str(e)}"
        )

@router.get("/api/airtable/tables/{table_id}/fields")
async def get_airtable_table_fields(
    table_id: str,
    current_user: dict = Depends(verify_token)
):
    """
    Get the fields for a specific Airtable table
    """
    try:
        user_id = current_user.get("user_id")
        credentials = await get_service_credentials(user_id, "airtable")
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Airtable credentials not found"
            )
        
        # This would be implemented in the airtable_service
        fields = await get_airtable_table_fields(credentials, table_id)
        return fields
    except Exception as e:
        logger.error(f"Error getting Airtable table fields: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting Airtable table fields: {str(e)}"
        )

# Helper functions
async def get_service_credentials(user_id: int, service_name: str):
    """
    Get credentials for a specific service and user
    """
    query = """
        SELECT credentials 
        FROM user_credentials 
        WHERE user_id = %s AND service_name = %s AND is_connected = TRUE
    """
    results = await db.execute(query, (user_id, service_name))
    
    if results and results[0].get("credentials"):
        return results[0]["credentials"]
    return None

def format_data_for_export(call_data, field_mapping):
    """
    Format call data based on field mapping for export
    """
    formatted_data = []
    
    for call in call_data:
        formatted_call = {}
        
        for source_field, dest_field in field_mapping.items():
            if not dest_field:
                # Skip fields that don't have a destination mapping
                continue
                
            # Handle nested fields (e.g., client_info.name)
            if '.' in source_field:
                parent_field, child_field = source_field.split('.', 1)
                
                # Check if parent field exists and is a dictionary
                if parent_field in call and isinstance(call[parent_field], dict):
                    parent_dict = call[parent_field]
                    
                    # Check if child field exists in parent dictionary
                    if child_field in parent_dict:
                        value = parent_dict[child_field]
                        
                        # Convert datetime objects to ISO string format
                        if isinstance(value, datetime):
                            formatted_call[dest_field] = value.isoformat()
                        else:
                            formatted_call[dest_field] = value
            
            # Handle regular fields
            elif source_field in call:
                # Convert datetime objects to ISO string format
                if isinstance(call[source_field], datetime):
                    formatted_call[dest_field] = call[source_field].isoformat()
                else:
                    formatted_call[dest_field] = call[source_field]
        
        formatted_data.append(formatted_call)
    
    return formatted_data

async def export_to_google_sheets(credentials, options, formatted_data):
    """
    Export data to Google Sheets
    """
    sheet_id = options.destination
    
    # For new sheets, create it first
    if options.create_new:
        # Create a new sheet with the specified name
        sheet_id = await google_service.create_sheet(credentials, options.destination)
        
        # Set up headers based on field mapping
        headers = []
        for source_field, dest_field in options.field_mapping.items():
            if dest_field:  # Only include mapped fields
                headers.append(dest_field)
                
        # Write headers to the first row
        await google_service.update_sheet_values(credentials, sheet_id, "A1", [headers])
        
        # Prepare row data
        row_data = []
        for item in formatted_data:
            row = [item.get(header, "") for header in headers]
            row_data.append(row)
            
        # Write data starting from second row
        if row_data:
            await google_service.update_sheet_values(credentials, sheet_id, "A2", row_data)
    else:
        # Existing sheet - append data
        # First get existing headers
        existing_headers = await google_service.get_sheet_columns(credentials, sheet_id)
        
        # Prepare row data
        row_data = []
        for item in formatted_data:
            row = [item.get(header, "") for header in existing_headers]
            row_data.append(row)
            
        # Append data to the sheet
        await google_service.append_sheet_values(credentials, sheet_id, row_data)
    
    return {
        "sheet_id": sheet_id,
        "rows_exported": len(formatted_data)
    }

async def export_to_supabase(credentials, options, formatted_data):
    """
    Export data to Supabase
    """
    table_name = options.destination
    
    # For new tables, create it first
    if options.create_new:
        # Create a schema based on field mapping
        schema = {}
        for source_field, dest_field in options.field_mapping.items():
            if dest_field:  # Only include mapped fields
                # Determine field type based on source field
                field_type = get_field_type_for_supabase(source_field)
                schema[dest_field] = field_type
                
        # Create the table
        await supabase_service.create_table(credentials, table_name, schema)
    
    # Insert data into the table
    rows_inserted = await supabase_service.insert_rows(credentials, table_name, formatted_data)
    
    return {
        "table_name": table_name,
        "rows_exported": rows_inserted
    }

async def export_to_airtable(credentials, options, formatted_data):
    """
    Export data to Airtable
    """
    table_id = options.destination
    
    # For new tables, create it first (if possible with Airtable API)
    if options.create_new:
        # Create a schema based on field mapping
        fields = []
        for source_field, dest_field in options.field_mapping.items():
            if dest_field:  # Only include mapped fields
                # Determine field type based on source field
                field_type = get_field_type_for_airtable(source_field)
                fields.append({
                    "name": dest_field,
                    "type": field_type
                })
                
        # Create the table - this requires Airtable API capabilities
        table_id = await create_airtable_table(credentials, options.destination, fields)
    
    # Insert data into the table
    rows_inserted = await insert_airtable_records(credentials, table_id, formatted_data)
    
    return {
        "table_id": table_id,
        "rows_exported": rows_inserted
    }

def get_field_type_for_supabase(field_name):
    """
    Determine appropriate Supabase field type based on field name
    """
    if field_name in ["start_time", "end_time", "created_at"]:
        return "timestamp"
    elif field_name in ["duration", "cost", "ultravox_cost"]:
        return "decimal"
    elif field_name == "transcription":
        return "text"
    else:
        return "varchar"

def get_field_type_for_airtable(field_name):
    """
    Determine appropriate Airtable field type based on field name
    """
    if field_name in ["start_time", "end_time", "created_at"]:
        return "dateTime"
    elif field_name in ["duration"]:
        return "number"
    elif field_name in ["cost", "ultravox_cost"]:
        return "currency"
    elif field_name == "transcription":
        return "multilineText"
    else:
        return "singleLineText"

async def setup_sync_job(current_user, options):
    """
    Set up a job to sync data in real-time
    """
    user_id = current_user.get("user_id")
    
    # Store sync configuration in the database
    query = """
        INSERT INTO data_sync_jobs (
            user_id, service, destination, field_mapping, 
            last_synced, is_active, created_at
        ) VALUES (%s, %s, %s, %s, NOW(), TRUE, NOW())
        ON DUPLICATE KEY UPDATE
            field_mapping = VALUES(field_mapping),
            is_active = TRUE,
            updated_at = NOW()
    """
    
    await db.execute(
        query, 
        (
            user_id, 
            options.service, 
            options.destination, 
            json.dumps(options.field_mapping)
        )
    )
    
    return True

# The functions below would be implemented in their respective service classes
# These are placeholder implementations

async def get_supabase_table_schema(credentials, table_name):
    """
    Get Supabase table schema (placeholder implementation)
    """
    # In a real implementation, this would query the Supabase API
    # to get the table schema
    # For now, return default fields
    default_fields = [
        {"name": "id", "type": "number", "label": "ID"},
        {"name": "call_sid", "type": "string", "label": "Call SID"},
        {"name": "from_number", "type": "string", "label": "From Number"},
        {"name": "to_number", "type": "string", "label": "To Number"},
        {"name": "direction", "type": "string", "label": "Direction"},
        {"name": "status", "type": "string", "label": "Status"},
        {"name": "start_time", "type": "datetime", "label": "Start Time"},
        {"name": "duration", "type": "number", "label": "Duration"},
        {"name": "cost", "type": "number", "label": "Cost"},
        {"name": "created_at", "type": "datetime", "label": "Created At"}
    ]
    
    return default_fields

async def get_airtable_tables(credentials):
    """
    Get Airtable tables (placeholder implementation)
    """
    # In a real implementation, this would query the Airtable API
    # to get the available bases and tables
    # For now, return default tables
    default_tables = [
        {"id": "tblcallhistory", "name": "Call History"},
        {"id": "tblcallanalytics", "name": "Call Analytics"}
    ]
    
    return default_tables

async def get_airtable_table_fields(credentials, table_id):
    """
    Get Airtable table fields (placeholder implementation)
    """
    # In a real implementation, this would query the Airtable API
    # to get the table fields
    # For now, return default fields
    default_fields = [
        {"name": "Call SID", "type": "singleLineText", "label": "Call SID"},
        {"name": "From", "type": "singleLineText", "label": "From Number"},
        {"name": "To", "type": "singleLineText", "label": "To Number"},
        {"name": "Direction", "type": "singleSelect", "label": "Direction"},
        {"name": "Status", "type": "singleSelect", "label": "Status"},
        {"name": "Start Time", "type": "dateTime", "label": "Start Time"},
        {"name": "Duration", "type": "number", "label": "Duration"},
        {"name": "Cost", "type": "currency", "label": "Cost"},
        {"name": "Created", "type": "dateTime", "label": "Created At"}
    ]
    
    return default_fields

async def create_airtable_table(credentials, table_name, fields):
    """
    Create Airtable table (placeholder implementation)
    """
    # In a real implementation, this would use the Airtable API
    # to create a new table with the specified fields
    # For now, just return a mock table ID
    return f"tbl{table_name.lower().replace(' ', '')}"

async def insert_airtable_records(credentials, table_id, records):
    """
    Insert records into Airtable (placeholder implementation)
    """
    # In a real implementation, this would use the Airtable API
    # to insert records into the specified table
    # For now, just return the number of records
    return len(records)
