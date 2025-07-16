
// Global variables
let guests = [];
let isPhoneValid = false;
let formValidationState = {
    prefix: true,  // Optional, so default valid
    first_name: false,
    last_name: false,
    greeting_name: true,  // Optional, so default valid
    phone: true,  // Optional for non-primary, so default valid
    group_id: false
};

// Utility functions
function debounce(func, delay) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func(...args), delay);
    };
}

// Update submit button state based on form validation
function updateSubmitButtonState() {
    const submitButton = document.querySelector('#add-guest-form button[type="submit"]');
    const isFormValid = Object.values(formValidationState).every(valid => valid);
    
    if (isFormValid) {
        submitButton.disabled = false;
        submitButton.classList.remove('btn-disabled');
    } else {
        submitButton.disabled = true;
        submitButton.classList.add('btn-disabled');
    }
}

// Name validation and formatting
function validateAndFormatName(input, fieldName) {
    let value = input.value.trim();
    const errorSpan = document.getElementById(`${fieldName}-error`);
    let errorMessage = '';
    let isValid = false;
    
    if (value) {
        // Check if contains only letters
        if (!/^[a-zA-Z]+$/.test(value)) {
            errorMessage = 'Must contain only letters (A-Z)';
            input.style.border = '1px solid red';
        } else {
            // Auto-capitalize first letter
            value = value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();
            input.value = value;
            input.style.border = '';
            isValid = true;
        }
    } else if (fieldName === 'prefix' || fieldName === 'greeting_name') {
        // Empty is valid for optional fields
        input.style.border = '';
        isValid = true;
    } else {
        // Empty is invalid for required fields
        errorMessage = 'This field is required';
        input.style.border = '1px solid red';
    }
    
    if (errorSpan) {
        if (errorMessage) {
            errorSpan.textContent = errorMessage;
            errorSpan.style.color = 'red';
        } else {
            errorSpan.textContent = '';
        }
    }
    
    // Update form validation state
    if (fieldName === 'first-name') {
        formValidationState.first_name = isValid;
    } else if (fieldName === 'last-name') {
        formValidationState.last_name = isValid;
    } else if (fieldName === 'greeting-name') {
        formValidationState.greeting_name = isValid;
    } else {
        formValidationState[fieldName] = isValid;
    }
    updateSubmitButtonState();
    
    return isValid;
}

// Greeting validation (max 60 characters, free-form text allowed)
function validateGreeting(input) {
    const value = input.value; // Don't trim - preserve user's exact input including spaces
    const errorSpan = document.getElementById('greeting-error');
    let errorMessage = '';
    let isValid = true;
    
    if (value && value.length > 60) {
        errorMessage = `Must be 60 characters or less (currently ${value.length})`;
        input.style.border = '1px solid red';
        isValid = false;
    } else {
        input.style.border = '';
        isValid = true;
    }
    
    if (errorSpan) {
        errorSpan.textContent = errorMessage;
        errorSpan.style.color = 'red';
    }
    
    // Update form validation state
    formValidationState.greeting_name = isValid;
    updateSubmitButtonState();
    
    return isValid;
}

// Group ID validation and formatting
function sanitizeAndValidateGroupId(input, errorSpanId) {
    let originalValue = input.value;
    // Sanitize: Allow only letters a-z, convert to lowercase
    let value = originalValue.toLowerCase().replace(/[^a-z]/g, '');
    
    input.value = value;
    const errorSpan = document.getElementById(errorSpanId);
    let errorMessage = '';
    let isValid = false;
    
    if (originalValue !== value && originalValue) {
        errorMessage = 'Invalid characters removed. Only lowercase letters a-z allowed.';
    }
    
    if (!value) {
        errorMessage = errorMessage ? errorMessage + ' ' : '' + 'Group ID is required';
    } else {
        isValid = true;
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
    
    // Update form validation state
    formValidationState.group_id = isValid;
    updateSubmitButtonState();
    
    return isValid;
}

// Phone validation functions
function validateAndFormatPhone(input, isImmediate = false) {
    let value = input.value.trim();
    const errorSpan = document.getElementById('phone-error');
    let errorMessage = '';
    
    // Strip all non-digit characters except + for validation
    const cleanValue = value.replace(/[^\d+]/g, '');
    
    // Check if user is typing
    if (isImmediate) {
        // Basic validation while typing
        if (value && !value.startsWith('+')) {
            errorMessage = 'Must start with "+"';
            isPhoneValid = false;
        } else if (value && cleanValue !== value.replace(/[\s-]/g, '')) {
            // Allow only numbers, +, spaces, and dashes
            errorMessage = 'Only numbers, spaces, and dashes allowed after "+"';
            isPhoneValid = false;
        } else {
            // While typing, don't show error if it's just incomplete
            isPhoneValid = false; // Will be set to true after full validation
        }
    } else {
        // Full validation (debounced)
        if (value && !cleanValue.startsWith('+')) {
            errorMessage = 'Must start with "+"';
            isPhoneValid = false;
        } else if (value && cleanValue.length > 1) {
            // Validate known formats
            if (cleanValue.startsWith('+1') && cleanValue.length === 12) {  // US/Canada: +1 + 10 digits
                isPhoneValid = true;
            } else if (cleanValue.startsWith('+44') && cleanValue.length === 13) {  // UK: +44 + 10 digits
                isPhoneValid = true;
            } else if (cleanValue.startsWith('+91') && cleanValue.length === 13) {  // India: +91 + 10 digits
                isPhoneValid = true;
            } else if (cleanValue.startsWith('+971') && cleanValue.length === 13) {  // UAE: +971 + 9 digits
                isPhoneValid = true;
            } else if (cleanValue.length >= 9 && cleanValue.length <= 16) {  // Other countries: + followed by 8-15 digits
                isPhoneValid = true;
            } else {
                errorMessage = 'Invalid phone number format';
                isPhoneValid = false;
            }
        } else if (value && cleanValue.length === 1) {
            errorMessage = 'Phone number incomplete';
            isPhoneValid = false;
        } else if (!value) {
            // Empty is valid for non-primary
            isPhoneValid = true;
            errorMessage = '';
        }
    }
    
    // Update UI
    if (errorMessage) {
        input.style.border = '1px solid red';
        errorSpan.textContent = errorMessage;
        errorSpan.style.color = 'red';
    } else if (!isImmediate && value && isPhoneValid) {
        input.style.border = '1px solid green';
        errorSpan.textContent = '✓ Valid phone number';
        errorSpan.style.color = 'green';
    } else {
        input.style.border = '';
        errorSpan.textContent = '';
    }
    
    // Update form validation state - phone validation depends on primary checkbox
    const isPrimary = document.getElementById('is_group_primary').checked;
    if (isPrimary) {
        formValidationState.phone = isPhoneValid && !!value;
        if (!value) {
            input.style.border = '1px solid red';
            errorSpan.textContent = 'Phone number required for primary contacts';
            errorSpan.style.color = 'red';
        }
    } else {
        formValidationState.phone = true; // Always valid for non-primary
    }
    updateSubmitButtonState();
}

// Format phone for display in table
function formatPhoneForDisplay(phone) {
    if (!phone) return '';
    
    // Clean the phone number first
    const clean = phone.replace(/[^\d+]/g, '');
    
    if (clean.startsWith('+1') && clean.length === 12) {
        return '+1-' + clean.slice(2,5) + '-' + clean.slice(5,8) + '-' + clean.slice(8);
    } else if (clean.startsWith('+44') && clean.length === 13) {
        return '+44-' + clean.slice(3,7) + '-' + clean.slice(7,10) + '-' + clean.slice(10);
    } else if (clean.startsWith('+91') && clean.length === 13) {
        return '+91-' + clean.slice(3,8) + '-' + clean.slice(8);
    } else if (clean.startsWith('+971') && clean.length === 13) {
        return '+971-' + clean.slice(4,6) + '-' + clean.slice(6,9) + '-' + clean.slice(9);
    }
    
    return clean;
}

// Format datetime for display
function formatDateTime(dateStr) {
    if (!dateStr) return 'N/A';
    
    const date = new Date(dateStr);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Show message
function showMessage(message, type) {
    const messageDiv = document.getElementById('form-message');
    messageDiv.textContent = message;
    messageDiv.className = `message ${type}`;
    messageDiv.style.display = 'block';
    
    setTimeout(() => {
        messageDiv.style.display = 'none';
    }, 5000);
}

// Fetch and display guests
async function loadGuests() {
    try {
        const response = await fetch('/api/guests');
        if (!response.ok) throw new Error('Failed to fetch guests');
        
        guests = await response.json();
        displayGuests();
    } catch (error) {
        console.error('Error loading guests:', error);
        showMessage('Failed to load guests', 'error');
    }
}

// Display guests in table
function displayGuests() {
    const tbody = document.getElementById('guests-tbody');
    const noGuestsDiv = document.getElementById('no-guests');
    const table = document.getElementById('guests-table');
    
    tbody.innerHTML = '';
    
    if (guests.length === 0) {
        table.style.display = 'none';
        noGuestsDiv.style.display = 'block';
        return;
    }
    
    table.style.display = 'table';
    noGuestsDiv.style.display = 'none';
    
    guests.forEach(guest => {
        const row = document.createElement('tr');
        
        // UI logic for ready checkbox
        const isSent = guest.sent_to_whatsapp !== 'pending';
        const readyCheckboxDisabled = isSent || !guest.phone;
        
        if (!guest.ready && isSent) {
            console.error(`Inconsistency Error: Guest ID ${guest.id} is not marked as ready but has been sent to WhatsApp.`);
        }

        row.innerHTML = `
            <td>${guest.id}</td>
            <td>${guest.prefix || ''}</td>
            <td>${guest.first_name}</td>
            <td>${guest.last_name}</td>
            <td>${guest.greeting_name || ''}</td>
            <td class="${guest.phone_class || ''}">${formatPhoneForDisplay(guest.phone)}</td>
            <td>${guest.group_id}</td>
            <td>${guest.is_group_primary ? 'Yes' : 'No'}</td>
            <td>
                <input type="checkbox" 
                       ${guest.ready ? 'checked' : ''} 
                       ${readyCheckboxDisabled ? 'disabled' : ''}
                       onchange="updateReady(${guest.id}, this.checked)"
                       title="${!guest.phone ? 'Phone number required to mark as ready' : (isSent ? 'Already sent' : 'Mark as ready for invite')}">
            </td>
            <td>${guest.sent_to_whatsapp}</td>
            <td>${formatDateTime(guest.api_call_at)}</td>
            <td>${formatDateTime(guest.sent_at)}</td>
            <td>${formatDateTime(guest.delivered_at)}</td>
            <td>${formatDateTime(guest.read_at)}</td>
            <td>${guest.message_id || ''}</td>
            <td>${formatDateTime(guest.created_at)}</td>
            <td>${formatDateTime(guest.updated_at)}</td>
            <td>
                <button class="edit-btn" onclick="editGuest(${guest.id})">Edit</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Update guest ready status
async function updateReady(guestId, ready) {
    try {
        const response = await fetch(`/api/guests/${guestId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ready })
        });
        
        if (!response.ok) throw new Error('Failed to update guest');
        
        // Update local data
        const updatedGuest = await response.json();
        const index = guests.findIndex(g => g.id === guestId);
        if (index !== -1) {
            guests[index] = updatedGuest;
        }
        
        showMessage('Guest updated successfully', 'success');
    } catch (error) {
        console.error('Error updating guest:', error);
        showMessage('Failed to update guest', 'error');
        // Reload to restore correct state
        loadGuests();
    }
}

// Edit guest (placeholder for future implementation)
function editGuest(guestId) {
    const guest = guests.find(g => g.id === guestId);
    if (!guest) return;
    
    // For now, just show guest details
    const displayName = [guest.prefix, guest.first_name, guest.last_name].filter(Boolean).join(' ');
    alert(`Edit functionality coming soon!\n\nGuest: ${displayName}\nPhone: ${guest.phone || 'N/A'}\nGroup: ${guest.group_id}`);
}

// Handle form submission
async function handleAddGuest(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const phoneInput = document.getElementById('phone-input');
    const isPrimary = formData.get('is_group_primary') === 'on';
    
    // Validate all name fields
    const prefixValid = validateAndFormatName(document.getElementById('prefix'), 'prefix');
    const firstNameValid = validateAndFormatName(document.getElementById('first_name'), 'first-name');
    const lastNameValid = validateAndFormatName(document.getElementById('last_name'), 'last-name');
    const greetingValid = validateGreeting(document.getElementById('greeting_name'));
    
    if (!prefixValid || !firstNameValid || !lastNameValid || !greetingValid) {
        showMessage('Please correct the form errors before submitting', 'error');
        return;
    }
    
    // Check phone validation
    if (isPrimary && !phoneInput.value) {
        showMessage('Phone number is required for primary contacts', 'error');
        phoneInput.focus();
        return;
    }
    
    if (phoneInput.value && !isPhoneValid) {
        showMessage('Please correct the phone number before submitting', 'error');
        phoneInput.focus();
        return;
    }
    
    // Prepare data
    const data = {
        prefix: formData.get('prefix').trim() || null,
        first_name: formData.get('first_name').trim(),
        last_name: formData.get('last_name').trim(),
        greeting_name: formData.get('greeting_name') || null,  // Don't trim - preserve exact user input
        phone: phoneInput.value ? phoneInput.value.replace(/[^\d+]/g, '') : null,  // Remove all formatting except + and digits
        group_id: formData.get('group_id').trim(),
        is_group_primary: isPrimary,
        ready: false
    };
    
    try {
        const response = await fetch('/api/guests', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const responseData = await response.json();
        
        if (!response.ok) {
            throw new Error(responseData.detail || 'Failed to add guest');
        }
        
        showMessage('Guest added successfully', 'success');
        event.target.reset();
        phoneInput.style.border = '';
        document.getElementById('phone-error').textContent = '';
        isPhoneValid = false;
        
        // Reload guests
        loadGuests();
    } catch (error) {
        console.error('Error adding guest:', error);
        showMessage(error.message || 'Failed to add guest', 'error');
    }
}

// Send invites
async function sendInvites() {
    if (!confirm('Are you sure you want to send invites to all ready guests?')) {
        return;
    }
    
    try {
        const response = await fetch('/whatsapp/send-invites-to-ready-guests', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) throw new Error('Failed to send invites');
        
        const result = await response.json();
        showMessage(result.message || 'Invites sent successfully', 'success');
        
        // Reload guests to see updated statuses
        loadGuests();
    } catch (error) {
        console.error('Error sending invites:', error);
        showMessage('Failed to send invites', 'error');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Load guests
    loadGuests();
    
    // Set up name validation
    const prefixInput = document.getElementById('prefix');
    const firstNameInput = document.getElementById('first_name');
    const lastNameInput = document.getElementById('last_name');
    const greetingInput = document.getElementById('greeting_name');
    
    if (prefixInput) {
        prefixInput.addEventListener('input', () => validateAndFormatName(prefixInput, 'prefix'));
    }
    
    if (firstNameInput) {
        firstNameInput.addEventListener('input', () => validateAndFormatName(firstNameInput, 'first-name'));
    }
    
    if (lastNameInput) {
        lastNameInput.addEventListener('input', () => validateAndFormatName(lastNameInput, 'last-name'));
    }
    
    if (greetingInput) {
        greetingInput.addEventListener('input', () => {
            validateGreeting(greetingInput);
        });
    }
    
    // Set up phone input validation
    const phoneInput = document.getElementById('phone-input');
    const debouncedValidate = debounce(() => validateAndFormatPhone(phoneInput), 300);
    
    // Immediate check on every input for basic rules
    phoneInput.addEventListener('input', () => {
        validateAndFormatPhone(phoneInput, true);
        debouncedValidate();  // Also trigger debounced full check
    });
    
    // Set up group_id validation
    const groupIdInput = document.getElementById('group_id');
    if (groupIdInput) {
        groupIdInput.addEventListener('input', () => sanitizeAndValidateGroupId(groupIdInput, 'group-id-error'));
    }
    
    // Handle primary checkbox change - revalidate phone
    const primaryCheckbox = document.getElementById('is_group_primary');
    if (primaryCheckbox) {
        primaryCheckbox.addEventListener('change', () => {
            // Force full validation when primary status changes
            validateAndFormatPhone(phoneInput, false);
        });
    }
    
    // Form submission
    const form = document.getElementById('add-guest-form');
    form.addEventListener('submit', handleAddGuest);
    
    // Send invites button
    const sendInvitesBtn = document.getElementById('send-invites-btn');
    sendInvitesBtn.addEventListener('click', sendInvites);
    
    // Initial submit button state
    updateSubmitButtonState();
    
    // Refresh guests every 30 seconds to see webhook updates
    setInterval(loadGuests, 30000);
});
