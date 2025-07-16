# Wedding RSVP Management System - Design Document

## Overview

A simple, local Wedding RSVP Management application with WhatsApp integration for sending invitations and tracking delivery status.

### Key Principles
- **Simplicity**: Minimal features, no complex infrastructure
- **Local-first**: Runs on home PC without cloud dependencies
- **Clear separation**: Client-side format validation, server-side business logic validation

## Architecture

### Technology Stack
- **Backend**: FastAPI (Python)
- **Frontend**: HTML/CSS/JavaScript (Vanilla JS)
- **Database**: SQLite (local file)
- **Messaging**: WhatsApp Business API
- **Deployment**: Local development server

### Project Structure
```
whatsapp-api/
├── src/
│   ├── whatsapp_api/
│   │   ├── main.py          # FastAPI application
│   │   ├── database.py      # SQLite setup
│   │   ├── models.py        # Pydantic models
│   │   ├── guests.py        # Guest CRUD operations
│   │   └── rest/
│   │       └── whatsapp.py  # WhatsApp integration
│   ├── static/
│   │   ├── style.css        # Styling
│   │   └── script.js        # Frontend logic
│   └── templates/
│       └── index.html       # Main UI
└── wedding.db               # SQLite database
```

## Database Schema

### Guests Table
```sql
CREATE TABLE guests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prefix TEXT,                          -- Optional: Mr, Mrs, etc.
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    greeting_name TEXT,                   -- Free-form text, max 60 chars
    phone TEXT UNIQUE,                    -- E.164 format, unique constraint
    group_id TEXT NOT NULL,               -- Lowercase letters only
    is_group_primary BOOLEAN NOT NULL,
    ready BOOLEAN NOT NULL DEFAULT FALSE,
    sent_to_whatsapp TEXT DEFAULT 'pending',
    api_call_at DATETIME,
    sent_at DATETIME,
    delivered_at DATETIME,
    read_at DATETIME,
    message_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

### Logs Table
```sql
CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guest_id INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    type TEXT NOT NULL,
    payload TEXT NOT NULL,
    status TEXT,
    is_multiple BOOLEAN DEFAULT FALSE
)
```

## Validation Strategy

### Client-Side (Format Validation)
All format validation happens in the browser:

1. **Names (prefix, first_name, last_name)**:
   - Only letters (a-zA-Z)
   - Auto-capitalize (First letter upper, rest lower)
   - Required for first_name and last_name

2. **Greeting Name**:
   - Free-form text (any characters, spaces, capitalization)
   - Maximum 60 characters
   - Optional

3. **Phone Number**:
   - Must start with '+'
   - Accepts multiple country formats:
     - US/Canada (+1): 11 digits total
     - UK (+44): 13 digits total
     - India (+91): 13 digits total
     - UAE (+971): 13 digits total
     - Others: 8-15 digits total
   - Auto-formats for display
   - Required for primary contacts

4. **Group ID**:
   - Lowercase letters only (a-z)
   - Auto-converts to lowercase
   - Required

### Server-Side (Business Logic Validation)
Server only validates business rules:

1. **Phone Uniqueness**: Database constraint prevents duplicates
2. **Group Primary Rules**:
   - First member of a group must be primary
   - Only one primary per group
   - Primary must have phone number
3. **Data Immutability**: After creation, only `ready` field can be updated

## API Endpoints

### 1. GET /
Serves the main UI page

### 2. GET /guests
Returns all guests with computed phone color classes

### 3. POST /guests
Creates a new guest with business logic validation

### 4. PATCH /guests/{guest_id}
Updates only the ready status (all other fields immutable)

### 5. POST /send-invites
Sends WhatsApp messages to ready guests with phone numbers

### 6. GET/POST /webhook
WhatsApp webhook for delivery status updates

## User Interface

### Features
- **Guest Table**: Shows all guests with status tracking
- **Add Guest Form**: Real-time validation feedback
- **Ready Checkbox**: Auto-submits, disabled for guests without phones
- **Send Invites Button**: Triggers WhatsApp messages
- **Auto-refresh**: Table updates every 30 seconds

### Phone Color Coding
- India (+91): Orange background
- UAE (+971): Light yellow
- US/Canada (+1): Light blue
- UK (+44): Light green
- Others: Light gray

## WhatsApp Integration

### Message Flow
1. Mark guests as "ready"
2. Click "Send Invites"
3. System sends messages to ready guests with phones
4. Webhook receives status updates (sent/delivered/read)
5. UI displays delivery timestamps

### Configuration (.env)
```env
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_ACCESS_TOKEN=your_access_token
WEBHOOK_VERIFY_TOKEN=your_webhook_verify_token
WHATSAPP_TEMPLATE_NAME=your_template_name
WHATSAPP_LANGUAGE_CODE=en
WHATSAPP_API_VERSION=v18.0
```

## Key Design Decisions

1. **No SQLAlchemy ORM**: Uses direct SQLite for simplicity
2. **Client-side validation**: Reduces server complexity
3. **Immutable guest data**: Ensures webhook tracking integrity
4. **No bulk operations**: Simple one-at-a-time guest addition
5. **Local-only**: No authentication needed

## Future Enhancements (Out of Scope)
- RSVP response handling
- Message template editor
- Bulk import/export
- Guest editing (currently immutable)
- Cloud deployment