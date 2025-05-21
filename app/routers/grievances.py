from fastapi import APIRouter, Depends, HTTPException, status
from ..dependencies import verify_token
from datetime import datetime
from xata.client import XataClient
from dotenv import load_dotenv
from ..models.grievance_models import GrievanceCreate, GrievanceUpdate, Grievance, STATUS_OPTIONS

load_dotenv()
xata = XataClient()

router = APIRouter(
    prefix="/grievances",
    tags=["grievances"],
    dependencies=[Depends(verify_token)],
    responses={404: {"description": "Not found"}},
)


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
        
        current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        grievance_data = {
            "description": grievance.description,
            "category": grievance.category,
            "priority": grievance.priority,
            "user_id": grievance.user_id,
            "status": "pending",
            "created_at": current_time,
            "updated_at": current_time,
            "grievance_received_date": current_time,
            "reformed_top_level_category": grievance.reformed_top_level_category,
            "reformed_last_level_category": grievance.reformed_last_level_category,
            "reformed_flag": grievance.reformed_flag
        }
        
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