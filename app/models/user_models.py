from pydantic import BaseModel, field_validator
import re

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

class UserResponse(BaseModel):
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
