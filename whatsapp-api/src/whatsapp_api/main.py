import os
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, HTTPException

import aiohttp

from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

WHATSAPP_API_BASE_URL = "https://graph.facebook.com"
WHATSAPP_API_VERSION = "v23.0"

load_dotenv(dotenv_path='/Users/madhavsharma/dotenv/aamantran.env')
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN")
TABLE_NAME = os.getenv("TABLE_NAME")


from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="local_secret")

# Set up Jinja templates (points to "templates" folder)
templates = Jinja2Templates(directory="src/templates")

# Register custom filter for phone formatting


# Mount static files (serves CSS/JS from "/static" URL)
app.mount("/static", StaticFiles(directory="src/static"), name="static")

from . import db
from .models import GuestIn
from .rest.api import create_template_message, send_whatsapp_message
from .rest.webhook import router as whatsapp_router
from .views.html import router as html_router

# Include routers from sub packages
app.include_router(whatsapp_router)
app.include_router(html_router)
import sqlite3

def fetch_guests():
    conn = db.get_connection()
    c = conn.cursor()
    guests = c.execute("SELECT * FROM guests ORDER BY group_id, is_group_primary DESC").fetchall()
    columns = [desc[0] for desc in c.description]
    country_code_colors = {
        '1': 'cc-usacan',    # USA/Canada
        '971': 'cc-uae',    # UAE
        '44': 'cc-uk',      # UK
        '91': 'cc-in',      # India
    }
    def get_phone_class(phone):
        if not phone or not phone.startswith('+'):
            return ''
        # Try 3, 2, then 1 digit country code
        for length in (3, 2, 1):
            prefix = phone[1:1+length]
            if prefix in country_code_colors:
                return country_code_colors[prefix]
        return 'cc-other'
    guest_dicts = []
    for row in guests:
        d = dict(zip(columns, row))
        d['phone_class'] = get_phone_class(d.get('phone'))
        guest_dicts.append(d)
    conn.close()
    return guest_dicts


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, error: str = "", form_data: dict = None, errors: list = None):
    guests = fetch_guests()
    # Check session for preserved add form data
    session_form = request.session.get("add_form_data") if hasattr(request, "session") else None
    if session_form and not form_data:
        form_data = session_form
    # Note: Do not clear session data here. The preserved form data will be cleared
    #       explicitly after a successful guest addition inside add_guest().

    return templates.TemplateResponse("index.html", {"request": request, "guests": guests, "error": error, "form_data": form_data or {}, "errors": errors or []})

@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    Webhook verification endpoint for WhatsApp
    """
    print(request)
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
        print("Webhook verified successfully!")
        return Response(content=challenge, media_type="text/plain")
    else:
        print("Webhook verification failed!")
        return Response(content="Forbidden", status_code=403)

@app.post("/webhook")
async def handle_webhook(request: Request):
    print(request)
    data = await request.json()
    print(data)
    return Response(content="OK", status_code=200)

def create_template_message(
        recipient: str,
        template_name: str,
        language_code: str = "en_US",
        components: Optional[list] = None
) -> Dict[str, Any]:
    """
    Create a template message payload

    Args:
        recipient: Phone number in international format
        template_name: Name of the WhatsApp template
        language_code: Language code for the template (default: "en_US")
        components: Optional template components (parameters, buttons, etc.)

    Returns:
        Message payload dictionary
    """
    message = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {
                "code": language_code
            }
        }
    }

    if components:
        message["template"]["components"] = components

    return message


async def send_whatsapp_message(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a message via WhatsApp Business API

    Args:
        data: The message payload as a dictionary

    Returns:
        Response from the WhatsApp API
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
    }

    url = f"{WHATSAPP_API_BASE_URL}/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=data, headers=headers) as response:
                response_data = await response.json()

                if response.status == 200:
                    print(f"Message sent successfully: {response_data}")
                    return {"status": "success", "data": response_data}
                else:
                    print(f"Error sending message. Status: {response.status}")
                    print(f"Response: {response_data}")
                    return {"status": "error", "code": response.status, "data": response_data}

        except aiohttp.ClientConnectorError as e:
            print(f"Connection Error: {str(e)}")
            return {"status": "error", "message": f"Connection error: {str(e)}"}
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return {"status": "error", "message": f"Unexpected error: {str(e)}"}

from fastapi import Form
from fastapi.responses import RedirectResponse

@app.post("/add-guest")
async def add_guest(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    greeting_name: str = Form(None),
    phone: str = Form(None),
    group_id: str = Form(...),
    is_group_primary: str = Form(None)  # Checkbox returns 'true' or None
):
    # Parse checkbox
    is_primary_val = is_group_primary == "true"
    form_data = {
        "first_name": first_name,
        "last_name": last_name,
        "greeting_name": greeting_name,
        "phone": phone,
        "group_id": group_id,
        "is_group_primary": is_primary_val
    }
    errors = []
    # Validate using Pydantic
    try:
        guest_in = GuestIn(
            first_name=first_name,
            last_name=last_name,
            greeting_name=greeting_name,
            phone=phone,
            group_id=group_id,
            is_group_primary=is_primary_val
        )
    except Exception as e:
        errors.append(str(e))
        request.session["add_form_data"] = form_data
        guests = fetch_guests()
        return templates.TemplateResponse("index.html", {"request": request, "guests": guests, "form_data": form_data, "errors": errors})
    # App-level validation
    conn = db.get_connection()
    c = conn.cursor()
    # Phone uniqueness check
    if phone:
        phone_count = c.execute("SELECT COUNT(*) FROM guests WHERE phone = ?", (phone,)).fetchone()[0]
        if phone_count > 0:
            errors.append("Phone number already exists for another guest.")
    group_primaries = c.execute("SELECT COUNT(*) FROM guests WHERE group_id = ? AND is_group_primary = 1", (group_id,)).fetchone()[0]
    if is_primary_val and group_primaries > 0:
        errors.append("Primary already exists for this group_id.")
    if not is_primary_val and group_primaries == 0:
        errors.append("Primary must be added first for a new group_id.")
    if errors:
        request.session["add_form_data"] = form_data
        conn.close()
        guests = fetch_guests()
        return templates.TemplateResponse("index.html", {"request": request, "guests": guests, "form_data": form_data, "errors": errors})
    # Insert guest
    c.execute("""
        INSERT INTO guests (first_name, last_name, greeting_name, phone, group_id, is_group_primary, ready)
        VALUES (?, ?, ?, ?, ?, ?, 0)
    """, (first_name, last_name, greeting_name, phone, group_id, int(is_primary_val)))
    conn.commit()
    conn.close()
    # Clear preserved form data after a successful insert, if any
    if hasattr(request, "session"):
        request.session.pop("add_form_data", None)
    return RedirectResponse(url="/", status_code=303)

@app.post("/send-invites")
async def send_invites(request: Request):
    # Stub for now: just redirect
    return RedirectResponse(url="/", status_code=303)

@app.post("/update-ready/{guest_id}")
async def update_ready(request: Request, guest_id: int):
    form = await request.form()
    ready_val = 1 if form.get("ready") == "on" else 0
    # Validate guest exists
    conn = db.get_connection()
    c = conn.cursor()
    exists = c.execute("SELECT 1 FROM guests WHERE id = ?", (guest_id,)).fetchone()
    if exists:
        c.execute("UPDATE guests SET ready = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (ready_val, guest_id))
        conn.commit()
    conn.close()
    # Preserve add_form_data in session if present
    if hasattr(request, "session") and "add_form_data" in request.session:
        pass  # Already preserved
    return RedirectResponse(url="/", status_code=303)


def generate_html_response():
    html_content = """
    <html>
        <head>
            <title>Some HTML in here</title>
        </head>
        <body>
            <h1>Look ma! HTML!</h1>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)


@app.get("/items/", response_class=HTMLResponse)
async def read_items():
    return generate_html_response()
