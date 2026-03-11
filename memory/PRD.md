# LFD Clock - Product Requirements Document

## Original Problem Statement
Build a Logistics SaaS called "LFD Clock" with:
- Unique inbound email per user for forwarding freight notifications
- Email/PDF parsing using Gemini AI to extract shipment data
- Data extraction for: container_number, vessel_name, arrival_date, last_free_day (LFD)
- Automated SMS notifications at 48h, 24h, 12h, and 6h before LFD expires
- Dashboard with "Traffic Light" system (Green=Safe, Yellow=Warning, Red=Critical)
- Settings for notification interval toggles

## User Personas
1. **Freight Forwarder** - Primary user tracking multiple container LFDs to avoid demurrage
2. **Logistics Coordinator** - Manages shipment schedules and pickup deadlines
3. **Operations Manager** - Oversees team's container tracking and compliance

## Core Requirements (Static)
- JWT-based authentication
- Unique forwarding email generation per user (fwd-xxxxx@lfdclock.com)
- Shipment CRUD operations
- Traffic light status system based on hours remaining
- Real-time countdown timers
- Notification settings management

## Tech Stack
- **Frontend**: React 19, Tailwind CSS, Shadcn/UI, Lucide Icons
- **Backend**: FastAPI, Python 3.11
- **Database**: MongoDB
- **AI**: Gemini 2.5 Flash (via Emergent LLM key)
- **SMS**: Twilio (MOCKED for demo)

## What's Been Implemented (March 11, 2026)

### Backend
- [x] User authentication (signup/login) with JWT tokens
- [x] Unique forwarding email generation per user
- [x] Shipments CRUD (create, read, delete)
- [x] Shipment stats endpoint with status breakdown
- [x] Email parsing endpoint with Gemini AI integration
- [x] Notification settings CRUD
- [x] SMS notification check endpoint (MOCKED)
- [x] Demo data seeding endpoint

### Frontend
- [x] Landing page with hero, features, CTA sections
- [x] Login/Signup pages with form validation
- [x] Dashboard with traffic light shipment cards
- [x] Real-time countdown timers (d h m s format)
- [x] Status stats cards (Total, Safe, Warning, Critical, Expired)
- [x] Add Shipment dialog for manual entry
- [x] Delete shipment functionality
- [x] Settings page with notification toggles (48h, 24h, 12h, 6h)
- [x] User menu dropdown
- [x] Copy forwarding email functionality

## Mocked/Simulated Features
- **SMS Notifications**: Logged to database, not sent via Twilio
- **Email Inbound**: Simulated endpoint, no real SendGrid/Postmark webhook

## Prioritized Backlog

### P0 - Core (Completed)
- [x] Authentication flow
- [x] Dashboard with traffic light system
- [x] Shipment management
- [x] Notification settings

### P1 - Next Phase
- [ ] Real Twilio SMS integration
- [ ] Real email inbound webhook (SendGrid/Postmark)
- [ ] PDF attachment parsing
- [ ] Bulk shipment import

### P2 - Future Enhancements
- [ ] Team/organization support
- [ ] Reporting and analytics
- [ ] Mobile app (React Native)
- [ ] Webhook notifications (Slack, email)
- [ ] Demurrage cost calculator

## Next Action Items
1. Integrate real Twilio SMS (user needs API credentials)
2. Set up SendGrid Inbound Parse webhook for @lfdclock.com domain
3. Add PDF document parsing with Gemini Vision
4. Implement automated cron job for notification checking
