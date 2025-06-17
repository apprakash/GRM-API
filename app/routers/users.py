from fastapi import APIRouter, Depends, HTTPException, status
from ..dependencies import verify_token
from xata.client import XataClient
from dotenv import load_dotenv
from ..models.user_models import UserResponse, UserCreate

load_dotenv()
xata = XataClient()

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(verify_token)],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    """Create a new user in the Xata database with validation"""

    try:
       resp = xata.records().insert("Users", {
        "Name": user.Name,
        "Email": user.Email,
        "State": user.State,
        "Gender": user.Gender,
        "District": user.District,
        "Mobile": user.Mobile
       })
       assert resp.is_success()
       return {"id": resp["id"], "status": "User created successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{user_id}", response_model=dict)
async def get_user(user_id: str):
    """Get a user by ID from the Xata database"""
    
    try:
        user_data = xata.records().get("Users", user_id)
        if not user_data.is_success():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        return {
            "id": user_id,
            "Name": user_data.get("Name", ""),
            "Email": user_data.get("Email", ""),
            "State": user_data.get("State", ""),
            "Gender": user_data.get("Gender", ""),
            "District": user_data.get("District", ""),
            "Mobile": user_data.get("Mobile", ""),
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
