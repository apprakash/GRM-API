from fastapi import APIRouter

router = APIRouter()

@router.post("/")
async def update_admin():
    return {"message": "Admin getting schwifty"}


@router.get("/")
async def read_admin():
    return {"message": "Admin only"}
