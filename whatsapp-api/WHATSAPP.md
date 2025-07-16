# WhatsApp API Documentation - Wedding Invitation System

This document describes the WhatsApp Business API integration for sending wedding invitations.

## Overview

The system uses WhatsApp Business API to send template-based wedding invitations to guests. It tracks delivery status through webhooks and maintains a complete audit trail.

## API Configuration

- **Base URL**: `https://graph.facebook.com/v23.0`
- **Phone Number ID**: Configured via `WHATSAPP_PHONE_NUMBER_ID` environment variable
- **Authentication**: Bearer token via `WHATSAPP_TOKEN` environment variable
- **Template**: `wedding_pre_invite_1` (English US)

## API Endpoints

### Send Message Endpoint
```
POST https://graph.facebook.com/v23.0/{PHONE_NUMBER_ID}/messages
```

## Message Templates

### wedding_pre_invite_1
A personalized wedding invitation template with one parameter:
- `name`: Guest's name (from greeting_name or constructed from prefix + first_name + last_name)

## API Request/Response Flow

### 1. Successful Message Send

**Request:**
```json
{
  "messaging_product": "whatsapp",
  "to": "971509364178",
  "type": "template",
  "template": {
    "name": "wedding_pre_invite_1",
    "language": {
      "code": "en_US"
    },
    "components": [
      {
        "type": "body",
        "parameters": [
          {
            "type": "text",
            "text": "Madhav Sharma",
            "parameter_name": "name"
          }
        ]
      }
    ]
  }
}
```

**Response (200 OK):**
```json
{
  "messaging_product": "whatsapp",
  "contacts": [
    {
      "input": "971509364178",
      "wa_id": "971509364178"
    }
  ],
  "messages": [
    {
      "id": "wamid.HBgJOTcxNTA5MzY0MTc4FQIAEhggOTlCRjc0N0IyRjVBNzBCRTUyODRBQjM1RTczQkQxNUIA",
      "message_status": "accepted"
    }
  ]
}
```

### 2. Failed Message Send (Missing Parameter)

**Request:**
```json
{
  "messaging_product": "whatsapp",
  "to": "14373668209",
  "type": "template",
  "template": {
    "name": "wedding_pre_invite_1",
    "language": {
      "code": "en_US"
    }
  }
}
```

**Response (400 Bad Request):**
```json
{
  "error": {
    "message": "(#132000) Number of parameters does not match the expected number of params",
    "type": "OAuthException",
    "code": 132000,
    "error_data": {
      "messaging_product": "whatsapp",
      "details": "body: number of localizable_params (0) does not match the expected number of params (1)"
    },
    "fbtrace_id": "ATdqH-A9cFJNdLo1xMIvz0t"
  }
}
```

## Webhook Events

### 1. Message Sent Status
```json
{
  "entry": [
    {
      "id": "583457838212229",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "16505550123",
              "phone_number_id": "486788031053645"
            },
            "statuses": [
              {
                "id": "wamid.HBgJOTcxNTA5MzY0MTc4FQIAEhggOTlCRjc0N0IyRjVBNzBCRTUyODRBQjM1RTczQkQxNUIA",
                "status": "sent",
                "timestamp": "1736960889",
                "recipient_id": "971509364178",
                "conversation": {
                  "id": "72b3b7ed25b2e5cf8b4f5b728f628d76",
                  "origin": {
                    "type": "utility"
                  }
                },
                "pricing": {
                  "billable": true,
                  "pricing_model": "CBP",
                  "category": "utility"
                }
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ],
  "object": "whatsapp_business_account"
}
```

### 2. Message Delivered Status
```json
{
  "entry": [
    {
      "id": "583457838212229",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "16505550123",
              "phone_number_id": "486788031053645"
            },
            "statuses": [
              {
                "id": "wamid.HBgJOTcxNTA5MzY0MTc4FQIAEhggOTlCRjc0N0IyRjVBNzBCRTUyODRBQjM1RTczQkQxNUIA",
                "status": "delivered",
                "timestamp": "1736960889",
                "recipient_id": "971509364178",
                "conversation": {
                  "id": "72b3b7ed25b2e5cf8b4f5b728f628d76",
                  "origin": {
                    "type": "utility"
                  }
                }
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ],
  "object": "whatsapp_business_account"
}
```

### 3. Message Read Status
```json
{
  "entry": [
    {
      "id": "583457838212229",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "16505550123",
              "phone_number_id": "486788031053645"
            },
            "statuses": [
              {
                "id": "wamid.HBgJOTcxNTA5MzY0MTc4FQIAEhggOTlCRjc0N0IyRjVBNzBCRTUyODRBQjM1RTczQkQxNUIA",
                "status": "read",
                "timestamp": "1736960892",
                "recipient_id": "971509364178"
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ],
  "object": "whatsapp_business_account"
}
```

### 4. Incoming Message (Button Response)
```json
{
  "entry": [
    {
      "id": "583457838212229",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "16505550123",
              "phone_number_id": "486788031053645"
            },
            "contacts": [
              {
                "profile": {
                  "name": "Madhav Sharma"
                },
                "wa_id": "971509364178"
              }
            ],
            "messages": [
              {
                "context": {
                  "from": "16505550123",
                  "id": "wamid.HBgJOTcxNTA5MzY0MTc4FQIAEhggOTlCRjc0N0IyRjVBNzBCRTUyODRBQjM1RTczQkQxNUIA"
                },
                "from": "971509364178",
                "id": "wamid.HBgJOTcxNTA5MzY0MTc4FQIAEhggMzZGRUJGMThGRDQ3MkZCQUQ5RjY1OEJGQTlEMDQ1NDMA",
                "timestamp": "1736960900",
                "type": "button",
                "button": {
                  "text": "Send me the invite",
                  "payload": "Send me the invite"
                }
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ],
  "object": "whatsapp_business_account"
}
```

## Status Flow

1. **API Call** - Request sent to WhatsApp API
2. **Accepted** - WhatsApp accepts the message (returns message ID)
3. **Sent** - Message sent to recipient's device
4. **Delivered** - Message delivered to recipient's device
5. **Read** - Recipient read the message
6. **Button Response** - Recipient clicked the invitation button

## Error Handling

### Common Errors

1. **Missing Template Parameters (Code: 132000)**
   - Ensure all template parameters are provided
   - Check parameter names match template definition

2. **Invalid Phone Number**
   - Remove '+' prefix from phone numbers
   - Ensure number includes country code

## Security

- All webhooks include `X-Hub-Signature-256` header for payload verification
- Use `WEBHOOK_VERIFY_TOKEN` for webhook endpoint verification
- Bearer token authentication for all API calls

## Database Fields Updated

### On Successful Send
- `sent_to_whatsapp`: 'succeeded'
- `message_id`: WhatsApp message ID
- `api_call_at`: Timestamp of API call

### On Webhook Events
- `sent_at`: When status = 'sent'
- `delivered_at`: When status = 'delivered'
- `read_at`: When status = 'read'
- `responded_with_button`: When button response received

## Implementation Notes

1. Phone numbers must exclude the '+' prefix when sending
2. All timestamps in webhooks are Unix timestamps (seconds)
3. Template language must be specified as 'en_US' (not just 'en')
4. Guest names are constructed from greeting_name or prefix + first_name + last_name
5. Webhook responses must always return 200 OK to prevent retries