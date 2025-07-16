# WhatsApp API Service

This directory contains the WhatsApp RSVP management service implementation.

## Quick Start

```bash
# Install dependencies
poetry install

# Configure environment
cp .env.example .env
# Edit .env with your WhatsApp API credentials

# Run the service
poetry run uvicorn src.whatsapp_api.main:app --reload --port 8000
```

## Structure

```
src/
├── whatsapp_api/     # Backend API
├── static/           # CSS and JavaScript
└── templates/        # HTML templates
```

## Documentation

For detailed documentation, see:
- [Main README](../README.md) - Usage guide and features
- [DESIGN.md](../DESIGN.md) - Technical design and architecture

## Environment Variables

Required in `.env`:
- `WHATSAPP_PHONE_NUMBER_ID`
- `WHATSAPP_ACCESS_TOKEN`
- `WEBHOOK_VERIFY_TOKEN`
- `WHATSAPP_TEMPLATE_NAME`
- `WHATSAPP_LANGUAGE_CODE`
- `WHATSAPP_API_VERSION`