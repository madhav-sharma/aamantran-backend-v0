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
AIRTABLE_API_TOKEN = os.getenv("AIRTABLE_API_TOKEN")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = os.getenv("TABLE_NAME")


app = FastAPI()

# Set up Jinja templates (points to "templates" folder)
templates = Jinja2Templates(directory="src/templates")

# Mount static files (serves CSS/JS from "/static" URL)
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# Simple route for the homepage
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Render "index.html" from templates folder
    # Pass any data as a dict, like {"message": "Hello"}
    return templates.TemplateResponse("index.html", {"request": request, "message": "Welcome to my simple site!"})

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

@app.post("/send-template-message")
async def send_template_message() -> Dict[str, Any]:
    """
    Send a template message to a WhatsApp number

    Args:
        recipient: Phone number in international format
        template_name: Name of the WhatsApp template
        language_code: Language code for the template
        components: Optional template components

    Returns:
        Response from the WhatsApp API
    """
    recipient = "14373668209"
    template_name = "wedding_pre_invite"
    language_code = "en_US"
    components = None

    message_data = create_template_message(recipient, template_name, language_code, components)
    return await send_whatsapp_message(message_data)


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
