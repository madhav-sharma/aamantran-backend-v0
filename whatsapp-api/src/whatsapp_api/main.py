import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .database import init_database
from .rest.whatsapp import router as whatsapp_router
from .rest.crud import router as crud_router
from .pages.guests import router as guests_page_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Wedding RSVP Management")

# Mount static files (CSS, JS, images, etc.)
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# Include routers
app.include_router(whatsapp_router)
app.include_router(crud_router)
app.include_router(guests_page_router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_database()
    logger.info("Application started")


# Simple route for the homepage
@app.get("/")
async def read_root():
    """Return welcome message"""
    return {"message": "Welcome to Wedding RSVP Management API"}

