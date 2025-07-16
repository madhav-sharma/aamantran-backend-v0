# Wedding RSVP Management System

A simple, local Wedding RSVP Management application with WhatsApp integration for sending invitations and tracking delivery status.

## Features

- **Guest Management**: Add and organize guests by groups
- **Group Organization**: Primary contacts system for family/group management
- **WhatsApp Integration**: Send pre-invite messages via WhatsApp Business API
- **Real-time Status Tracking**: Track sent, delivered, and read statuses via webhooks
- **Smart Validation**: Client-side format validation with server-side business rules
- **Phone Number Support**: Multiple country formats with visual color coding
- **Auto-Submit Ready Status**: Quick checkbox updates without page refresh
- **Responsive UI**: Clean, simple interface that works on all devices

## Quick Start

### Prerequisites

- Python 3.8+
- Poetry (for dependency management)
- WhatsApp Business API access

### Installation

```bash
# Clone the repository
cd whatsapp-api

# Install dependencies with Poetry
poetry install
```

### Configuration

Create a `.env` file in the `whatsapp-api` directory:

```env
# WhatsApp API Configuration
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_ACCESS_TOKEN=your_access_token
WEBHOOK_VERIFY_TOKEN=your_webhook_verify_token
WHATSAPP_TEMPLATE_NAME=your_template_name
WHATSAPP_LANGUAGE_CODE=en
WHATSAPP_API_VERSION=v18.0
```

### Running the Application

```bash
# Start the development server
poetry run uvicorn src.whatsapp_api.main:app --reload --port 8000
```

The application will be available at `http://localhost:8000`

## Usage Guide

### Adding Guests

1. **First Guest in a Group**: Must be marked as "Primary Contact"
2. **Required Fields**:
   - First Name & Last Name (letters only, auto-capitalized)
   - Group ID (lowercase letters only, auto-converted)
   - Phone (required for primary contacts)
3. **Optional Fields**:
   - Prefix (Mr, Mrs, etc.)
   - Greeting Name (free-form text, max 60 characters)
   - Phone (for non-primary contacts)

### Phone Number Formats

The system accepts international formats:
- **US/Canada**: +1 (10 digits) → +1-XXX-XXX-XXXX
- **UK**: +44 (10 digits) → +44-XXXX-XXX-XXX
- **India**: +91 (10 digits) → +91-XXXXX-XXXXX
- **UAE**: +971 (9 digits) → +971-XX-XXX-XXXX
- **Others**: Any valid E.164 format (8-15 digits)

### Managing Guests

- **Ready Status**: Check the checkbox to mark guests for invitation
  - Disabled for guests without phone numbers
  - Auto-saves on change
- **Group Organization**: Guests are sorted by group, with primaries first
- **Phone Colors**: Different countries shown with different background colors
  - 🟧 Orange: India (+91)
  - 🟨 Light Yellow: UAE (+971)
  - 🟦 Light Blue: US/Canada (+1)
  - 🟩 Light Green: UK (+44)
  - ⬜ Light Gray: Other countries

### Sending Invitations

1. Mark guests as "Ready" using the checkbox
2. Click "Send Invites to Ready Guests" button
3. Only guests with phone numbers will receive invitations
4. Track status in real-time:
   - Sent At: Message sent to WhatsApp
   - Delivered At: Message delivered to recipient
   - Read At: Message read by recipient

## API Reference

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/` | GET | Main UI page |
| `/guests` | GET | Retrieve all guests |
| `/guests` | POST | Add a new guest |
| `/guests/{id}` | PATCH | Update ready status |
| `/send-invites` | POST | Send WhatsApp invitations |
| `/webhook` | GET/POST | WhatsApp webhook |

## Validation Rules

### Client-Side (Format)
- **Names**: Letters only, auto-capitalized
- **Greeting**: Any text, max 60 characters
- **Phone**: Valid E.164 format with country code
- **Group ID**: Lowercase letters only

### Server-Side (Business Logic)
- Phone numbers must be unique
- First member of a group must be primary
- Primary contacts must have phone numbers
- Guest data is immutable (except ready status)

## WhatsApp Webhook Setup

For local development with webhooks:

```bash
# Use ngrok or similar
ngrok http 8000

# Configure webhook URL in WhatsApp Business API
https://your-domain.ngrok.io/webhook
```

## Troubleshooting

### Common Issues

1. **"Phone number already exists"**
   - Each phone number must be unique across all guests

2. **"First member of a group must be primary"**
   - Always add the primary contact before other group members

3. **"Primary guest must have a phone number"**
   - Primary contacts require phone numbers for group communication

4. **WhatsApp API errors**
   - Verify your `.env` configuration
   - Check API credentials and template name
   - Ensure phone numbers are in correct format

### Development Notes

- Database (`wedding.db`) is created automatically on first run
- Guest table refreshes every 30 seconds for webhook updates
- All timestamps are stored in UTC
- Phone numbers are stored in E.164 format without formatting

## Technical Details

See [DESIGN.md](DESIGN.md) for detailed technical documentation including:
- System architecture
- Database schema
- Validation strategy
- API specifications
- Design decisions

## License

This project is for personal use. Feel free to adapt for your own events.