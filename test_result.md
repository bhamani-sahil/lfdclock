<<<<<<< HEAD
"# LFD Clock - Technical Documentation

## Project Overview

**LFD Clock** is a Logistics SaaS application that helps freight forwarders, 3PLs, and drayage brokers avoid demurrage fees by automatically tracking container Last Free Days (LFD) and sending SMS alerts before deadlines.

### Core Flow
```
Email with PDF → Postmark Webhook → Gemini AI Parse → MongoDB → Twilio SMS
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19, Tailwind CSS, Shadcn/UI, Lucide Icons |
| Backend | FastAPI (Python 3.11), Uvicorn |
| Database | MongoDB (via `motor` async driver) |
| AI/ML | Google Gemini 2.5 Flash (PDF/text parsing) |
| SMS | Twilio |
| Email Inbound | Postmark Inbound Webhook |
| Auth | JWT (PyJWT) |

---

## Directory Structure

```
/app/
├── backend/
│   ├── server.py              # Main FastAPI app (ALL endpoints, models, logic)
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Backend environment variables
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── auth/
│   │   │   │   ├── LoginPage.js
│   │   │   │   └── SignupPage.js
│   │   │   ├── dashboard/
│   │   │   │   └── DashboardPage.js    # Main dashboard (1100+ lines)
│   │   │   ├── legal/
│   │   │   │   ├── PrivacyPolicyPage.js
│   │   │   │   └── TermsOfServicePage.js
│   │   │   ├── ui/                      # Shadcn components
│   │   │   ├── LandingPage.js           # Public homepage
│   │   │   ├── CountdownTimer.js
│   │   │   └── TrafficLight.js
│   │   ├── context/
│   │   │   └── AuthContext.js           # Auth state management
│   │   ├── App.js                       # React Router config
│   │   └── index.css                    # Global styles + custom CSS
│   ├── package.json
│   └── .env                             # Frontend environment variables
└── memory/
    └── PRD.md                           # Product requirements
```

---

## Environment Variables

### Backend (`/app/backend/.env`)

```env
# Database
MONGO_URL=mongodb://localhost:27017        # ⚠️ CHANGE FOR PRODUCTION
DB_NAME=lfd_clock

# Security
JWT_SECRET=your-secret-key                 # ⚠️ CHANGE FOR PRODUCTION

# CORS
CORS_ORIGINS=https://your-domain.com       # ⚠️ CHANGE FOR PRODUCTION

# Twilio SMS
TWILIO_ACCOUNT_SID=AC4e1abe8925f4b98749fb922cb52866cb
TWILIO_AUTH_TOKEN=6a426795161d3a06f0b6084845526e58
TWILIO_PHONE_NUMBER=+14178043751
# ⚠️ TWILIO IS TRIAL ACCOUNT - must verify recipient numbers manually

# AI (Gemini via Emergent)
EMERGENT_LLM_KEY=your-emergent-key         # Used for Gemini API calls
```

### Frontend (`/app/frontend/.env`)

```env
REACT_APP_BACKEND_URL=https://logistics-lfd.preview.emergentagent.com  # ⚠️ CHANGE FOR PRODUCTION
WDS_SOCKET_PORT=443
```

---

## Third-Party Integrations

### 1. Postmark (Inbound Email)

**Purpose**: Receives forwarded emails with PDF attachments containing LFD notices.

**Webhook Endpoint**: `POST /api/inbound-lfd`

**Current Configuration**:
- Inbound domain: `@inbound.lfdclock.com`
- Webhook URL: `https://logistics-lfd.preview.emergentagent.com/api/inbound-lfd`

**⚠️ PRODUCTION CHANGES NEEDED**:
- Update webhook URL in Postmark dashboard to production domain
- MX records for `inbound.lfdclock.com` must point to Postmark

**Postmark sends JSON like**:
```json
{
  \"From\": \"carrier@shipping.com\",
  \"To\": \"company-name@inbound.lfdclock.com\",
  \"Subject\": \"Arrival Notice\",
  \"TextBody\": \"...\",
  \"HtmlBody\": \"...\",
  \"Attachments\": [
    {
      \"Name\": \"arrival_notice.pdf\",
      \"ContentType\": \"application/pdf\",
      \"Content\": \"base64-encoded-pdf\"
    }
  ]
}
```

---

### 2. Twilio (SMS)

**Purpose**: Sends real-time SMS alerts for new shipments and LFD reminders.

**Current Account**: TRIAL (limited to verified numbers only)

**Credentials**:
- Account SID: `AC4e1abe8925f4b98749fb922cb52866cb`
- Auth Token: `6a426795161d3a06f0b6084845526e58`
- Phone Number: `+14178043751`

**⚠️ PRODUCTION CHANGES NEEDED**:
- Upgrade Twilio to paid account to send SMS to any number
- Currently must manually verify each recipient in Twilio Console → Verified Caller IDs

**SMS Triggers**:
1. New shipment created (instant alert)
2. LFD updated (instant alert)
3. Scheduled reminders: 48h, 24h, 12h, 6h before LFD

---

### 3. Google Gemini (AI Parsing)

**Purpose**: Extracts container_number, last_free_day, carrier_name from emails/PDFs.

**Model**: `gemini-2.5-flash-preview-05-20`

**Integration**: Via `emergentintegrations` library with Emergent LLM Key

**Usage in code** (`server.py`):
```python
from emergentintegrations.llm.gemini import GeminiChat

chat = GeminiChat(
    emergent_api_key=EMERGENT_LLM_KEY,
    model=\"gemini-2.5-flash-preview-05-20\"
)
response = chat.send_message(prompt)
```

**⚠️ NOTE**: Uses Emergent LLM Key (universal key), not direct Google API key.

---

## Database Schema (MongoDB)

### Collection: `users`
```json
{
  \"_id\": \"ObjectId\",
  \"email\": \"user@company.com\",
  \"hashed_password\": \"bcrypt_hash\",
  \"company_name\": \"Acme Logistics\",
  \"phone_number\": \"+15551234567\",
  \"inbound_email\": \"acme-logistics@inbound.lfdclock.com\",
  \"lifetime_fees_avoided\": 900,
  \"notify_settings\": {
    \"notify_48h\": true,
    \"notify_24h\": true,
    \"notify_12h\": true,
    \"notify_6h\": true
  },
  \"created_at\": \"2025-12-15T10:00:00Z\"
}
```

### Collection: `shipments`
```json
{
  \"_id\": \"ObjectId\",
  \"user_id\": \"user_object_id_string\",
  \"container_number\": \"MSCU1234567\",
  \"vessel_name\": \"MSC Aurora\",
  \"carrier\": \"MSC\",
  \"arrival_date\": \"2025-12-15T00:00:00Z\",
  \"last_free_day\": \"2025-12-20T23:59:59Z\",
  \"status\": \"warning\",           // safe, warning, critical, expired, picked_up
  \"picked_up\": false,
  \"picked_up_at\": null,
  \"source\": \"email\",             // email, pdf_attachment, direct_upload, manual
  \"created_at\": \"2025-12-15T10:00:00Z\"
}
```

### Collection: `reminders`
```json
{
  \"_id\": \"ObjectId\",
  \"shipment_id\": \"shipment_object_id_string\",
  \"user_id\": \"user_object_id_string\",
  \"hours_before\": 48,
  \"schedule_time\": \"2025-12-18T23:59:59Z\",
  \"status\": \"pending\",           // pending, sent, failed
  \"sent_at\": null,
  \"created_at\": \"2025-12-15T10:00:00Z\"
}
```

### Collection: `sms_logs`
```json
{
  \"_id\": \"ObjectId\",
  \"user_id\": \"user_object_id_string\",
  \"shipment_id\": \"shipment_object_id_string\",
  \"to_number\": \"+15551234567\",
  \"message\": \"LFD Alert: MSCU1234567...\",
  \"status\": \"sent\",              // sent, failed
  \"twilio_sid\": \"SM...\",
  \"error\": null,
  \"created_at\": \"2025-12-15T10:00:00Z\"
}
```

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/signup` | Create new user account |
| POST | `/api/auth/login` | Login, returns JWT token |
| GET | `/api/users/me` | Get current user profile |

### Shipments
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/shipments` | Get all user's shipments |
| POST | `/api/shipments` | Create shipment manually |
| DELETE | `/api/shipments/{id}` | Delete shipment |
| GET | `/api/shipments/stats` | Get shipment statistics |
| POST | `/api/shipments/{id}/mark-picked-up` | Mark as picked up (+$300 saved) |
| POST | `/api/shipments/{id}/share-trucker` | SMS shipment details to trucker |
| GET | `/api/shipments/{id}/carrier-portal` | Get carrier payment portal URL |

### Inbound Processing
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/inbound-lfd` | **Postmark webhook** - receives emails |
| POST | `/api/upload/pdf` | Direct PDF upload from dashboard |
| POST | `/api/test/email-sms` | Test email parsing + SMS |

### Settings
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/settings/notifications` | Get notification preferences |
| PUT | `/api/settings/notifications` | Update notification preferences |

### Demo/Testing
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/demo/seed` | Create demo shipments |
| GET | `/api/health` | Health check |

---

## Background Tasks

### Automated Reminder System

Located in `server.py`, runs as an `asyncio` background task every 5 minutes:

```python
async def check_and_send_reminders():
    # Runs every 5 minutes (300 seconds)
    # Checks for pending reminders where schedule_time <= now
    # Sends SMS via Twilio
    # Updates reminder status to 'sent' or 'failed'
```

**Reminder Creation**: When a shipment is created/updated, reminders are scheduled for 48h, 24h, 12h, 6h before LFD (based on user's notify_settings).

---

## Key URLs That Need Production Updates

| Current (Preview) | Change To |
|-------------------|-----------|
| `https://logistics-lfd.preview.emergentagent.com` | `https://lfdclock.com` or your domain |
| `@inbound.lfdclock.com` | Keep same (already your domain) |
| Postmark webhook URL | Update in Postmark dashboard |

---

## Frontend Routes

| Path | Component | Auth Required |
|------|-----------|---------------|
| `/` | LandingPage | No |
| `/login` | LoginPage | No |
| `/signup` | SignupPage | No |
| `/dashboard` | DashboardPage | Yes |
| `/settings` | DashboardPage (settings view) | Yes |
| `/privacy` | PrivacyPolicyPage | No |
| `/terms` | TermsOfServicePage | No |

---

## Design System

### Colors
```css
--accent-orange: #FF4F00        /* Primary accent */
--background: #FAF7F2           /* Paper/cream background */
--surface: #FFFFFF              /* Cards */
--border: #E8E2D9               /* Borders */
--text: #1A1A1A                 /* Primary text */
--text-muted: #666666           /* Secondary text */
```

### Status Colors (Traffic Light)
```css
Safe (>48h):     #10B981 (green)
Warning (24-48h): #F59E0B (amber)
Critical (<24h):  #EF4444 (red)
Expired:          #6B7280 (gray)
Picked Up:        #10B981 (green)
```

---

## Known Limitations

1. **Twilio Trial**: Must manually verify each recipient phone number
2. **Single User per Account**: No team/multi-user support yet
3. **No Payment Integration**: Stripe not implemented yet
4. **No Admin Dashboard**: Platform owner can't view all users/stats yet

---

## Running Locally

### Backend
```bash
cd /app/backend
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend
```bash
cd /app/frontend
yarn install
yarn start
```

### Services (Production)
Managed by Supervisor:
- Backend: Port 8001
- Frontend: Port 3000
- Ingress routes `/api/*` to backend, everything else to frontend

---

## Testing

### Test Email Parsing
```bash
curl -X POST \"https://your-domain.com/api/test/email-sms\" \
  -H \"Authorization: Bearer YOUR_TOKEN\" \
  -H \"Content-Type: application/json\" \
  -d '{
    \"email_content\": \"Container: MSCU1234567
Vessel: MSC Aurora
LFD: December 20, 2025\",
    \"phone_number\": \"+15551234567\"
  }'
```

### Test Postmark Webhook
```bash
curl -X POST \"https://your-domain.com/api/inbound-lfd\" \
  -H \"Content-Type: application/json\" \
  -d '{
    \"From\": \"test@carrier.com\",
    \"To\": \"company@inbound.lfdclock.com\",
    \"Subject\": \"Arrival Notice\",
    \"TextBody\": \"Container: MSCU1234567, LFD: Dec 20, 2025\"
  }'
```

---

## Contact Information (Displayed on Website)

- Email: info@lfdclock.com
- Phone: +1 825 760 7425

---

## Next Development Tasks

1. **P1**: Build Admin Dashboard (view all users, platform stats, SMS usage)
2. **P2**: Multi-phone number support per user
3. **P2**: Stripe payment integration
4. **P3**: Automated trucker dispatch
"
=======
#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================
>>>>>>> 655c419beed107eeca6880d64fd372fe152b25b6
