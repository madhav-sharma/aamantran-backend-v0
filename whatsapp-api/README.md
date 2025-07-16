# Wedding RSVP Management System

A simple, local Wedding RSVP Management application with WhatsApp integration for sending invitations and tracking delivery status.

## Features

- **Guest Management**: Add, update, and organize guests by groups
- **Group Organization**: Primary contacts system for family/group management
- **WhatsApp Integration**: Send pre-invite messages via WhatsApp Business API
- **Real-time Status Tracking**: Track sent, delivered, and read statuses via webhooks
- **Phone Validation**: Strict validation for UAE (+971) and India (+91) phone numbers
- **Auto-Submit Ready Status**: Quick checkbox updates without page refresh
- **Responsive UI**: Clean, simple interface that works on all devices

## Project Structure

```
whatsapp-api/
├── src/
│   ├── whatsapp_api/
│   │   ├── main.py          # FastAPI application and endpoints
│   │   ├── database.py      # SQLite database setup and connection
│   │   ├── models.py        # Pydantic models for validation
│   │   ├── guests.py        # Guest CRUD operations
│   │   └── rest/
│   │       └── whatsapp.py  # WhatsApp API integration
│   ├── static/
│   │   ├── style.css        # Application styling
│   │   └── script.js        # Frontend JavaScript logic
│   └── templates/
│       └── index.html       # Main UI template
├── pyproject.toml           # Poetry configuration
└── wedding.db               # SQLite database (created on first run)
```

## Setup Instructions

### 1. Prerequisites

- Python 3.8+
- Poetry (for dependency management)
- WhatsApp Business API access

### 2. Installation

```bash
# Clone the repository
cd whatsapp-api

# Install dependencies with Poetry
poetry install
```

### 3. Environment Configuration

Create a `.env` file in the `whatsapp-api` directory with your WhatsApp API credentials:

```env
# WhatsApp API Configuration
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_ACCESS_TOKEN=your_access_token
WEBHOOK_VERIFY_TOKEN=your_webhook_verify_token
WHATSAPP_TEMPLATE_NAME=your_template_name
WHATSAPP_LANGUAGE_CODE=en
WHATSAPP_API_VERSION=v18.0
```

### 4. Running the Application

```bash
# Start the development server
poetry run uvicorn src.whatsapp_api.main:app --reload --port 8000
```

The application will be available at `http://localhost:8000`

## Usage Guide

### Adding Guests

1. **First Guest in a Group**: Must be marked as "Primary Contact"
2. **Phone Requirements**: 
   - Required for primary contacts
   - Must start with '+' 
   - Supports only India (+91) and UAE (+971) numbers
   - Automatic formatting applied (e.g., +91-XXXXX-XXXXX)
3. **Group ID**: Use consistent naming (e.g., 'family-smith', 'friends-college')

### Managing Guests

- **Ready Status**: Check the "Ready" checkbox to mark guests for invitation
- **Edit**: Click "Edit" button to modify guest details (coming soon)
- **Phone Colors**: Different countries shown with different background colors

### Sending Invitations

1. Mark guests as "Ready" using the checkbox
2. Click "Send Invites to Ready Guests" button
3. Only guests with phone numbers will receive invitations
4. Track status in the table (Sent At, Delivered At, Read At)

## API Endpoints

- `GET /` - Main UI page
- `GET /guests` - Retrieve all guests
- `POST /guests` - Add a new guest
- `PATCH /guests/{guest_id}` - Update guest details
- `POST /send-invites` - Send WhatsApp invitations to ready guests
- `GET /webhook` - WhatsApp webhook verification
- `POST /webhook` - Receive WhatsApp status updates

## Database Schema

### Guests Table
- Stores guest information and invitation status
- Tracks WhatsApp message delivery status
- Maintains group relationships

### Logs Table
- Records all WhatsApp API interactions
- Useful for debugging and auditing

## WhatsApp Webhook Setup

To receive delivery status updates, configure your WhatsApp webhook URL:

```
https://your-domain.com/webhook
```

For local development, use ngrok or similar:
```bash
ngrok http 8000
```

## Troubleshooting

### Common Issues

1. **"Phone number already exists"**: Each phone number must be unique
2. **"First member of a group must be primary"**: Always add the primary contact first
3. **WhatsApp API errors**: Check your `.env` configuration and API credentials

### Logs

Check the application logs for detailed error messages:
```bash
# View server logs in the terminal where uvicorn is running
```

## Development Notes

- Database is created automatically on first run
- Guest table refreshes every 30 seconds to show webhook updates
- All timestamps are stored in UTC
- Phone numbers are stored in E.164 format without formatting

## Future Enhancements

- Guest editing functionality
- RSVP response handling
- Message template customization
- Bulk import from CSV
- Export guest list
- Advanced filtering and search
