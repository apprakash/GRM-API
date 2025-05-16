from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# List of valid tokens (in a real application, this might be stored more securely)
VALID_TOKENS = [
    "token1",
    "token2",
    "token3",
    "fakesupersecrettoken"
]

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials not in VALID_TOKENS:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials
