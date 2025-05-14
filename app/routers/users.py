from fastapi import APIRouter, Depends
from ..dependencies import get_query_token

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(get_query_token)],
    responses={404: {"description": "Not found"}},
)

fake_users_db = {"johndoe": {"username": "johndoe"}, "alice": {"username": "alice"}}


@router.get("/")
async def read_users():
    return fake_users_db


@router.get("/{username}")
async def read_user(username: str):
    if username not in fake_users_db:
        return {"message": "User not found"}
    return {"username": username}
