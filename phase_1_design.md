# Wedding RSVP Management: WhatsApp Chatbot Application

## Technical Design Document

### Version
V1.1 - Updated to incorporate timestamp-based webhook status tracking for sent, delivered, and read.

### Overview
This document outlines the technical design for a simple, local Wedding RSVP Management application using a WhatsApp chatbot. The application is designed for a single wedding (not a SaaS product), running on a home PC with no cloud dependencies, auto-scaling, or Docker. It uses FastAPI as the web framework, Jinja templates for the UI, SQLite as the database, and direct integration with the WhatsApp API for messaging. All operations are local, with logging for API interactions stored in the database.

Key goals:
- Simplicity: Minimal features, no complex infrastructure.
- Focus: Manage guest list, send pre-invite messages via WhatsApp, track delivery via webhooks, and visualize status in a UI table.
- Scope: V1 covers guest management, bulk-like addition (one-at-a-time with context), message sending, webhook processing, and basic logging. RSVP responses (e.g., buttons) are out of scope for this design.

### System Architecture
- **Backend**: FastAPI application serving API endpoints and Jinja-templated HTML pages.
- **Frontend/UI**: Simple HTML tables rendered via Jinja, with forms for adding guests and triggering sends. No JavaScript frameworks; basic HTML/CSS for UX (e.g., table with input row at bottom).
- **Database**: SQLite file (e.g., `wedding.db`) for storing guests and logs.
- **Messaging**: Direct WhatsApp Business API calls (using `requests` library or similar) for sending messages. Webhook endpoint in FastAPI to receive status updates (sent/delivered/read).
- **Background Tasks**: Use FastAPI's `BackgroundTasks` for processing webhooks (e.g., update DB statuses asynchronously).
- **Logging**: All WhatsApp API requests, responses, and webhooks stored in a dedicated DB table.
- **Deployment**: Run locally via `uvicorn` (e.g., `uvicorn main:app --reload`). Webhook exposure handled externally (e.g., ngrok/port forwarding—not covered in design).

No ORM (e.g., SQLAlchemy) specified; use direct `sqlite3` module with raw SQL for DB interactions. Use Pydantic for data validation where needed (e.g., guest models).

### Database Schema
Single SQLite database with two tables: `guests` and `logs`.

#### Guests Table
Stores guest information and invite status. Created with SQL like:
```sql
CREATE TABLE IF NOT EXISTS guests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    greeting_name TEXT,  -- Optional, used in message template if provided
    phone TEXT,  -- E.164 format (e.g., +1234567890), required for primaries and anyone receiving messages
    group_id TEXT NOT NULL,  -- User-assigned string (e.g., 'family-smith'), unique check at app level
    is_group_primary BOOLEAN NOT NULL,  -- True for primary contact in group
    ready BOOLEAN NOT NULL DEFAULT FALSE,  -- Flag to indicate ready for invite send
    sent_to_whatsapp TEXT DEFAULT 'pending',  -- 'pending' (default/initial), 'succeeded', 'failed'
    sent_at DATETIME,  -- NULL by default; set to timestamp on webhook receipt for 'sent'
    delivered_at DATETIME,  -- NULL by default; set to timestamp on webhook receipt for 'delivered'
    read_at DATETIME,  -- NULL by default; set to timestamp on webhook receipt for 'read'
    responded_with_button BOOLEAN DEFAULT FALSE,  -- Out of scope, but placeholder for future
    message_id TEXT,  -- WhatsApp message ID from successful send, for webhook matching
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```
- **Constraints/Validations** (handled at application level, not DB constraints for simplicity):
  - `first_name` and `last_name`: Required, non-empty strings.
  - `greeting_name`: Optional string.
  - `phone`: Required if `is_group_primary` is True; optional otherwise (non-primaries without phone won't receive messages). Validate as E.164 format (e.g., starts with '+', digits only).
  - `group_id`: Required non-empty string. App-level unique check: Ensure no duplicates across records (but allow multiple guests per group_id).
  - `is_group_primary`: 
    - For new group_id: Must be True (primary added first).
    - For existing group_id: Must be False, and ensure only one True per group_id.
  - `ready`: Defaults to False; user sets to True via UI (e.g., checkbox in table).
  - `sent_to_whatsapp`: Defaults to 'pending'. Updated after API send: 'succeeded' on 200 OK, 'failed' otherwise.
  - Webhook fields (`sent_at`, `delivered_at`, `read_at`): NULL initially. On webhook processing, set to the timestamp from the webhook (or CURRENT_TIMESTAMP if not provided) when the corresponding status is received. Presence of a timestamp indicates the event occurred.
  - Timestamps: `created_at` set on insert; `updated_at` updated on any change.
- Indexes: Add `INDEX ON group_id` and `INDEX ON message_id` for faster queries.

#### Logs Table
Stores WhatsApp API interactions for auditing. Created with SQL like:
```sql
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guest_id INTEGER,  -- FK to guests.id, nullable (NULL if can't link or multiple)
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    type TEXT NOT NULL,  -- 'request', 'response', 'webhook'
    payload TEXT NOT NULL,  -- JSON string of the full data
    status TEXT,  -- Quick ref, e.g., HTTP code or webhook status ('sent', 'delivered', 'read')
    is_multiple BOOLEAN DEFAULT FALSE  -- True if webhook/response affects multiple guests (no guest_id link)
);
```
- No strict FK constraint (to allow NULL guest_id).
- For bulk/multi webhooks: Set `guest_id` to NULL, `is_multiple` to True, store full payload for manual review.
- No UI for logs in V1 (out of scope); accessible via direct DB queries if needed.

### User Interface (UI)
- **Main Page**: `/` (GET) - Renders a Jinja template with:
  - A table displaying all guests from DB, columns: ID, First Name, Last Name, Greeting Name, Phone, Group ID, Is Primary (checkbox, read-only), Ready (editable checkbox), Sent to WA (text), Sent At (datetime or 'N/A'), Delivered At (datetime or 'N/A'), Read At (datetime or 'N/A'), Message ID.
  - Rows sorted by group_id then is_group_primary (descending).
  - At the bottom: Inline input fields for new guest (First Name, Last Name, Greeting Name, Phone, Group ID, Is Primary checkbox).
  - Button next to inputs: "Add Guest" (POST to `/add-guest`, validates, adds to DB, redirects to refresh page).
  - Another button: "Send Invites" (POST to `/send-invites`, scans for ready=True and sent_to_whatsapp='pending', sends messages).
  - UX: Table allows seeing all records while adding (no separate form). Use simple CSS for validation errors (e.g., red borders). Display 'N/A' or empty for NULL timestamps.
- **No Bulk Upload**: Addition feels "bulk-like" but is one-at-a-time with context (user sees previous for reference, e.g., to match group_ids).
- **Validation Feedback**: On add, if invalid (e.g., missing phone for primary), show error message above table and preserve inputs.

### API Endpoints (FastAPI)
- **GET /**: Render main Jinja template with guests data (query DB: `SELECT * FROM guests ORDER BY group_id, is_group_primary DESC`).
- **POST /add-guest**: 
  - Parse form data (first_name, etc.).
  - Validate fields and group rules (e.g., query DB for existing group_id, check primary rules).
  - If valid, insert into DB with raw SQL.
  - Redirect to `/`.
- **POST /send-invites**:
  - Query guests where ready=True and sent_to_whatsapp='pending'.
  - For each (loop synchronously, as simple/local):
    - If phone exists: Construct WhatsApp API request (hard-coded template with {name} = greeting_name or first_name).
    - Log request payload.
    - Send via `requests.post` to WhatsApp API.
    - Log response.
    - If 200: Update sent_to_whatsapp='succeeded', store message_id from response.
    - Else: 'failed'.
  - Redirect to `/`.
- **POST /webhook**: WhatsApp webhook endpoint (verify token as per API docs).
  - Receive payload (JSON).
  - Log full webhook as type='webhook', payload=JSON dump.
  - If multiple statuses: Set is_multiple=True, guest_id=NULL.
  - Else: Extract message_id, status (sent/delivered/read), and timestamp (if provided).
  - Query guests by message_id to find match.
  - Update corresponding _at field (e.g., sent_at = webhook_timestamp or CURRENT_TIMESTAMP) and updated_at.
  - If no match or multi: Log with NULL guest_id.
- **PATCH /update-ready/{guest_id}**: (If needed for checkbox updates; else handle via form in table.)

### Messaging Flow
- **Pre-Invite Send**: Hard-coded template (out of scope for details; e.g., "Dear {name}, ..."). Send only to guests with phone (primaries required to have one; non-primaries optional).
- **Webhook Processing**: Background task parses payload, matches via message_id, updates DB timestamps for sent_at, delivered_at, read_at. Store all in logs.
- **Tracking**: UI table shows timestamps (indicating occurrence); no auto-retries (manual via "Send Invites" button).

### Security/Edge Cases
- Local-only: No auth needed (assume single user).
- Validation: App-level for all rules to keep DB simple.
- Errors: Log failures; show in UI if critical.
- Data Integrity: Unique group_id check on add (query existing).

### Dependencies
- FastAPI
- Jinja2
- requests (for WhatsApp API)
- sqlite3 (built-in)

### Future Extensions (Out of Scope)
- RSVP button handling.
- Log viewing UI.
- Message template editor.
- Retries/auto-sends.
- Handling failed webhook statuses (e.g., add failed_at timestamp).

