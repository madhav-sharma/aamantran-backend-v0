def format_phone(phone: str) -> str:
    """
    Format E.164 phone numbers for display: +91-XXXXX-XXXXX (India), +971-XX-XXX-XXXX (UAE), else as is.
    """
    if not phone or not phone.startswith('+'):
        return phone or ''
    if phone.startswith('+91') and len(phone) == 13:
        return f'+91-{phone[3:8]}-{phone[8:]}'
    if phone.startswith('+971') and len(phone) == 13:
        return f'+971-{phone[4:6]}-{phone[6:9]}-{phone[9:]}'
    return phone
