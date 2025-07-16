# WhatsApp API Sample Data Documentation

This document contains sample data from the WhatsApp API integration including API calls, webhook payloads, and guest invitation flow.

## Table of Contents
1. [WhatsApp API Calls](#whatsapp-api-calls)
2. [Webhook Payloads](#webhook-payloads)
3. [Guest Invitation Flow](#guest-invitation-flow)

---

## WhatsApp API Calls

### 1. Successful Template Message Request
**Request Details:**
- **Method**: POST
- **URL**: `https://graph.facebook.com/v23.0/647078395158968/messages`
- **Timestamp**: 2025-07-16 15:29:25
- **Guest ID**: 1
- **Direction**: request

**Headers:**
```json
{
  "Content-Type": "application/json",
  "Authorization": "Bearer [REDACTED]"
}
```

**Request Payload:**
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

### 2. Successful Template Message Response
**Response Details:**
- **Status Code**: 200
- **Timestamp**: 2025-07-16 15:29:26
- **Guest ID**: 1
- **Direction**: response

**Response Payload:**
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
      "id": "wamid.HBgMOTcxNTA5MzY0MTc4FQIAERgSMzg4NzUxNDEzRDBGQ0E3N0RCAA==",
      "message_status": "accepted"
    }
  ]
}
```

### 3. Failed Template Message Request (Missing Parameter)
**Request Details:**
- **Method**: POST
- **URL**: `https://graph.facebook.com/v23.0/647078395158968/messages`
- **Timestamp**: 2025-07-16 15:19:58
- **Guest ID**: 1
- **Direction**: request

**Request Payload:**
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
            "text": "Madhav Sharma"
          }
        ]
      }
    ]
  }
}
```

### 4. Error Response (400 Bad Request)
**Response Details:**
- **Status Code**: 400
- **Timestamp**: 2025-07-16 15:19:58
- **Guest ID**: 1
- **Direction**: response

**Response Payload:**
```json
{
  "error": {
    "message": "(#100) Invalid parameter",
    "type": "OAuthException",
    "code": 100,
    "error_data": {
      "messaging_product": "whatsapp",
      "details": "Parameter name is missing or empty"
    },
    "fbtrace_id": "AtNAiNFtBJ0eRXu9pUoX0HW"
  }
}
```

---

## Webhook Payloads

### 1. Message Sent Status
**Event Type**: sent
**Timestamp**: 2025-07-16 15:29:29

**Webhook Payload:**
```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "1908606383273862",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "15556489771",
              "phone_number_id": "647078395158968"
            },
            "statuses": [
              {
                "id": "wamid.HBgMOTcxNTA5MzY0MTc4FQIAERgSMzg4NzUxNDEzRDBGQ0E3N0RCAA==",
                "status": "sent",
                "timestamp": "1752679768",
                "recipient_id": "971509364178",
                "conversation": {
                  "id": "2da21bfdb4f91acd479f8ae999a8f03f",
                  "expiration_timestamp": "1752679768",
                  "origin": {
                    "type": "utility"
                  }
                },
                "pricing": {
                  "billable": true,
                  "pricing_model": "PMP",
                  "category": "utility",
                  "type": "regular"
                }
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ]
}
```

### 2. Message Delivered Status
**Event Type**: delivered
**Timestamp**: 2025-07-16 15:29:32

**Webhook Payload:**
```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "1908606383273862",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "15556489771",
              "phone_number_id": "647078395158968"
            },
            "statuses": [
              {
                "id": "wamid.HBgMOTcxNTA5MzY0MTc4FQIAERgSMzg4NzUxNDEzRDBGQ0E3N0RCAA==",
                "status": "delivered",
                "timestamp": "1752679771",
                "recipient_id": "971509364178",
                "conversation": {
                  "id": "2da21bfdb4f91acd479f8ae999a8f03f",
                  "origin": {
                    "type": "utility"
                  }
                },
                "pricing": {
                  "billable": true,
                  "pricing_model": "PMP",
                  "category": "utility",
                  "type": "regular"
                }
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ]
}
```

### 3. Message Read Status
**Event Type**: read
**Timestamp**: 2025-07-16 15:29:50

**Webhook Payload:**
```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "1908606383273862",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "15556489771",
              "phone_number_id": "647078395158968"
            },
            "statuses": [
              {
                "id": "wamid.HBgMOTcxNTA5MzY0MTc4FQIAERgSMzg4NzUxNDEzRDBGQ0E3N0RCAA==",
                "status": "read",
                "timestamp": "1752679790",
                "recipient_id": "971509364178"
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ]
}
```

### 4. Incoming Button Response
**Event Type**: incoming_message
**Timestamp**: 2025-07-16 15:29:59

**Webhook Payload:**
```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "1908606383273862",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "15556489771",
              "phone_number_id": "647078395158968"
            },
            "contacts": [
              {
                "profile": {
                  "name": "Madhav"
                },
                "wa_id": "971509364178"
              }
            ],
            "messages": [
              {
                "context": {
                  "from": "15556489771",
                  "id": "wamid.HBgMOTcxNTA5MzY0MTc4FQIAERgSMzg4NzUxNDEzRDBGQ0E3N0RCAA=="
                },
                "from": "971509364178",
                "id": "wamid.HBgMOTcxNTA5MzY0MTc4FQIAEhggRUU2RjQ3M0U0MkEzMDBBMzg1MTc5MkQ4QTAyMjEzQzUA",
                "timestamp": "1752679799",
                "type": "button",
                "button": {
                  "payload": "Send me the invite",
                  "text": "Send me the invite"
                }
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ]
}
```

**Webhook Headers (Common for all webhooks):**
```json
{
  "host": "vectorreasoning.space",
  "user-agent": "facebookexternalua",
  "content-length": "[varies]",
  "accept": "*/*",
  "accept-encoding": "deflate, gzip",
  "content-type": "application/json",
  "x-forwarded-for": "[IP Address]",
  "x-forwarded-host": "vectorreasoning.space",
  "x-forwarded-proto": "https",
  "x-hub-signature": "sha1=[signature]",
  "x-hub-signature-256": "sha256=[signature]"
}
```

---

## Guest Invitation Flow

### Guest Record
The following guest record shows the complete flow of sending a WhatsApp invitation:

```json
{
  "id": 1,
  "prefix": null,
  "first_name": "Madhav",
  "last_name": "Sharma",
  "greeting_name": null,
  "phone": "+971509364178",
  "group_id": "madhav",
  "is_group_primary": 1,
  "ready": 1,
  "sent_to_whatsapp": "succeeded",
  "api_call_at": "2025-07-16 15:29:25",
  "sent_at": null,
  "delivered_at": null,
  "read_at": null,
  "responded_with_button": 0,
  "message_id": "wamid.HBgMOTcxNTA5MzY0MTc4FQIAERgSMzg4NzUxNDEzRDBGQ0E3N0RCAA==",
  "created_at": "2025-07-16 14:57:04",
  "updated_at": "2025-07-16 15:29:26"
}
```

### Flow Summary:
1. **Guest Created**: Guest record created at 14:57:04
2. **Ready Status**: Guest marked as ready (ready = 1)
3. **API Call**: WhatsApp API call made at 15:29:25
4. **Message Sent**: Template message sent successfully
5. **Status Updates**: Message progresses through sent → delivered → read statuses
6. **User Response**: User clicks "Send me the invite" button
7. **Success**: Guest record updated with succeeded status and message ID

### Key Fields Explained:
- **group_id**: Identifies the guest group (e.g., "madhav")
- **is_group_primary**: Indicates if this is the primary contact for the group
- **ready**: Boolean flag indicating if the guest is ready to receive invitations
- **sent_to_whatsapp**: Status of WhatsApp delivery (pending/succeeded/failed)
- **message_id**: WhatsApp message ID for tracking
- **responded_with_button**: Tracks if the guest responded to the invitation button

---

## Notes

1. **Authentication**: All API calls use Bearer token authentication (redacted in samples)
2. **Phone Format**: Phone numbers include country code with '+' prefix
3. **Template Messages**: Using "wedding_pre_invite_1" template with personalized name parameter
4. **Webhook Security**: Webhooks include SHA1 and SHA256 signatures for verification
5. **Message Flow**: Messages progress through: accepted → sent → delivered → read
6. **Error Handling**: API returns detailed error messages with error codes and trace IDs