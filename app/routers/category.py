from fastapi import APIRouter, Depends, HTTPException, status
from ..dependencies import verify_token
from ..utils.grievance_utils import process_grievance_category
from pydantic import BaseModel

# Define the request model
class GrievanceCategoryRequest(BaseModel):
    grievance_text: str

# Define the router with authentication dependency
router = APIRouter(
    prefix="/category",
    tags=["category"],
    dependencies=[Depends(verify_token)],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=dict)
async def categorize_grievance(request: GrievanceCategoryRequest):
    """
    Categorize a grievance text and return category information.
    
    This endpoint processes the provided grievance text and returns:
    - Matched categories with confidence scores
    - Top matching category
    - Required form fields for the top category
    - Classified category path
    """
    try:
        # Process the grievance text to get category information
        category_info = process_grievance_category(request.grievance_text)
        
        # Return the category information
        return {
            "status": "success",
            "categories": category_info.get('categories', []),
            "top_category": category_info.get('top_category'),
            "formatted_fields": category_info.get('formatted_fields', ""),
            "classified_category": category_info.get('classified_category', "")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )