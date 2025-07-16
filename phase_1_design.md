# Wedding RSVP Management: WhatsApp Chatbot Application

## Technical Design Document

### Version
V1.3 - Updated to include Appendix C on phone number enhancements.

### Overview
This document outlines the technical design for a simple, local Wedding RSVP Management application using a WhatsApp chatbot. The application is designed for a single wedding (not a SaaS product), running on a home PC with no cloud dependencies, auto-scaling, or Docker. It uses FastAPI as the web framework, Jinja templates for the UI, SQLite as the database, and direct integration with the WhatsApp API for messaging. All operations are local, with logging for API interactions stored in the database.

Key goals:
- Simplicity: Minimal features, no complex infrastructure.
- Focus: Manage guest list, send pre-invite messages via WhatsApp, track delivery via webhooks, and visualize status in a UI table.
- Scope: V1 covers guest management, bulk-like addition (one-at-a-time with context), message sending, webhook processing, and basic logging. RSVP responses (e.g., buttons) are out of scope for this design.

### System Architecture
- **Backend**: FastAPI application serving API endpoints and Jinja-templated HTML pages.
- **Frontend/UI**: Simple HTML tables rendered via Jinja, with forms for adding guests and triggering sends. No JavaScript frameworks; basic HTML/CSS for UX (e.g., table with input row at bottom). Minimal inline JavaScript allowed for specific enhancements (e.g., debouncing, auto-submit) as per appendices.
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
  - `phone`: Required if `is_group_primary` is True; optional otherwise (non-primaries without phone won't receive messages). Validate as E.164 format restricted to +91 (India, 10 digits) or +971 (UAE, 9 digits) (e.g., starts with '+', specific lengths). Additional uniqueness check as per Appendix C.
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
  - A table displaying all guests from DB, columns: ID, First Name, Last Name, Greeting Name, Phone (with color class as per Appendix C), Group ID, Is Primary (checkbox, read-only), Ready (editable checkbox with auto-submit as per Appendix B), Sent to WA (text), Sent At (datetime or 'N/A'), Delivered At (datetime or 'N/A'), Read At (datetime or 'N/A'), Message ID.
  - Rows sorted by group_id then is_group_primary (descending).
  - At the bottom: Inline input fields for new guest (First Name, Last Name, Greeting Name, Phone (with id="phone-input" and <span id="phone-error"></span> for validation as per Appendix C), Group ID, Is Primary checkbox).
  - Button next to inputs: "Add Guest" (POST to `/add-guest`, validates, adds to DB, redirects to refresh page).
  - Another button: "Send Invites" (POST to `/send-invites`, scans for ready=True and sent_to_whatsapp='pending', sends messages).
  - UX: Table allows seeing all records while adding (no separate form). Use simple CSS for validation errors (e.g., red borders). Display 'N/A' or empty for NULL timestamps. Inline JS for phone debouncing/formatting and ready auto-submit.
- **No Bulk Upload**: Addition feels "bulk-like" but is one-at-a-time with context (user sees previous for reference, e.g., to match group_ids).
- **Validation Feedback**: On add, if invalid (e.g., missing phone for primary, duplicate phone), show error message above table and preserve inputs (as per Appendix A/B).

### API Endpoints (FastAPI)
- **GET /**: Render main Jinja template with guests data (query DB: `SELECT * FROM guests ORDER BY group_id, is_group_primary DESC`). Compute phone_class for each guest (as per Appendix C) and pass to template.
- **POST /add-guest**: 
  - Parse form data (first_name, etc.). Strip any human-readable formatting from phone (e.g., remove dashes) for phone before validation/storage.
  - Validate fields, group rules (e.g., query DB for existing group_id, check primary rules), phone uniqueness and format (as per Appendix C).
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
- **POST /update-ready/{guest_id}**: Update ready field as per Appendix B (POST for form compatibility).

### Messaging Flow
- **Pre-Invite Send**: Hard-coded template (out of scope for details; e.g., "Dear {name}, ..."). Send only to guests with phone (primaries required to have one; non-primaries optional).
- **Webhook Processing**: Background task parses payload, matches via message_id, updates DB timestamps for sent_at, delivered_at, read_at. Store all in logs.
- **Tracking**: UI table shows timestamps (indicating occurrence); no auto-retries (manual via "Send Invites" button).

### Security/Edge Cases
- Local-only: No auth needed (assume single user).
- Validation: App-level for all rules to keep DB simple.
- Errors: Log failures; show in UI if critical.
- Data Integrity: Unique group_id check on add (query existing); phone uniqueness as per Appendix C.

### Dependencies
- FastAPI
- Jinja2
- requests (for WhatsApp API)
- sqlite3 (built-in)
- Starlette (for SessionMiddleware as per Appendix B)

### Future Extensions (Out of Scope)
- RSVP button handling.
- Log viewing UI.
- Message template editor.
- Retries/auto-sends.
- Handling failed webhook statuses (e.g., add failed_at timestamp).

### Appendix A: Preserving Form Data on Validation Failure for 'is_group_primary' and Other Checks

This appendix provides implementation guidance for ensuring that, upon validation failure during the guest addition process (POST to /add-guest), the user's input data is preserved and redisplayed in the form fields. This applies to all validations, including 'is_group_primary' rules (e.g., must be True for new group_id, False for existing with no duplicates per group), as well as others like phone format or required fields. The core design already notes preserving inputs on failure, but this appendix details the approach without altering the main requirements.

#### Rationale
- Post-submission validation (server-side) can fail due to data-dependent checks (e.g., querying DB for group_id existence). To improve UX, the user should not lose entered data (e.g., names, phone, group_id), avoiding retyping on correction (e.g., unchecking is_group_primary or changing group_id).

#### Implementation Approach
- **Handle in FastAPI Endpoint** (/add-guest):
  - Use Pydantic or manual dict to parse form data into a guest_data object/dict.
  - Perform validations; if any fail (e.g., for is_group_primary):
    - Query DB: `cur.execute("SELECT COUNT(*) FROM guests WHERE group_id = ? AND is_group_primary = 1", (group_id,))` to check existing primaries.
    - If invalid, do NOT insert; instead, prepare to re-render the main template (/) with additional context:
      - Pass `error_message = "Specific error, e.g., 'Cannot add non-primary to new group; primary must be added first.'"`
      - Pass `form_data = request.form` or the parsed data dict (e.g., {'first_name': 'John', 'is_group_primary': True, ...}) to the template.
  - On success, insert and redirect to / (302 Found).

- **Jinja Template Adjustments**:
  - In the add-row section, use Jinja conditionals to pre-fill inputs from `form_data` if provided:
    ```jinja
    <input type="text" name="first_name" value="{{ form_data.first_name if form_data else '' }}">
    <input type="checkbox" name="is_group_primary" {% if form_data.is_group_primary %}checked{% endif %}>
    ```
  - Display error if present: `{% if error_message %}<p style="color: red;">{{ error_message }}</p>{% endif %}` above the add row.
  - This ensures fields retain values from the failed submission.

- **No JavaScript Required**: Relies on server-side renders and redirects. On failure, render / directly from /add-guest (no redirect), showing updated table with existing guests plus preserved form.
- **Edge Cases**:
  - Multiple errors: Collect all validation errors in a list and display as bullet points.
  - Security: Escape inputs in Jinja to prevent XSS (though local-only).
  - Testing: Simulate failures (e.g., invalid group_id) to verify data persistence.

This appendix ensures the existing design supports data preservation without changing core flows or introducing new features like client-side validation.

### Appendix B: Implementing the Ready Update with Auto-Submit and Preserving Incomplete Add Form Data

This appendix provides guidance for enhancing the 'ready' field update mechanism using the optional PATCH /update-ready/{guest_id} endpoint (or a POST equivalent for simplicity). The goal is to enable auto-submission when ticking the 'ready' checkbox in the UI table, while preserving any incomplete data in the add-guest form (e.g., from a prior validation failure). This builds on the existing design without altering core requirements, keeping things simple (no JS frameworks, but allowing basic inline JavaScript for auto-submit since it's minimal and HTML-native). If preserving across updates proves too complex, it can be omitted as a V1 nice-to-have.

#### Rationale
- **Auto-Submit on Tick**: Users can click the 'ready' checkbox in a table row, triggering an immediate update without a separate "Save" button, improving UX for quick flagging.
- **Preserve Incomplete Add Form**: If the add-guest form at the bottom has pre-filled data (e.g., from a failed validation), updating a 'ready' checkbox elsewhere should not clear it on page reload. This avoids frustrating re-entry.

#### Implementation Approach
1. **Endpoint Setup**:
   - Use PATCH /update-ready/{guest_id} (or POST /update-ready/{guest_id} if PATCH is tricky with forms).
   - Logic:
     - Extract `guest_id` from path and `ready` (boolean) from form data (e.g., checkbox value).
     - Validate: Ensure guest exists (query DB: `SELECT 1 FROM guests WHERE id = ?`).
     - Update DB: `UPDATE guests SET ready = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?` (use 1/0 for boolean).
     - To handle preservation: If the request includes optional `form_data` (serialized, e.g., as JSON in a hidden field or query param), pass it back. But for simplicity, use server-side session storage (via Starlette middleware in FastAPI) to temporarily store incomplete add form data.
     - Redirect to / (with optional query param like ?error=... if needed, but primarily for success).
   - Enable sessions in FastAPI: Add `app = FastAPI()` with middleware like `app.add_middleware(SessionMiddleware, secret_key="local_secret")`. This is lightweight and fits the local app.

2. **UI Adjustments (Jinja Template)**:
   - For each table row's 'ready' column:
     ```html
     <form method="POST" action="/update-ready/{{ guest.id }}">  <!-- Use POST for form compatibility -->
       <input type="checkbox" name="ready" {% if guest.ready %}checked{% endif %} onchange="this.form.submit()">
     </form>
     ```
     - The `onchange="this.form.submit()"` uses basic inline JS to auto-submit on tick/untick. (No external JS file needed; this is HTML5-compatible and simple.)
   - For the add-guest form (bottom row):
     - No changes to inputs, but on validation failure in /add-guest, store the form_data in session: `request.session['add_form_data'] = {'first_name': form.first_name, ...}` before re-rendering /.
     - On rendering / (GET or after redirects):
       - Check session for 'add_form_data'; if present, pass to template as `form_data` and pre-fill:
         ```jinja
         <input type="text" name="first_name" value="{{ form_data.first_name if form_data else '' }}">
         <!-- Similarly for other fields, including checkbox for is_group_primary -->
         ```
       - After successful add, clear session: `del request.session['add_form_data']`.
   - Error display remains as-is (passed via context).

3. **Preservation Across Updates**:
   - When submitting a 'ready' update (auto or manual), the endpoint redirects to /, where the render checks session for 'add_form_data' and preserves it.
   - This works because session persists across requests (user's browser cookies handle it locally).
   - If no incomplete data (normal case), session key is absent, and add form is blank.
   - Complexity Check: Sessions add minimal overhead (one middleware line); if too complicated, alternative is passing serialized form_data as a hidden field in every ready form or query params on redirect (e.g., /?form_first_name=John&...), but sessions are cleaner and less error-prone.

4. **Edge Cases**:
   - **No JS Fallback**: If JS is disabled, checkbox won't auto-submit; user would need a "Save" button per row (add <button type="submit">Save</button>).
   - **Concurrent Actions**: Sessions handle one user fine (local app); no multi-user conflicts.
   - **Clearing Preservation**: On successful add, delete session data to reset form.
   - **Testing**: Simulate add failure (e.g., invalid primary), verify preservation; then update a ready checkbox and check add form retains data post-redirect.

This approach keeps the design simple while adding the requested UX improvements. If sessions are undesired, fall back to query params for preservation (append to redirect URL).

### Appendix C: Additional Requirements for Phone Number Handling

This appendix introduces new requirements for phone number management, including uniqueness checks, client-side debounced validation/formatting, and optional UI color-coding based on country codes for existing guests. These enhancements build on the existing design (e.g., phone as E.164 string, required for primaries) without altering core flows. Implementation uses app-level checks for uniqueness, basic inline JavaScript for UI interactions (consistent with prior appendices allowing minimal JS), and server-side logic for colors.

#### 1. Phone Number Uniqueness Check
- **Requirement**: Ensure no duplicate phone numbers across all guests to prevent errors (e.g., sending invites to the wrong person or webhook mismatches). This is an app-level validation, similar to group_id checks.
- **Implementation Guidance**:
  - In the /add-guest POST endpoint:
    - After parsing form data, query DB: `SELECT COUNT(*) FROM guests WHERE phone = ?` (bind the entered phone).
    - If count > 0 and phone is not empty, fail validation with error: "Phone number already exists for another guest."
    - Proceed only if unique (or empty for non-primaries).
  - Preserve form data on failure (as per Appendix A: use session or context to re-fill inputs).
  - Edge Cases: Ignore empty phones; case-insensitive? No, treat as exact string match (E.164 is standardized).

#### 2. UI-Level Debounced Typing Check for Formatting and Validation
- **Requirement**: In the add-guest form's phone input, provide real-time feedback as the user types: auto-format to E.164 (e.g., add '+' if missing), validate as valid E.164 restricted to Indian (+91, 10 digits) or UAE (+971, 9 digits) numbers only, show errors (e.g., red border and inline pop-up message like "Not a valid phone number" if invalid, including if it doesn't start with '+'), without spamming checks. Use debouncing to delay validation until typing pauses (e.g., 300ms). On valid input, apply human-readable formatting in the input field (e.g., +91-XXXXX-XXXXX for India, +971-XX-XXX-XXXX for UAE) while storing as E.164.
- **Implementation Guidance**:
  - **Client-Side JS**: Include a <script> block in the Jinja template (main page) for minimal inline JS. No external libraries needed. Assume an inline error span next to the input: <span id="phone-error"></span>.
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
    - Validation and formatting function:
      ```javascript
      function validateAndFormatPhone(input) {
        let value = input.value.trim().replace(/[^+\d]/g, '');  // Strip non-digits except +
        const errorSpan = document.getElementById('phone-error');
        
        // Auto-format: Add '+' if missing and starts with digit
        if (value && !value.startsWith('+') && /^\d/.test(value)) {
          value = '+' + value;
        }
        
        // Restrict to India (+91, 10 digits) or UAE (+971, 9 digits)
        let isValid = false;
        let formatted = value;
        if (value.startsWith('+91') && value.length === 13) {  // +91 + 10 digits
          isValid = true;
          formatted = '+91-' + value.slice(3,8) + '-' + value.slice(8);  // e.g., +91-XXXXX-XXXXX
        } else if (value.startsWith('+971') && value.length === 13) {  // +971 + 9 digits
          isValid = true;
          formatted = '+971-' + value.slice(4,6) + '-' + value.slice(6,9) + '-' + value.slice(9);  // e.g., +971-XX-XXX-XXXX
        }
        
        if (value && !isValid) {
          input.style.border = '1px solid red';  // Error style
          errorSpan.textContent = 'Not a valid phone number (must be Indian +91 or UAE +971 in E.164 format)';  // Inline "pop-up" message
          errorSpan.style.color = 'red';
        } else {
          input.style.border = '';  // Reset
          errorSpan.textContent = '';
          if (isValid) {
            input.value = formatted;  // Apply human-readable format to input
          }
        }
      }
      ```
    - Attach to input: In the template, for the phone <input id="phone-input" ...>, add onload or inline:
      ```javascript
      document.addEventListener('DOMContentLoaded', function() {
        const phoneInput = document.getElementById('phone-input');
        const debouncedValidate = debounce(validateAndFormatPhone, 300);
        phoneInput.addEventListener('input', () => debouncedValidate(phoneInput));
      });
      ```
  - **Server-Side Fallback**: Re-validate on submit (as existing, but add checks for +91/10 digits or +971/9 digits) to ensure integrity. Strip formatting dashes before storage.
  - **UX Notes**: Feedback is visual (e.g., border color and inline message acting as a "pop-up"); no blocking submit if invalid—error shown post-submit as before. Preserves form data on failure. Human display applied only in UI; store as plain E.164.

#### 3. Color Codes in UI Based on Country Code (for Existing Guests)
- **Requirement**: If feasible, visually distinguish existing guests in the table by coloring the phone cell (or row) based on the parsed country code from their E.164 phone (e.g., +1 blue for USA/Canada, +971 yellow for UAE, +44 green for UK). This aids quick scanning for international guests. Applicable only to entered users (table rows), not the add form.
- **Feasibility**: Yes, server-side via Jinja/CSS; no client-side needed. Use a static mapping of country codes to colors (grouped as specified; fallback 'cc-other' for others).
- **Implementation Guidance**:
  - **Python Mapping**: In the FastAPI app (e.g., in the GET / endpoint), define a dict for codes to CSS classes/colors:
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
    - Pass to Jinja: In guests query, add computed 'phone_class' per row (e.g., country_code_colors.get(prefix, 'cc-other')).
  - **CSS**: In template (or static file):
    ```css
    .cc-usacan { background-color: lightblue; }
    .cc-uae { background-color: lightyellow; }
    .cc-uk { background-color: lightgreen; }
    .cc-in { background-color: orange; }
    .cc-other { background-color: lightgray; }
    ```
  - **Template Update**: For phone column: <td class="{{ guest.phone_class }}">{{ guest.phone }}</td>
  - **Edge Cases**: No phone? No class. Invalid prefix? Fallback. Colors: Choose accessible (e.g., pastels); optional row coloring via <tr class="{{ guest.phone_class }}">.
  - **Expansion**: If needed, assign additional codes to 'cc-other'.

These requirements enhance data integrity and UX without complexity; implement sequentially starting with uniqueness.

This design provides a solid foundation for implementation. If any clarifications or adjustments are needed, let me know!