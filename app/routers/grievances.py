from fastapi import APIRouter, Depends, HTTPException, status
from ..dependencies import verify_token
from datetime import datetime
from xata.client import XataClient
from dotenv import load_dotenv
from ..models.grievance_models import GrievanceCreate, GrievanceUpdate, STATUS_OPTIONS


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
    """Create a new grievance in the Xata database with only required fields"""
    
    try:
        user_data = xata.records().get("Users", grievance.user_id)
        if not user_data.is_success():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        # Start with required fields
        grievance_data = {
            "title": grievance.title,
            "description": grievance.description,
            "category": grievance.category,
            "priority": grievance.priority,
            "user_id": grievance.user_id,
            "status": "pending",
            "created_at": current_time,
            "updated_at": current_time,
            "grievance_received_date": current_time
        }
        
        if grievance.cpgrams_category is not None:
            grievance_data["cpgrams_category"] = grievance.cpgrams_category
        
        # Add optional fields if they are provided
        if grievance.reformed_top_level_category is not None:
            grievance_data["reformed_top_level_category"] = grievance.reformed_top_level_category
            
        if grievance.reformed_last_level_category is not None:
            grievance_data["reformed_last_level_category"] = grievance.reformed_last_level_category
            
        if grievance.reformed_flag is not None:
            grievance_data["reformed_flag"] = grievance.reformed_flag

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
            "title": grievance.title,
            "description": grievance.description,
            "priority": grievance.priority,
            "user_id": grievance.user_id,
            "cpgrams_category": grievance.cpgrams_category,
        }
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
        grievance = xata.records().get("Grievance", grievance_id)
        if not grievance.is_success():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grievance not found"
            )
        
        # Update the grievance
        # Format datetime in RFC 3339 format with Z suffix for UTC
        current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        
        update_fields = {
            "status": update_data.status,
            "final_status": update_data.status,
            "officer_closed_by": update_data.officer_closed_by,
            "grievance_closing_date": current_time,
            "updated_at": current_time
        }
        
        resp = xata.records().update("Grievance", grievance_id, update_fields)
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


@router.get("/user/{user_id}", response_model=dict)
async def get_user_grievances(user_id: str, fetch_all: bool = True, page: int = 1, size: int = 10):
    """Get all grievances linked to a specific user ID"""
    try:
        # Check if user exists
        user_data = xata.records().get("Users", user_id)
        if not user_data.is_success():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        all_records = []
        
        if fetch_all:
            current_page = 0
            has_more = True
            
            while has_more:
                query = {
                    "filter": {
                        "user_id": user_id
                    },
                    "page": {
                        "size": size,
                        "offset": current_page * size
                    }
                }
                
                resp = xata.data().query("Grievance", query)
                
                if not resp.is_success():
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to fetch grievances"
                    )
                
                records = resp.get("records", [])
                all_records.extend(records)
                
                has_more = len(records) == size
                current_page += 1
        else:
            # Just get the requested page
            query = {
                "filter": {
                    "user_id": user_id
                },
                "page": {
                    "size": size,
                    "offset": (page - 1) * size
                }
            }
            
            resp = xata.data().query("Grievance", query)
            
            if not resp.is_success():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch grievances"
                )
                
            all_records = resp.get("records", [])
        
        # Get total count of grievances for this user (without pagination)
        count_query = {
            "filter": {
                "user_id": user_id
            }
        }
        total_resp = xata.data().aggregate("Grievance", {
            "aggs": {
                "total_count": {
                    "count": {}
                }
            },
            "filter": count_query["filter"]
        })
        
        total_count = total_resp.get("aggs", {}).get("total_count", 0) if total_resp.is_success() else 0
        
        response = {
            "status": "success",
            "user_id": user_id,
            "grievances": all_records,
            "total": total_count
        }
        
        # Add pagination info if not fetching all records
        if not fetch_all:
            response.update({
                "page": page,
                "size": size,
                "totalPages": (total_count + size - 1) // size if size > 0 else 0
            })
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )