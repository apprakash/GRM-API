from fastapi import APIRouter, Depends, HTTPException, status
from ..dependencies import verify_token
from datetime import datetime
from xata.client import XataClient
from dotenv import load_dotenv
from ..models.grievance_models import GrievanceCreate, GrievanceUpdate, FollowUpResponse, STATUS_OPTIONS
from ..utils.grievance_utils import process_grievance_category, generate_follow_up_questions

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

        # Process grievance category to get formatted fields and category information
        category_info = process_grievance_category(grievance.description)
        
        # Initialize follow-up questions and category data
        follow_up_questions = None
        
        # If we have a category match, get follow-up questions and update grievance data
        if category_info['top_category']:
            grievance_data["classified_category"] = category_info['classified_category']
            
            # Generate follow-up questions
            follow_up_questions = generate_follow_up_questions(
                grievance.description, 
                category_info['top_category'], 
                category_info['formatted_fields']
            )
            
            # If follow-up questions were generated successfully, store them
            if follow_up_questions:
                grievance_data["follow_up_questions"] = follow_up_questions.follow_up_questions
                grievance_data["missing_information"] = follow_up_questions.missing_information
                grievance_data["is_correct_category"] = follow_up_questions.is_correct_category

        # Insert the grievance with all the state information
        resp = xata.records().insert("Grievance", grievance_data)
        if not resp.is_success():
            print(f"Failed to create grievance: {resp}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create grievance",            
            )
            
        # Prepare the response with all relevant information
        response_data = {
            "id": resp["id"],
            "status": "Grievance created successfully",
        }
        
        # Include category information if available
        if category_info['top_category']:
            response_data.update({
                "required_info": category_info['formatted_fields'],
                "classified_category": category_info['classified_category'],
            })
            
            # Include follow-up questions if available
            if follow_up_questions:
                response_data["follow_up_questions"] = follow_up_questions.follow_up_questions
                response_data["is_correct_category"] = follow_up_questions.is_correct_category
                response_data["missing_information"] = follow_up_questions.missing_information
        
        return response_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )



@router.get("/{grievance_id}", response_model=dict)
async def get_grievance(grievance_id: str):
    """Get a grievance by its ID"""
    try:
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


@router.post("/{grievance_id}/follow-up", response_model=dict)
async def submit_follow_up(grievance_id: str, follow_up: FollowUpResponse):
    """Submit additional information in response to follow-up questions"""
    try:
        # First, get the existing grievance
        grievance_resp = xata.records().get("Grievance", grievance_id)
        if not grievance_resp.is_success():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grievance not found"
            )
        
        return {
            "status": "success",
            "grievance": grievance_resp
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