"""Simple HTML endpoints extracted from ``main.py`` for cleanliness."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


def _generate_html_response() -> HTMLResponse:
    """Return a basic HTML page (placeholder)."""
    html_content = (
        "<html>"
        "<head><title>Some HTML in here</title></head>"
        "<body><h1>Look ma! HTML!</h1></body>"
        "</html>"
    )
    return HTMLResponse(content=html_content, status_code=200)


@router.get("/items/", response_class=HTMLResponse)
async def read_items() -> HTMLResponse:  # noqa: D401
    """Return the placeholder HTML page."""
    return _generate_html_response()
