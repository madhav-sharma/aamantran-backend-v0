from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["pages"])

# Set up Jinja templates - using absolute path from project root
templates = Jinja2Templates(directory="src/templates")


@router.get("/guests", response_class=HTMLResponse)
async def guests_page(request: Request):
    """Serve the guest management page"""
    return templates.TemplateResponse("index.html", {"request": request})