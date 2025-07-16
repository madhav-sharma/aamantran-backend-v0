// Global variables
let guests = [];
let isPhoneValid = false;

// Utility functions
function debounce(func, delay) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func(...args), delay);
    };
}

// Phone validation functions

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
    if (!errorMessage && !isImmediate && value) {
        const cleanValue = value.replace(/[^+\d]/g, '');  // For validation, but don't modify input yet
        let formatted = cleanValue;
        
        if (cleanValue.startsWith('+1') && cleanValue.length === 12) {  // US: +1 + 10 digits
            isPhoneValid = true;
            formatted = '+1-' + cleanValue.slice(2,5) + '-' + cleanValue.slice(5,8) + '-' + cleanValue.slice(8);  // e.g., +1-XXX-XXX-XXXX
        } else if (cleanValue.startsWith('+44') && cleanValue.length === 13) {  // UK: +44 + 10 digits
            isPhoneValid = true;
            formatted = '+44-' + cleanValue.slice(3,7) + '-' + cleanValue.slice(7,10) + '-' + cleanValue.slice(10);  // e.g., +44-XXXX-XXX-XXX
        } else if (cleanValue.startsWith('+91') && cleanValue.length === 13) {  // India: +91 + 10 digits
            isPhoneValid = true;
            formatted = '+91-' + cleanValue.slice(3,8) + '-' + cleanValue.slice(8);  // e.g., +91-XXXXX-XXXXX
        } else if (cleanValue.startsWith('+971') && cleanValue.length === 13) {  // UAE: +971 + 9 digits
            isPhoneValid = true;
            formatted = '+971-' + cleanValue.slice(4,6) + '-' + cleanValue.slice(6,9) + '-' + cleanValue.slice(9);  // e.g., +971-XX-XXX-XXXX
        } else if (cleanValue.length >= 9 && cleanValue.length <= 16) {  // Other countries: + followed by 8-15 digits, little validation
            isPhoneValid = true;
            formatted = cleanValue;  // No specific formatting for others
        } else {
            errorMessage = 'Not a valid phone number';
            isPhoneValid = false;
        }
        
        if (isPhoneValid) {
            input.value = formatted;  // Apply human-readable format to input (display only)
        }
    } else if (errorMessage) {
        isPhoneValid = false;
    } else if (!value) {
        // Empty phone is valid for non-primary contacts
        isPhoneValid = true;
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

// Format phone for display
function formatPhoneForDisplay(phone) {
    if (!phone) return '';
    
    if (phone.startsWith('+91') && phone.length === 13) {
        return '+91-' + phone.slice(3,8) + '-' + phone.slice(8);
    } else if (phone.startsWith('+971') && phone.length === 13) {
        return '+971-' + phone.slice(4,6) + '-' + phone.slice(6,9) + '-' + phone.slice(9);
    }
    
    return phone;
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
        const response = await fetch('/guests');
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
        row.innerHTML = `
            <td>${guest.id}</td>
            <td>${guest.first_name}</td>
            <td>${guest.last_name}</td>
            <td>${guest.greeting_name || ''}</td>
            <td class="${guest.phone_class || ''}">${formatPhoneForDisplay(guest.phone)}</td>
            <td>${guest.group_id}</td>
            <td>${guest.is_group_primary ? 'Yes' : 'No'}</td>
            <td>
                <input type="checkbox" 
                       ${guest.ready ? 'checked' : ''} 
                       onchange="updateReady(${guest.id}, this.checked)"
                       title="Mark as ready for invite">
            </td>
            <td>${guest.sent_to_whatsapp}</td>
            <td>${formatDateTime(guest.sent_at)}</td>
            <td>${formatDateTime(guest.delivered_at)}</td>
            <td>${formatDateTime(guest.read_at)}</td>
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
        const response = await fetch(`/guests/${guestId}`, {
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
    alert(`Edit functionality coming soon!\n\nGuest: ${guest.first_name} ${guest.last_name}\nPhone: ${guest.phone || 'N/A'}\nGroup: ${guest.group_id}`);
}

// Handle form submission
async function handleAddGuest(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const phoneInput = document.getElementById('phone-input');
    const isPrimary = formData.get('is_group_primary') === 'on';
    
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
        first_name: formData.get('first_name').trim(),
        last_name: formData.get('last_name').trim(),
        greeting_name: formData.get('greeting_name').trim() || null,
        phone: phoneInput.value ? phoneInput.value.replace(/-/g, '') : null,  // Remove formatting
        group_id: formData.get('group_id').trim(),
        is_group_primary: isPrimary,
        ready: false
    };
    
    try {
        const response = await fetch('/guests', {
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
        const response = await fetch('/send-invites', {
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
    
    // Set up phone input validation
    const phoneInput = document.getElementById('phone-input');
    const debouncedValidate = debounce(() => validateAndFormatPhone(phoneInput), 300);
    
    // Immediate check on every input for basic rules
    phoneInput.addEventListener('input', () => {
        validateAndFormatPhone(phoneInput, true);
        debouncedValidate();  // Also trigger debounced full check
    });
    
    // Form submission
    const form = document.getElementById('add-guest-form');
    form.addEventListener('submit', handleAddGuest);
    
    // Send invites button
    const sendInvitesBtn = document.getElementById('send-invites-btn');
    sendInvitesBtn.addEventListener('click', sendInvites);
    
    // Refresh guests every 30 seconds to see webhook updates
    setInterval(loadGuests, 30000);
});
