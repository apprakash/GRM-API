from fastapi import APIRouter, Depends, HTTPException, Body, status
from ..dependencies import get_token_header
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from xata.client import XataClient
from dotenv import load_dotenv

load_dotenv()
xata = XataClient()

router = APIRouter(
    prefix="/grievances",
    tags=["grievances"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

# Grievance status options
STATUS_OPTIONS = ["pending", "in_progress", "resolved", "rejected"]


class GrievanceBase(BaseModel):
    title: str
    description: str
    category: str
    priority: str = Field(default="medium", description="Priority level: low, medium, high, critical")
    cpgrams_category: Optional[str] = None
    reformed_top_level_category: Optional[str] = None
    reformed_last_level_category: Optional[str] = None

class GrievanceCreate(GrievanceBase):
    user_id: str
    covid19_category: Optional[str] = None
    reformed_flag: Optional[bool] = False

class GrievanceUpdate(BaseModel):
    status: str
    resolution_notes: Optional[str] = None

class Grievance(GrievanceBase):
    id: str
    user_id: str
    status: str
    created_at: str
    updated_at: Optional[str] = None
    resolution_notes: Optional[str] = None
    grievance_received_date: Optional[str] = None
    grievance_closing_date: Optional[str] = None
    organisation_closing_date: Optional[str] = None
    org_status_date: Optional[str] = None
    reported_as_covid19_case_date: Optional[str] = None
    covid19_category: Optional[str] = None
    reformed_flag: Optional[bool] = False
    forwarded_to_subordinate: Optional[bool] = False
    forwarded_to_subordinate_details: Optional[str] = None
    rating: Optional[int] = None
    feedback: Optional[str] = None
    satisfaction_level: Optional[str] = None
    final_reply: Optional[str] = None
    appeal_no: Optional[str] = None
    appeal_date: Optional[str] = None
    appeal_reason: Optional[str] = None
    appeal_closing_date: Optional[str] = None
    appeal_closing_remarks: Optional[str] = None
    organisation_grievance_receive_date: Optional[str] = None
    organisation_grievance_close_date: Optional[str] = None
    officers_forwarding_grievance: Optional[str] = None
    date_of_receiving: Optional[str] = None
    officer_closed_by: Optional[str] = None
    final_status: Optional[str] = None

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_grievance(grievance: GrievanceCreate):
    """Create a new grievance in the Xata database"""
    
    try:
        # Verify that the user exists
        user_data = xata.records().get("Users", grievance.user_id)
        if not user_data.is_success():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Create the grievance record
        # Format datetime in RFC 3339 format as required by Xata
        current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        grievance_data = {
            "title": grievance.title,
            "description": grievance.description,
            "category": grievance.category,
            "priority": grievance.priority,
            "user_id": grievance.user_id,
            "status": "pending",
            "created_at": current_time,
            "updated_at": current_time,
            "grievance_received_date": current_time,
            # Removed covid19_category as it doesn't exist in the database
            "reformed_top_level_category": grievance.reformed_top_level_category,
            "reformed_last_level_category": grievance.reformed_last_level_category,
            "reformed_flag": grievance.reformed_flag
        }
        
        # cpgrams_category also needs to be a datetime in RFC 3339 format
        if grievance.cpgrams_category:
            # Using the same current_time for cpgrams_category as it also expects a datetime
            grievance_data["cpgrams_category"] = current_time
        
        resp = xata.records().insert("Grievance", grievance_data)
        print(resp)
        if not resp.is_success():
            print(resp)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create grievance"
            )
            
        return {
            "id": resp["id"],
            "status": "Grievance created successfully",
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{grievance_id}", response_model=dict)
async def get_grievance(grievance_id: str):
    """Get a grievance by its ID"""
    
    try:
        # Retrieve the grievance record
        resp = xata.records().get("Grievance", grievance_id)
        
        if not resp.is_success():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grievance not found"
            )
            
        return {
            "status": "success",
            "grievance": resp
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{grievance_id}", response_model=dict)
async def update_grievance_status(grievance_id: str, update_data: GrievanceUpdate):
    """Update the status of a grievance"""
    
    if update_data.status not in STATUS_OPTIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(STATUS_OPTIONS)}"
        )
    
    try:
        # Check if grievance exists
        grievance = xata.records().get("Grievances", grievance_id)
        if not grievance.is_success():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grievance not found"
            )
        
        # Update the grievance
        update_fields = {
            "status": update_data.status,
            "updated_at": datetime.now().isoformat()
        }
        
        if update_data.resolution_notes:
            update_fields["resolution_notes"] = update_data.resolution_notes
        
        resp = xata.records().update("Grievances", grievance_id, update_fields)
        if not resp.is_success():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update grievance"
            )
            
        return {
            "id": grievance_id,
            "status": "Grievance updated successfully",
            "updated_fields": update_fields
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )