from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .dependencies import verify_token
from .routers import grievances, users
from .internal import admin
from .utils.grievance_utils import disconnect_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: No specific actions needed as client is lazily initialized
    yield
    # Shutdown: Disconnect the Weaviate client
    disconnect_client()


app = FastAPI(lifespan=lifespan)

# Configure CORS middleware to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

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
