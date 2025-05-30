from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Unkey API configuration
UNKEY_API_URL = os.getenv("UNKEY_API_URL")
UNKEY_API_ID = os.getenv("UNKEY_API_ID") 

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    key = credentials.credentials
    
    payload = {
        "apiId": UNKEY_API_ID,
        "key": key
    }
    
    try:
        response = requests.post(UNKEY_API_URL, json=payload)
        response_data = response.json()
        
        # Check if the key is valid
        if response.status_code == 200 and response_data.get("valid", False):
            return key
        else:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception as e:
        # Handle any exceptions during API call
        raise HTTPException(
            status_code=500,
            detail=f"Authentication service error: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
