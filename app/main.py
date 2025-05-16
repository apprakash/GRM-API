from fastapi import FastAPI, Depends
from .dependencies import verify_token
from .routers import grievances, users
from .internal import admin

app = FastAPI()

# Include routers with their dependencies
app.include_router(users.router)
app.include_router(grievances.router)
app.include_router(
    admin.router,
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(verify_token)],
    responses={418: {"description": "I'm a teapot"}},
)


@app.get("/")
async def root():
    return {"message": "Welcome to GRM API!"}
