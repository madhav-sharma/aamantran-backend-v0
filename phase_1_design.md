# Wedding RSVP Management: WhatsApp Chatbot Application

## Technical Design Document

### Version
V1.5 - Enhanced phone number validation in Appendix C for tighter browser-side checks: immediate flagging for missing '+' prefix or non-numeric characters, strict enforcement of UAE/India formats without auto-adding '+', and prevention of submission if invalid.

### Overview
This document outlines the technical design for a simple, local Wedding RSVP Management application using a WhatsApp chatbot. The application is designed for a single wedding (not a SaaS product), running on a home PC with no cloud dependencies, auto-scaling, or Docker. It uses FastAPI as the web framework, Jinja templates for initial UI serving (with JS enhancements), SQLite as the database, and direct integration with the WhatsApp API for messaging. All operations are local, with logging for API interactions stored in the database.

Key goals:
- Simplicity: Minimal features, no complex infrastructure.
- Focus: Manage guest list, send pre-invite messages via WhatsApp, track delivery via webhooks, and visualize status in a UI table.
- Scope: V1 covers guest management, bulk-like addition (one-at-a-time with context), message sending, webhook processing, and basic logging. RSVP responses (e.g., buttons) are out of scope for this design.

### System Architecture
- **Backend**: FastAPI application serving REST API endpoints and an initial Jinja-templated HTML page.
- **Frontend/UI**: Responsive web app using HTML/CSS with JavaScript (vanilla JS or lightweight like React if desired) for dynamic interactions. JS handles form submissions via REST API calls (e.g., fetch or XMLHttpRequest), table updates, and real-time feedback. No pure form submissions; use JS to send data to APIs and update UI dynamically.
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
  - `phone`: Required if `is_group_primary` is True; optional otherwise (non-primaries without phone won't receive messages). Validate as E.164 format restricted to +91 (India, 10 digits) or +971 (UAE, 9 digits) (e.g., starts with '+', specific lengths). Additional uniqueness check as per Appendix C. Store clean without dashes or formatting.
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
- **Main Page**: `/` (GET) - Serves a Jinja template with an HTML structure, including a table placeholder, input fields for adding guests, and buttons. JS script fetches guest data via API (GET /guests), populates the table dynamically, and handles interactions.
  - Table: Displays all guests, columns: ID, First Name, Last Name, Greeting Name, Phone (with color class as per Appendix C; display with human-readable formatting via JS), Group ID, Is Primary (read-only), Ready (editable checkbox with auto-submit via JS as per Appendix B), Sent to WA (text), Sent At (datetime or 'N/A'), Delivered At (datetime or 'N/A'), Read At (datetime or 'N/A'), Message ID.
  - Rows sorted by group_id then is_group_primary (descending) via JS or API query.
  - Add Guest: Input fields (First Name, Last Name, Greeting Name, Phone (with id="phone-input" and <span id="phone-error"></span> for validation as per Appendix C), Group ID, Is Primary checkbox). JS handles "Add Guest" button click: Validates locally (including strict phone checks via JS, preventing submission if invalid), sends POST to /guests via fetch if valid, refreshes table on success, shows error message if failed.
  - Send Invites: Button triggers JS to call POST /send-invites, then refreshes table.
  - UX: Dynamic updates without full page reloads. Use CSS for validation errors (e.g., red borders). Display 'N/A' or empty for NULL timestamps. Inline JS for phone debouncing/formatting and ready auto-submit.
- **No Bulk Upload**: Addition feels "bulk-like" but is one-at-a-time with context (user sees previous for reference, e.g., to match group_ids).
- **Validation Feedback**: JS provides client-side feedback; server returns JSON errors on API calls (e.g., { "error": "Invalid phone" }), displayed via JS alerts or inline.

### API Endpoints (FastAPI)
- **GET /guests**: Return JSON list of all guests (query DB: `SELECT * FROM guests ORDER BY group_id, is_group_primary DESC`). Compute phone_class for each guest (as per Appendix C).
- **POST /guests**: 
  - Parse JSON body (first_name, etc.). Strip any formatting from phone (e.g., remove dashes) before validation/storage.
  - Validate fields, group rules (e.g., query DB for existing group_id, check primary rules), phone uniqueness and format (as per Appendix C).
  - If valid, insert into DB with raw SQL. Return 201 Created with guest data on success; 400 with JSON error on failure.
- **POST /send-invites**:
  - Query guests where ready=True and sent_to_whatsapp='pending'.
  - For each (loop synchronously, as simple/local):
    - If phone exists: Construct WhatsApp API request (hard-coded template with {name} = greeting_name or first_name).
    - Log request payload.
    - Send via `requests.post` to WhatsApp API.
    - Log response.
    - If 200: Update sent_to_whatsapp='succeeded', store message_id from response.
    - Else: 'failed'.
  - Return 200 OK on completion.
- **POST /webhook**: WhatsApp webhook endpoint (verify token as per API docs).
  - Receive payload (JSON).
  - Log full webhook as type='webhook', payload=JSON dump.
  - If multiple statuses: Set is_multiple=True, guest_id=NULL.
  - Else: Extract message_id, status (sent/delivered/read), and timestamp (if provided).
  - Query guests by message_id to find match.
  - Update corresponding _at field (e.g., sent_at = webhook_timestamp or CURRENT_TIMESTAMP) and updated_at.
  - If no match or multi: Log with NULL guest_id.
  - Return 200 OK.
- **PATCH /guests/{guest_id}**: Update fields like ready (JSON body: {"ready": true}). Return 200 OK on success.

### Messaging Flow
- **Pre-Invite Send**: Hard-coded template (out of scope for details; e.g., "Dear {name}, ..."). Send only to guests with phone (primaries required to have one; non-primaries optional).
- **Webhook Processing**: Background task parses payload, matches via message_id, updates DB timestamps for sent_at, delivered_at, read_at. Store all in logs.
- **Tracking**: UI table shows timestamps (indicating occurrence); no auto-retries (manual via "Send Invites" button).

### Security/Edge Cases
- Local-only: No auth needed (assume single user).
- Validation: App-level for all rules to keep DB simple.
- Errors: Log failures; return JSON errors for UI display.
- Data Integrity: Unique group_id check on add (query existing); phone uniqueness as per Appendix C.

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

### Appendix B: Implementing the Ready Update with Auto-Submit

This appendix provides guidance for enhancing the 'ready' field update mechanism using the PATCH /guests/{guest_id} endpoint. The goal is to enable auto-submission when ticking the 'ready' checkbox in the UI table. This builds on the existing design without altering core requirements, using JS for dynamic updates.

#### Rationale
- **Auto-Submit on Tick**: Users can click the 'ready' checkbox in a table row, triggering an immediate update without a separate "Save" button, improving UX for quick flagging.

#### Implementation Approach
1. **Endpoint Setup**:
   - PATCH /guests/{guest_id}:
     - Extract `guest_id` from path and `ready` (boolean) from JSON body.
     - Validate: Ensure guest exists (query DB: `SELECT 1 FROM guests WHERE id = ?`).
     - Update DB: `UPDATE guests SET ready = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?` (use 1/0 for boolean).
     - Return 200 OK.

2. **UI Adjustments (JS in Template)**:
   - For each table row's 'ready' column (dynamically generated via JS):
     ```html
     <input type="checkbox" {% if guest.ready %}checked{% endif %} onchange="updateReady({{ guest.id }}, this.checked)">
     ```
     - JS function:
       ```javascript
       async function updateReady(guestId, ready) {
         await fetch(`/guests/${guestId}`, {
           method: 'PATCH',
           headers: { 'Content-Type': 'application/json' },
           body: JSON.stringify({ ready })
         });
         // Optional: Refresh table or local update
       }
       ```
   - No fallback needed since JS is allowed; if JS disabled, feature degrades gracefully.

3. **Edge Cases**:
   - **Concurrent Actions**: Local app handles one user fine.
   - **Testing**: Simulate checkbox change, verify API call and DB update.

This approach keeps the design simple while adding the requested UX improvements.

### Appendix C: Additional Requirements for Phone Number Handling

This appendix introduces new requirements for phone number management, including uniqueness checks, client-side debounced validation/formatting, and optional UI color-coding based on country codes for existing guests. These enhancements build on the existing design (e.g., phone as E.164 string, required for primaries) without altering core flows. Implementation uses app-level checks for uniqueness, JavaScript for UI interactions, and server-side logic for colors. Formatting is display-only on front-end; backend stores clean E.164 without dashes.

#### 1. Phone Number Uniqueness Check
- **Requirement**: Ensure no duplicate phone numbers across all guests to prevent errors (e.g., sending invites to the wrong person or webhook mismatches). This is an app-level validation, similar to group_id checks.
- **Implementation Guidance**:
  - In the POST /guests endpoint:
    - After parsing body, query DB: `SELECT COUNT(*) FROM guests WHERE phone = ?` (bind the entered phone).
    - If count > 0 and phone is not empty, return 400 with JSON error: { "error": "Phone number already exists for another guest." }
    - Proceed only if unique (or empty for non-primaries).
  - Edge Cases: Ignore empty phones; treat as exact string match (E.164 is standardized).

#### 2. UI-Level Debounced Typing Check for Formatting and Validation
- **Requirement**: In the add-guest form's phone input, provide tight browser-side real-time feedback as the user types: immediately flag errors if the input does not start with '+' or contains anything but numbers after the '+'. Perform full validation to ensure it matches valid E.164 for Indian (+91 followed by exactly 10 digits) or UAE (+971 followed by exactly 9 digits) numbers only. Use debouncing to delay full validation until typing pauses (e.g., 300ms), but apply immediate checks for prefix and numeric content. Show errors (e.g., red border and inline message like "Must start with '+' followed by numbers only" or "Not a valid Indian (+91, 10 digits) or UAE (+971, 9 digits) phone number"). Do not auto-add '+'; require the user to type it. On valid input, apply human-readable formatting in the input field (e.g., +91-XXXXX-XXXXX for India, +971-XX-XXX-XXXX for UAE) for display only. Prevent submission (i.e., do not send the fetch POST to /guests) if invalid; show an alert or inline error on attempt.
- **Implementation Guidance**:
  - **Client-Side JS**: Include a <script> block in the Jinja template for inline JS. Assume an inline error span next to the input: <span id="phone-error"></span>. Track validity with a variable (e.g., isPhoneValid = false).
    - Define a debounce function:
      ```javascript
      function debounce(func, delay) {
        let timeout;
        return function(...args) {
          clearTimeout(timeout);
          timeout = setTimeout(() => func(...args), delay);
        };
      }
      ```
    - Validation and formatting function (called debounced for full check, but add immediate event for basic checks):
      ```javascript
      let isPhoneValid = false;

      function validateAndFormatPhone(input, isImmediate = false) {
        let value = input.value.trim();
        const errorSpan = document.getElementById('phone-error');
        let errorMessage = '';
        
        // Immediate checks: Must start with '+', and only + followed by digits
        if (value && !value.startsWith('+')) {
          errorMessage = 'Must start with "+"';
        } else if (value && !/^\+\d*$/.test(value)) {
          errorMessage = 'Must contain only numbers after "+"';
        }
        
        // If no immediate error and not immediate call, perform full debounced validation
        if (!errorMessage && !isImmediate) {
          const cleanValue = value.replace(/[^+\d]/g, '');  // For validation, but don't modify input yet
          let formatted = cleanValue;
          if (cleanValue.startsWith('+91') && cleanValue.length === 13) {  // +91 + 10 digits
            isPhoneValid = true;
            formatted = '+91-' + cleanValue.slice(3,8) + '-' + cleanValue.slice(8);  // e.g., +91-XXXXX-XXXXX
          } else if (cleanValue.startsWith('+971') && cleanValue.length === 13) {  // +971 + 9 digits
            isPhoneValid = true;
            formatted = '+971-' + cleanValue.slice(4,6) + '-' + cleanValue.slice(6,9) + '-' + cleanValue.slice(9);  // e.g., +971-XX-XXX-XXXX
          } else if (cleanValue) {
            errorMessage = 'Not a valid phone number (must be Indian +91 with 10 digits or UAE +971 with 9 digits)';
            isPhoneValid = false;
          } else {
            isPhoneValid = false;  // Empty is invalid for submission if required
          }
          
          if (isPhoneValid) {
            input.value = formatted;  // Apply human-readable format to input (display only)
          }
        } else if (errorMessage) {
          isPhoneValid = false;
        }
        
        if (errorMessage) {
          input.style.border = '1px solid red';  // Error style
          errorSpan.textContent = errorMessage;
          errorSpan.style.color = 'red';
        } else {
          input.style.border = '';  // Reset
          errorSpan.textContent = '';
        }
      }
      ```
    - Attach to input: 
      ```javascript
      document.addEventListener('DOMContentLoaded', function() {
        const phoneInput = document.getElementById('phone-input');
        const debouncedValidate = debounce(() => validateAndFormatPhone(phoneInput), 300);
        
        // Immediate check on every input for basic rules
        phoneInput.addEventListener('input', () => {
          validateAndFormatPhone(phoneInput, true);
          debouncedValidate();  // Also trigger debounced full check
        });
      });
      ```
    - On "Add Guest" button click (JS handler): Before fetch, check if isPhoneValid (or re-validate): If not (and phone required for primary), show alert/inline error like "Please correct the phone number before submitting." and prevent the API call.
    - On submit (JS fetch): If valid, strip dashes/formatting to send clean E.164 (e.g., phone = phone.replace(/-/g, '');).
  - **Server-Side Fallback**: Re-validate on API receive (check for +91/10 digits or +971/9 digits) to ensure integrity. Store as plain E.164.
  - **UX Notes**: Feedback is visual and immediate for basic rules (prefix, digits-only), debounced for full format/length. Submission blocked client-side if invalid.

#### 3. Color Codes in UI Based on Country Code (for Existing Guests)
- **Requirement**: Visually distinguish existing guests in the table by coloring the phone cell (or row) based on the parsed country code from their E.164 phone (e.g., +1 blue for USA/Canada, +971 yellow for UAE, +44 green for UK). This aids quick scanning for international guests. Applicable only to entered users (table rows), not the add form.
- **Feasibility**: Yes, server-side via API/JS; use a static mapping of country codes to colors (grouped as specified; fallback 'cc-other' for others).
- **Implementation Guidance**:
  - **Python Mapping**: In the FastAPI app (e.g., in GET /guests), define a dict for codes to CSS classes/colors:
    ```python
    country_code_colors = {
        '1': 'cc-usacan',    # USA/Canada - e.g., lightblue
        '971': 'cc-uae',     # UAE - e.g., lightyellow
        '44': 'cc-uk',       # UK - e.g., lightgreen
        '91': 'cc-in',       # India - orange
        # Fallback for others: 'cc-other'
    }
    ```
    - Parse country code: For each guest.phone (if present), extract prefix after '+' (1-3 digits; simple: take until length matches a key, or use regex r'^\+(\d{1,3})').
    - Include 'phone_class' in JSON per guest (e.g., country_code_colors.get(prefix, 'cc-other')).
  - **CSS**: In template (or static file):
    ```css
    .cc-usacan { background-color: lightblue; }
    .cc-uae { background-color: lightyellow; }
    .cc-uk { background-color: lightgreen; }
    .cc-in { background-color: orange; }
    .cc-other { background-color: lightgray; }
    ```
  - **JS Update**: When populating table, apply class: <td class="${guest.phone_class}">${formatPhoneForDisplay(guest.phone)}</td> (where formatPhoneForDisplay adds dashes for display).
  - **Edge Cases**: No phone? No class. Invalid prefix? Fallback. Colors: Choose accessible (e.g., pastels); optional row coloring.

These requirements enhance data integrity and UX without complexity; implement sequentially starting with uniqueness.

This design provides a solid foundation for implementation. If any clarifications or adjustments are needed, let me know!