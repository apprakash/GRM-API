from fastapi import APIRouter, Depends, HTTPException, Body, status
from ..dependencies import get_query_token, get_token_header
from pydantic import BaseModel, Field, field_validator
import re
from xata.client import XataClient
from dotenv import load_dotenv

load_dotenv()
xata = XataClient()

router = APIRouter(
    prefix="/users",
    tags=["users"],
    # Removed router-level dependency to apply specific auth to endpoints
    responses={404: {"description": "Not found"}},
)

class UserBase(BaseModel):
    Name: str
    Email: str
    State: str
    Gender: str
    District: str
    Mobile: str

class User(UserBase):
    id: str
    status: str

class UserCreate(UserBase):
    @field_validator('Mobile')
    @classmethod
    def validate_mobile(cls, v):
        if not re.match(r'^\d{10}$', v):
            raise ValueError('Mobile number must be exactly 10 digits')
        return v
        
    @field_validator('Email')
    @classmethod
    def validate_email(cls, v):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_token_header)])
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
       print(resp)
       print("Record Id: %s" % resp["id"])
       return {"id": resp["id"], "status": "User created successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{user_id}", response_model=dict, dependencies=[Depends(get_query_token)])
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
