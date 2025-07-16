# Wedding RSVP Management: WhatsApp Chatbot Application

## Technical Design Document

### Instructions
- The code provided in the design doc is just for sample purposes. 
- The file structure should allow for future growth of the application.
- REST APIs should have a directory and a separate file for the whatsapp webhook
- HTML page aPIs should be separate
- JS scripts and CSS can be in-line with HTML or with separate files, it's upon the discretion of the implementation agent

### Version

V0.1

### Overview

This document outlines the technical design for Phase 1 of a simple, local Wedding RSVP Management application using a WhatsApp chatbot. It is just meant to send a pre-invite message and track its status and allow guests to be entered. The application is designed for a single wedding (not a SaaS product), running on a home PC with no cloud dependencies, auto-scaling, or Docker. It uses FastAPI as the web framework, Jinja templates for initial UI serving (with JS enhancements), SQLite as the database, and direct integration with the WhatsApp API for messaging. All operations are local, with logging for API interactions stored in the database.

Key goals:

- **Simplicity**: Minimal features, no complex infrastructure.
- **Focus**: Manage guest list, send pre-invite messages via WhatsApp, track delivery via webhooks, and visualize status in a UI table.
- **Scope**: V1 covers guest management, bulk-like addition (one-at-a-time with context), message sending, webhook processing, and basic logging. RSVP responses (e.g., buttons) are out of scope for this design.

### System Architecture

- **Backend**: FastAPI application serving REST API endpoints and an initial Jinja-templated HTML page.
- **Frontend/UI**: Responsive web app using HTML/CSS with JavaScript (vanilla JS or lightweight like React if desired) for dynamic interactions. JS handles form submissions via REST API calls (e.g., fetch or XMLHttpRequest), table updates, and real-time feedback. No pure form submissions; use JS to send data to APIs and update UI dynamically.
- **Database**: SQLite file (e.g., `wedding.db`) for storing guests and logs.
- **Messaging**: Direct WhatsApp Business API calls (using `requests` library or similar) for sending messages. Webhook endpoint in FastAPI to receive status updates (sent/delivered/read).
- **Logging**: All WhatsApp API requests, responses, and webhooks stored in a dedicated DB table.
- **Deployment**: Run locally for testing via `fastapi dev src/whatsapp_api/main.py` or `fastapi run src/whatsapp_api/main.py` outside of localhost development and webhook forwarding and internet exposure are outside the scope.

Use SQLAlchemy for DB interactions (declarative models with sessions for CRUD operations). Use Pydantic for data validation where needed (e.g., guest models integrated with SQLAlchemy).

### Validation Strategy

This application strictly separates validation concerns between client and server:

- **Client-Side Validation**: ALL format validation (names contain only letters, phone numbers match E.164 format, group_id contains only lowercase letters). Client-side prevents submission of invalid formats but does not check against database records. The submit button is disabled until all format validations pass.
- **Server-Side Validation**: Business logic validation against database records ONLY (phone number uniqueness, group primary rules, ensuring primaries have phone numbers). Server does NOT re-validate formats - no regex checks, no pattern matching, no string formatting.

**Important**: The server must trust that the client has already validated formats. Server-side code should NOT include:
- Regex pattern validation
- String capitalization/formatting
- Length checks (except database column limits)
- Character set validation
- Any format transformation

The only server-side validations are:
1. Database uniqueness constraints (e.g., phone number already exists)
2. Business rule validation (e.g., group must have a primary before adding non-primary members)
3. Required field validation based on other fields (e.g., primary contacts must have phone numbers)


### Database Schema

Single SQLite database with two tables: `guests` and `logs`. Define SQLAlchemy models for each.

#### Guests Model

Stores guest information and invite status. SQLAlchemy model example:

```python
from sqlalchemy import Column, Integer, String, String, Boolean, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Guest(Base):
    __tablename__ = 'guests'
    id = Column(Integer, primary_key=True, autoincrement=True)
    prefix = Column(String)  # Optional prefix like 'Mr.', 'Mrs.', etc.
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    greeting_name = Column(String)
    phone = Column(String, unique=True)  # Enforce uniqueness at DB level
    group_id = Column(String, nullable=False)
    is_group_primary = Column(Boolean, nullable=False)
    ready = Column(Boolean, nullable=False, default=False)
    sent_to_whatsapp = Column(String, default='pending')
    api_call_at = Column(DateTime)  # When the WhatsApp API call was made
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    read_at = Column(DateTime)
    responded_with_button = Column(Boolean, default=False)
    message_id = Column(String)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
```

**Constraints/Validations**:

- `prefix`: Optional string; format validated client-side only.
- `first_name` and `last_name`: Required, non-empty strings; format validated client-side only (Appendix A).
- `greeting_name`: Optional string; format validated client-side only (Appendix A).
- `phone`: Required if `is_group_primary` is True; optional otherwise. Format validated client-side only (Appendix C). Uniqueness enforced at database level. Store clean E.164 without dashes or formatting.
- `group_id`: Required non-empty string; format validated client-side only (Appendix D). Server validates business rules for group primary logic.
- `is_group_primary`: Server validates business rules:
  - For new group_id: Must be True (primary added first) and guest must have phone number.
  - For existing group_id: Must be False, and ensure only one True per group_id exists.
- `ready`: Defaults to False; user sets to True via UI (e.g., checkbox in table). The checkbox is disabled (client-side) for guests without phone numbers since invites cannot be sent without a phone number.
- `sent_to_whatsapp`: Defaults to 'pending'. Updated after API send: 'succeeded' on 200 OK, 'failed' otherwise.
- `api_call_at`: Set to current timestamp when WhatsApp API call is made.
- Webhook fields (`sent_at`, `delivered_at`, `read_at`): NULL initially. On webhook processing, set to the timestamp from the webhook (or CURRENT_TIMESTAMP if not provided) when the corresponding status is received.
- Timestamps: `created_at` set on insert; `updated_at` updated on any change.
- Indexes: Add via SQLAlchemy (e.g., `Index('idx_group_id', 'group_id')`, `Index('idx_message_id', 'message_id')`).
- **Data Immutability**: After guest creation, names, phone numbers, group_id, and is_group_primary cannot be modified via API to maintain data integrity for messaging operations and webhook tracking.

#### Logs Model

Stores WhatsApp API interactions for auditing. SQLAlchemy model example:

```python
class Log(Base):
    __tablename__ = 'logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    guest_id = Column(Integer)
    timestamp = Column(DateTime, default=func.current_timestamp())
    type = Column(String, nullable=False)
    payload = Column(String, nullable=False)
    status = Column(String)
    is_multiple = Column(Boolean, default=False)
```

- No strict FK constraint (to allow NULL guest_id).
- For bulk/multi webhooks: Set `guest_id` to NULL, `is_multiple` to True, store full payload for manual review.
- No UI for logs in V1 (out of scope); accessible via direct DB queries if needed.

### User Interface (UI)

- **Main Page**: `/` (GET) - Serves a Jinja template with an HTML structure, including a table placeholder, input fields for adding guests, and buttons. JS script fetches guest data via API (GET /guests), populates the table dynamically, and handles interactions.
- **Table**: Displays all guests with read-only columns for all fields except Ready (editable checkbox). Names, phone, and group information cannot be modified after creation. Columns: ID, Prefix (if present), First Name, Last Name, Greeting Name, Phone (with color class as per Appendix C; display with human-readable formatting via JS), Group ID, Is Primary (read-only), Ready (editable checkbox with auto-submit via JS as per Appendix B; disabled for guests without phone numbers), Sent to WA (text), API Call At (datetime or 'N/A'), Sent At (datetime or 'N/A'), Delivered At (datetime or 'N/A'), Read At (datetime or 'N/A'), Message ID.
- Rows sorted by group_id then is_group_primary (descending) via JS or API query.

- **Add Guest**: Input fields (Prefix input with id="prefix-input" and `<span id="prefix-error"></span>`, First Name (with id="first-name-input" and `<span id="first-name-error"></span>` for validation as per Appendix A), Last Name (similar), Greeting Name (similar), Phone (with id="phone-input" and `<span id="phone-error"></span>` for validation as per Appendix C), Group ID (with id="group-id-input" and `<span id="group-id-error"></span>` for validation as per Appendix D), Is Primary checkbox). Submit button is disabled until all format validations pass. JS handles "Add Guest" button click: Validates locally (including strict name, phone, and group_id format checks via JS, preventing submission if invalid), sends POST to /guests via fetch if valid, refreshes table on success, shows error message if failed.

- **Send Invites**: Button triggers JS to call POST /send-invites, then refreshes table.
- **UX**: Dynamic updates without full page reloads. Use CSS for validation errors (e.g., red borders). Display 'N/A' or empty for NULL timestamps. Inline JS for name sanitization/capitalization, phone debouncing/formatting, group_id validation, and ready auto-submit.
- **No Bulk Upload**: Addition feels "bulk-like" but is one-at-a-time with context (user sees previous for reference, e.g., to match group_ids).
- **Validation Feedback**: JS provides client-side format validation feedback; server returns JSON errors on API calls for business logic violations (e.g., { "error": "Phone number already exists for another guest." }), displayed via JS alerts or inline.

### API Endpoints (FastAPI)

- **GET /guests**: Return JSON list of all guests (query via SQLAlchemy session: `session.query(Guest).order_by(Guest.group_id, Guest.is_group_primary.desc()).all()`). Compute phone_class for each guest (as per Appendix C).

- **POST /guests**:
  - Parse JSON body (prefix, first_name, etc.). Store phone as-is from client (client already removed formatting).
  - Server-side business logic validation ONLY:
    - **Phone uniqueness**: Database constraint enforced (handle IntegrityError if duplicate)
    - **Group primary rules**:
      - If is_group_primary=True: Query database to ensure no other guests exist with this group_id AND verify phone is provided
      - If is_group_primary=False: Query database to ensure at least one primary already exists for this group_id
    - **Primary phone requirement**: If is_group_primary=True, phone must not be empty/null
  - NO format validation, NO regex checks, NO string manipulation on server

  - If valid, create Guest instance, add to session, commit. Return 201 Created with guest data on success; 400 with JSON error on failure.

- **POST /send-invites**:
  - Query guests where ready=True and sent_to_whatsapp='pending' (via session).
  - For each (loop, as simple/local):
    - If phone exists: 
      - Set guest.api_call_at = current timestamp
      - Construct WhatsApp API request (hard-coded template with {name} = greeting_name or first_name)
      - Log request payload (create Log instance, add to session)
      - Send via `requests.post` to WhatsApp API
      - Log response (add another Log)
      - If 200: Update guest.sent_to_whatsapp='succeeded', store message_id, commit
      - Else: Update guest.sent_to_whatsapp='failed', commit
  - Return 200 OK on completion.

- **POST /webhook**: WhatsApp webhook endpoint (verify token as per API docs).
  - Receive payload (JSON).
  - Log full webhook (create Log with type='webhook', payload=JSON dump, add to session).
  - If multiple statuses: Set is_multiple=True, guest_id=NULL.
  - Else: Extract message_id, status (sent/delivered/read), and timestamp (if provided).
  - Query guests by message_id (via session) to find match.
  - Update corresponding _at field (e.g., guest.sent_at = webhook_timestamp or func.current_timestamp()) and updated_at, commit.
  - If no match or multi: Log with NULL guest_id.
  - Return 200 OK.

- **PATCH /guests/{guest_id}**: Update the ready field only (JSON body: {"ready": true}). Query guest by id, update ready attribute, commit. Return 200 OK on success. Note: Core guest information (names, phone, group_id, etc.) cannot be updated after creation to maintain data integrity for messaging operations.

### Messaging Flow

- **Pre-Invite Send**: Hard-coded template (out of scope for details; e.g., "Dear {name}, ..."). Send only to guests with phone (primaries required to have one; non-primaries optional). Use greeting_name if available, otherwise first_name for {name} placeholder.
- **Webhook Processing**: Endpoint handler parses payload, matches via message_id, updates DB timestamps for sent_at, delivered_at, read_at. Store all in logs.
- **Tracking**: UI table shows timestamps (indicating occurrence); no auto-retries (manual via "Send Invites" button).

### Security/Edge Cases

- **Local-only**: No auth needed (assume single user).
- **Validation**: Client-side for format validation; server-side for business logic validation against database records.
- **Errors**: Log failures; return JSON errors for UI display.
- **Data Integrity**: Phone uniqueness enforced at database level; group primary checks enforced at application level.
- **No Updates to Core Data**: After guest creation, names, phone numbers, group_id, and is_group_primary cannot be modified via API to prevent data inconsistencies with sent messages and webhook tracking. Only the ready status can be toggled.

### Dependencies

- FastAPI
- Jinja2
- httpx for all API calls
- sqlalchemy (for DB models and sessions)
- sqlite3 (built-in, used via SQLAlchemy engine)
- pydantic when needed

### Future Extensions (Out of Scope)

- RSVP button handling.
- Log viewing UI.
- Message template editor.
- Retries/auto-sends.
- Handling failed webhook statuses (e.g., add failed_at timestamp).
- Transaction management for complex operations.

### Appendix A: Additional Requirements for Name Handling

This appendix introduces new requirements for name fields (prefix, first_name, last_name, greeting_name) management, including prefix support and client-side real-time capitalization/sanitization. These enhancements build on the existing design (e.g., names as strings, required for first/last) without altering core flows. Implementation uses only front-end checks for format validation, JavaScript for UI interactions. All format validation is client-side only.

#### 1. Prefix Support

**Requirement**: Allow optional prefixes (e.g., Mr, Ms) as single word without spaces or symbols. Store separately in DB for potential future use.

**Implementation Guidance**:
- In UI: allow any string containing only a-zA-Z or empty (validated client-side).
- In POST body: Send 'prefix' as string (or empty).
- Server: No format validation. Store in guest.prefix as received from client.

#### 2. UI-Level Real-Time Typing Check for Capitalization and Sanitization

**Requirement**: For prefix, first_name, last_name, and greeting_name inputs, provide instant browser-side feedback: As typing, automatically capitalize the first letter and lowercase the rest (e.g., "john" -> "John"). Instantly sanitize by removing non-letter inputs (allow only a-zA-Z; disallow spaces, numbers/symbols). If sanitization removes characters, show a transient inline message (e.g., "Invalid characters removed"). Flag errors if name is empty (for required fields). Prevent submission if invalid; show red border and inline message (e.g., "This field is required"). No debouncing needed—immediate on input. Fixed case structure: first capital, rest lower, no spaces.

**Implementation Guidance**:

**Client-Side JS**: Include a `<script>` block in the Jinja template. Assume error spans like `<span id="first-name-error"></span>` for each.

Function for each name input (or generic):

```javascript
function sanitizeAndCapitalizeName(input, errorSpanId, required) {
    let originalValue = input.value;
    // Sanitize: Allow only letters a-zA-Z
    let value = originalValue.replace(/[^a-zA-Z]/g, '');
    // Capitalize: First letter upper, rest lower
    if (value) {
        value = value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();
    }
    input.value = value;
    const errorSpan = document.getElementById(errorSpanId);
    let errorMessage = '';
    if (originalValue !== value && originalValue) {
        errorMessage = 'Invalid characters removed'; // Transient feedback
    }
    if (required && !value) {
        errorMessage = errorMessage ? errorMessage + '. ' : '' + 'This field is required';
    }
    if (errorMessage) {
        input.style.border = '1px solid red';
        errorSpan.textContent = errorMessage;
        errorSpan.style.color = 'red';
    } else {
        input.style.border = '';
        errorSpan.textContent = '';
    }
    // Clear transient message after 2 seconds if no other error
    if (errorMessage.startsWith('Invalid characters removed')) {
        setTimeout(() => {
            if (errorSpan.textContent.startsWith('Invalid characters removed')) {
                errorSpan.textContent = '';
                input.style.border = '';
            }
        }, 2000);
    }
    return !errorMessage || errorMessage.startsWith('Invalid characters removed'); // Allow submit if only transient
}
```

Attach to inputs:

```javascript
document.addEventListener('DOMContentLoaded', function() {
    const nameInputs = [
        {id: 'prefix-input', error: 'prefix-error', required: false},
        {id: 'first-name-input', error: 'first-name-error', required: true},
        {id: 'last-name-input', error: 'last-name-error', required: true},
        {id: 'greeting-name-input', error: 'greeting-name-error', required: false}
    ];
    nameInputs.forEach(({ id, error, required }) => {
        const input = document.getElementById(id);
        if (input) {
            input.addEventListener('input', () => sanitizeAndCapitalizeName(input, error, required));
        }
    });
});
```

**On "Add Guest" Button Click**: Before fetch, re-validate all names: Loop through inputs, call sanitizeAndCapitalizeName, check if no persistent errors (e.g., empty required). If invalid, show alert/inline error and prevent API call.

**No Server-Side Format Validation**: Rely solely on client-side validation for name formats.

**UX Notes**: Immediate sanitization/capitalization improves input; transient messages for removals; errors visual (border, message). Submission blocked client-side if invalid (e.g., required empty).

#### 3. Edge Cases

- Empty optional fields (greeting_name, prefix): Allow, no error.
- Names with spaces/symbols: Automatically remove them, capitalize the resulting string.
- Storage: Names stored as formatted (capitalized, sanitized); prefix separate.

These requirements enhance data quality and UX for names; implement after phone handling.

### Appendix B: Implementing the Ready Update with Auto-Submit

This appendix provides guidance for enhancing the 'ready' field update mechanism using the PATCH /guests/{guest_id} endpoint. The goal is to enable auto-submission when ticking the 'ready' checkbox in the UI table. This builds on the existing design without altering core requirements, using JS for dynamic updates.

#### Rationale

**Auto-Submit on Tick**: Users can click the 'ready' checkbox in a table row, triggering an immediate update without a separate "Save" button, improving UX for quick flagging.

#### Implementation Approach

1. **Endpoint Setup**:
   - PATCH /guests/{guest_id}:
     - Extract `guest_id` from path and `ready` (boolean) from JSON body.
     - Validate: Ensure guest exists (query session: `session.query(Guest).filter_by(id=guest_id).first()`).
     - Update: guest.ready = ready, commit.
     - Return 200 OK.

2. **UI Adjustments (JS in Template)**:
   - For each table row's 'ready' column (dynamically generated via JS):
   - Checkbox is disabled if guest has no phone number (client-side check)
   - Tooltip shows appropriate message based on phone availability

```html
<input type="checkbox" 
       {% if guest.ready %}checked{% endif %} 
       {% if not guest.phone %}disabled{% endif %}
       onchange="updateReady({{ guest.id }}, this.checked)"
       title="{% if not guest.phone %}Phone number required to mark as ready{% else %}Mark as ready for invite{% endif %}">
```

JS function:

```javascript
async function updateReady(guestId, ready) {
    await fetch(`/guests/${guestId}`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            ready
        })
    });
    // Optional: Refresh table or local update
}
```

No fallback needed since JS is allowed; if JS disabled, feature degrades gracefully.

3. **Edge Cases**:
   - **Concurrent Actions**: Local app handles one user fine.
   - **Testing**: Simulate checkbox change, verify API call and DB update.
   - **No Phone Number**: Checkbox is disabled client-side for guests without phone numbers, preventing ready status updates for these guests.

This approach keeps the design simple while adding the requested UX improvements.

### Appendix C: Additional Requirements for Phone Number Handling

This appendix introduces new requirements for phone number management, including uniqueness checks, client-side debounced validation/formatting, and optional UI color-coding based on country codes for existing guests. These enhancements build on the existing design (e.g., phone as E.164 string, required for primaries) without altering core flows. Implementation uses database-level constraints for uniqueness, JavaScript for UI interactions, and server-side logic for colors. Formatting is display-only on front-end; backend stores clean E.164 without dashes. All format validation is client-side only.

#### 1. Phone Number Uniqueness Check

**Requirement**: Ensure no duplicate phone numbers across all guests to prevent errors (e.g., sending invites to the wrong person or webhook mismatches). This is enforced at the database level for data integrity.

**Implementation Guidance**:
- **Database Level**: Add `unique=True` constraint to the phone column in the SQLAlchemy model to enforce uniqueness at the database level.
- In the POST /guests endpoint:
  - Try to create and commit the Guest instance
  - If a database integrity error occurs due to duplicate phone (SQLAlchemy will raise an IntegrityError), catch the exception and return 400 with JSON error: { "error": "Phone number already exists for another guest." }
  - This ensures data integrity even if multiple requests arrive simultaneously
- Edge Cases: Empty/NULL phones are allowed and don't conflict with the unique constraint.

#### 2. UI-Level Debounced Typing Check for Formatting and Validation


**Requirement**: In the add-guest form's phone input, provide tight browser-side real-time feedback as the user types: immediately flag errors if the input does not start with '+' or contains anything but numbers, spaces, and dashes after the '+'. Allow users to type with or without formatting (spaces and dashes are permitted). Perform full validation to ensure it matches valid E.164 format (any country code with appropriate number of digits). Use debouncing to delay full validation until typing pauses (e.g., 300ms), but apply immediate checks for basic format. Show clear error messages with green checkmark for valid numbers. Do not auto-format the input field - users can type naturally with or without dashes/spaces. The server will strip all formatting before storage. For display in tables, apply consistent formatting based on country code. Prevent submission if invalid, and ensure the submit button is disabled when phone format is invalid (for primary contacts, phone is required).


**Implementation Guidance**:

**Client-Side JS**: Include a `<script>` block in the Jinja template for inline JS. Assume an inline error span next to the input: `<span id="phone-error"></span>`. Track validity with a variable (e.g., isPhoneValid = false).

Define a debounce function:

```javascript
function debounce(func, delay) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func(...args), delay);
    };
}
```

Validation and formatting function (called debounced for full check, but add immediate event for basic checks):

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
        const cleanValue = value.replace(/[^+\d]/g, ''); // For validation, but don't modify input yet
        let formatted = cleanValue;
        if (cleanValue.startsWith('+91') && cleanValue.length === 13) { // +91 + 10 digits
            isPhoneValid = true;
            formatted = '+91-' + cleanValue.slice(3, 8) + '-' + cleanValue.slice(8); // e.g., +91-XXXXX-XXXXX
        } else if (cleanValue.startsWith('+971') && cleanValue.length === 13) { // +971 + 9 digits
            isPhoneValid = true;
            formatted = '+971-' + cleanValue.slice(4, 6) + '-' + cleanValue.slice(6, 9) + '-' + cleanValue.slice(9); // e.g., +971-XX-XXX-XXXX
        } else if (cleanValue) {
            errorMessage = 'Not a valid phone number (must be Indian +91 with 10 digits or UAE +971 with 9 digits)';
            isPhoneValid = false;
        } else {
            isPhoneValid = false; // Empty is invalid for submission if required
        }
        if (isPhoneValid) {
            input.value = formatted; // Apply human-readable format to input (display only)
        }
    } else if (errorMessage) {
        isPhoneValid = false;
    }
    if (errorMessage) {
        input.style.border = '1px solid red'; // Error style
        errorSpan.textContent = errorMessage;
        errorSpan.style.color = 'red';
    } else {
        input.style.border = ''; // Reset
        errorSpan.textContent = '';
    }
}
```

Attach to input:

```javascript
document.addEventListener('DOMContentLoaded', function() {
    const phoneInput = document.getElementById('phone-input');
    const debouncedValidate = debounce(() => validateAndFormatPhone(phoneInput), 300);
    // Immediate check on every input for basic rules
    phoneInput.addEventListener('input', () => {
        validateAndFormatPhone(phoneInput, true);
        debouncedValidate(); // Also trigger debounced full check
    });
});
```

On "Add Guest" button click (JS handler): Before fetch, check if isPhoneValid (or re-validate): If not (and phone required for primary), show alert/inline error like "Please correct the phone number before submitting." and prevent the API call.

On submit (JS fetch): If valid, strip dashes/formatting to send clean E.164 (e.g., phone = phone.replace(/-/g, '');).

**No Server-Side Format Validation**: Client-side handles all format validation.

**UX Notes**: Feedback is visual and immediate for basic rules (prefix, digits-only), debounced for full format/length. Submission blocked client-side if invalid.

#### 3. Color Codes in UI Based on Country Code (for Existing Guests)

**Requirement**: Visually distinguish existing guests in the table by coloring the phone cell (or row) based on the parsed country code from their E.164 phone (e.g., +1 blue for USA/Canada, +971 yellow for UAE, +44 green for UK). This aids quick scanning for international guests. Applicable only to entered users (table rows), not the add form.

**Feasibility**: Yes, server-side via API/JS; use a static mapping of country codes to colors (grouped as specified; fallback 'cc-other' for others).

**Implementation Guidance**:

**Python Mapping**: In the FastAPI app (e.g., in GET /guests), define a dict for codes to CSS classes/colors:

```python
country_code_colors = {
    '1': 'cc-usacan',  # USA/Canada - e.g., lightblue
    '971': 'cc-uae',  # UAE - e.g., lightyellow
    '44': 'cc-uk',  # UK - e.g., lightgreen
    '91': 'cc-in',  # India - orange
    # Fallback for others: 'cc-other'
}
```

Parse country code: For each guest.phone (if present), extract prefix after '+' (1-3 digits; simple: take until length matches a key, or use regex r'^\+(\d{1,3})').

Include 'phone_class' in JSON per guest (e.g., country_code_colors.get(prefix, 'cc-other')).

**CSS**: In template (or static file):

```css
.cc-usacan { background-color: lightblue; }
.cc-uae { background-color: lightyellow; }
.cc-uk { background-color: lightgreen; }
.cc-in { background-color: orange; }
.cc-other { background-color: lightgray; }
```

**JS Update**: When populating table, apply class: `<td class="${guest.phone_class}">${formatPhoneForDisplay(guest.phone)}</td>` (where formatPhoneForDisplay adds dashes for display).

**Edge Cases**: No phone? No class. Invalid prefix? Fallback. Colors: Choose accessible (e.g., pastels); optional row coloring.

These requirements enhance data integrity and UX without complexity; implement sequentially starting with uniqueness.

### Appendix D: Additional Requirements for Group ID Handling

This appendix introduces requirements for group_id field management, including format validation and client-side real-time sanitization to ensure consistent grouping. These enhancements build on the existing design without altering core flows. Implementation uses front-end validation and dynamic sanitization for user experience. All format validation is client-side only.

#### 1. Group ID Format Requirements

**Requirement**: group_id must be a lowercase string containing only letters a-z. No spaces, numbers, symbols, or uppercase letters allowed. This ensures consistent grouping and prevents data integrity issues.

**Implementation Guidance**:
- Validation: Only a-z characters allowed (client-side only)
- Storage: As received from client (client ensures lowercase)
- UI: Real-time sanitization and validation

#### 2. UI-Level Real-Time Group ID Validation and Sanitization

**Requirement**: For the group_id input, provide instant browser-side feedback: As typing, automatically convert to lowercase and remove any non-letter characters. If sanitization removes characters, show a transient inline message (e.g., "Invalid characters removed"). Flag errors if group_id is empty (required field). Prevent submission if invalid; show red border and inline message. No debouncing needed—immediate on input.

**Implementation Guidance**:

**Client-Side JS**: Include validation function for group_id input with error span `<span id="group-id-error"></span>`.

```javascript
function sanitizeAndValidateGroupId(input, errorSpanId) {
    let originalValue = input.value;
    // Sanitize: Allow only letters a-z, convert to lowercase
    let value = originalValue.toLowerCase().replace(/[^a-z]/g, '');
    
    input.value = value;
    const errorSpan = document.getElementById(errorSpanId);
    let errorMessage = '';
    
    if (originalValue !== value && originalValue) {
        errorMessage = 'Invalid characters removed. Only lowercase letters a-z allowed.';
    }
    
    if (!value) {
        errorMessage = errorMessage ? errorMessage + ' ' : '' + 'Group ID is required';
    }
    
    if (errorMessage) {
        input.style.border = '1px solid red';
        errorSpan.textContent = errorMessage;
        errorSpan.style.color = 'red';
    } else {
        input.style.border = '';
        errorSpan.textContent = '';
    }
    
    // Clear transient message after 2 seconds if no other error
    if (errorMessage.startsWith('Invalid characters removed')) {
        setTimeout(() => {
            if (errorSpan.textContent.startsWith('Invalid characters removed')) {
                if (value) { // Only clear if we have a valid value
                    errorSpan.textContent = '';
                    input.style.border = '';
                }
            }
        }, 2000);
    }
    
    return !!value; // Return true if valid (non-empty)
}
```

Attach to group_id input:

```javascript
document.addEventListener('DOMContentLoaded', function() {
    const groupIdInput = document.getElementById('group-id-input');
    if (groupIdInput) {
        groupIdInput.addEventListener('input', () => sanitizeAndValidateGroupId(groupIdInput, 'group-id-error'));
    }
});
```

**On "Add Guest" Button Click**: Before fetch, validate group_id: Call sanitizeAndValidateGroupId and check return value. If invalid (empty or sanitized to empty), prevent API call.

**No Server-Side Format Validation**: Client-side handles all format validation.

**UX Notes**: Immediate sanitization provides clear feedback; prevents user confusion about valid formats. Submission blocked client-side if invalid.

This design provides a solid foundation for implementation. If any clarifications or adjustments are needed, let me know!


# Wedding RSVP API Reference

## Overview
This document provides a concise reference for all API endpoints in the Wedding RSVP Management application.

## Base URL
Local development: `http://localhost:8000`

## Endpoints

### 1. GET /guests
**Purpose**: Retrieve all guests with computed phone color classes.

**Request**: 
```http
GET /guests
```

**Response**: 
```json
[
  {
    "id": 1,
    "prefix": "Mr",
    "first_name": "John",
    "last_name": "Doe",
    "greeting_name": "Johnny",
    "phone": "+919876543210",
    "phone_class": "cc-in",
    "group_id": "family",
    "is_group_primary": true,
    "ready": false,
    "sent_to_whatsapp": "pending",
    "api_call_at": null,
    "sent_at": null,
    "delivered_at": null,
    "read_at": null,
    "message_id": null,
    "created_at": "2025-01-15T10:30:00",
    "updated_at": "2025-01-15T10:30:00"
  }
]
```

**Notes**: Results ordered by group_id, then is_group_primary (descending).

---

### 2. POST /guests
**Purpose**: Create a new guest with server-side business logic validation.

**Request**:
```http
POST /guests
Content-Type: application/json

{
  "prefix": "Ms",
  "first_name": "Jane",
  "last_name": "Smith",
  "greeting_name": "Janie",
  "phone": "+971501234567",
  "group_id": "friends",
  "is_group_primary": true
}
```

**Success Response** (201):
```json
{
  "id": 2,
  "prefix": "Ms",
  "first_name": "Jane",
  "last_name": "Smith",
  "greeting_name": "Janie",
  "phone": "+971501234567",
  "group_id": "friends",
  "is_group_primary": true,
  "ready": false,
  "sent_to_whatsapp": "pending",
  "api_call_at": null,
  "sent_at": null,
  "delivered_at": null,
  "read_at": null,
  "message_id": null,
  "created_at": "2025-01-15T10:35:00",
  "updated_at": "2025-01-15T10:35:00"
}
```

**Error Responses** (400):
```json
{ "error": "Phone number already exists for another guest." }
{ "error": "Primary guest must have a phone number." }
{ "error": "Group already exists. New guest must not be primary." }
{ "error": "Group does not exist. First guest must be primary." }
```

**Server-Side Validation Rules**:
- Phone uniqueness (database constraint)
- If `is_group_primary=true`: group_id must not exist AND phone must be provided
- If `is_group_primary=false`: group_id must exist with existing primary
- Primary guests must have phone numbers

---

### 3. PATCH /guests/{guest_id}
**Purpose**: Update only the ready status of an existing guest.

**Request**:
```http
PATCH /guests/1
Content-Type: application/json

{
  "ready": true
}
```

**Success Response** (200):
```json
{
  "message": "Guest updated successfully"
}
```

**Error Response** (404):
```json
{ "error": "Guest not found" }
```

**Notes**: Only the `ready` field can be updated. All other guest information is immutable.

---

### 4. POST /send-invites
**Purpose**: Send WhatsApp invites to all ready guests with pending status.

**Request**:
```http
POST /send-invites
```

**Response** (200):
```json
{
  "message": "Invites processing completed",
  "processed": 5,
  "sent": 3,
  "failed": 2
}
```

**Process Flow**:
1. Query guests where `ready=true` and `sent_to_whatsapp='pending'`
2. For each guest with phone:
   - Set `api_call_at` to current timestamp
   - Log request payload
   - Send WhatsApp API request
   - Log response
   - Update `sent_to_whatsapp` to 'succeeded' or 'failed'
   - Store `message_id` if successful

**Notes**: Uses template with `{name}` = `greeting_name` or `first_name`

---

### 5. POST /webhook
**Purpose**: Receive WhatsApp delivery status updates.

**Request**:
```http
POST /webhook
Content-Type: application/json

{
  "entry": [{
    "changes": [{
      "value": {
        "statuses": [{
          "id": "wamid.ABC123",
          "status": "delivered",
          "timestamp": "1642686000",
          "recipient_id": "919876543210"
        }]
      }
    }]
  }]
}
```

**Response** (200):
```json
{ "status": "ok" }
```

**Process Flow**:
1. Log full webhook payload
2. Extract message_id, status, and timestamp
3. Find matching guest by message_id
4. Update corresponding timestamp field:
   - `sent_at` for "sent" status
   - `delivered_at` for "delivered" status  
   - `read_at` for "read" status
5. If multiple statuses or no match: log with `guest_id=NULL`

---

### 6. GET /
**Purpose**: Serve the main UI page with Jinja template.

**Request**:
```http
GET /
```

**Response**: HTML page with table, forms, and JavaScript for dynamic interactions.

## Error Handling

### Common HTTP Status Codes
- **200**: Success
- **201**: Created (for POST /guests)
- **400**: Bad Request (validation errors)
- **404**: Not Found (for PATCH /guests with invalid ID)
- **500**: Internal Server Error

### Validation Types

- **Client-Side**: ALL format validation (names a-zA-Z only, phone E.164 format, group_id a-z only, greeting name max 60 chars). Submit button disabled until valid.
- **Server-Side**: Business logic validation ONLY (phone uniqueness via DB constraint, group primary rules via DB queries, primary phone requirement)


## Data Types

### Guest Object
```typescript
{
  id: number,
  prefix?: string,
  first_name: string,
  last_name: string,
  greeting_name?: string,
  phone?: string,
  phone_class?: string, // Only in GET responses
  group_id: string,
  is_group_primary: boolean,
  ready: boolean,
  sent_to_whatsapp: "pending" | "succeeded" | "failed",
  api_call_at?: datetime,
  sent_at?: datetime,
  delivered_at?: datetime,
  read_at?: datetime,
  message_id?: string,
  created_at: datetime,
  updated_at: datetime
}
```

### Phone Color Classes
- `cc-in`: India (+91) - Orange
- `cc-uae`: UAE (+971) - Light yellow
- `cc-usacan`: USA/Canada (+1) - Light blue
- `cc-uk`: UK (+44) - Light green
- `cc-other`: Other countries - Light gray