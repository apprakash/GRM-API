from fastapi import APIRouter, Depends, HTTPException, status
from ..dependencies import verify_token
from ..utils.grievance_utils import process_grievance_category, fetch_faqs
from ..models.grievance_models import GrievanceCategoryRequest, FAQRequest, FAQResponse

# Request model is now imported from grievance_models.py
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


@router.post("/faq", response_model=FAQResponse)
async def get_faq_information(request: FAQRequest):
    """
    Retrieve FAQ information based on a search query.
    
    This endpoint searches for relevant FAQ items using the provided query and returns:
    - A list of FAQ items with their id, code, question, and answer
    - The total count of returned FAQ items
    
    The number of returned items can be limited using the 'limit' parameter (default: 5)
    """
    try:
        # Fetch FAQ items based on the query
        faq_items = fetch_faqs(request.query, request.limit)
        
        # Return the FAQ information
        return {
            "status": "success",
            "faqs": faq_items,
            "count": len(faq_items)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )