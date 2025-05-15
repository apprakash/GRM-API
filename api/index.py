from fastapi import FastAPI
import uvicorn
import sys
import os

# Add the parent directory to sys.path to make the app module importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the FastAPI app from the main module
from app.main import app

# This is necessary for Vercel serverless deployment
# The app variable will be used by the Vercel Python runtime
