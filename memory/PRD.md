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
- Unique forwarding email generation per user (company@inbound.lfdclock.com)
- Shipment CRUD operations
- Traffic light status system based on hours remaining
- Real-time countdown timers
- Notification settings management

## Tech Stack
- **Frontend**: React 19, Tailwind CSS, Shadcn/UI, Lucide Icons
- **Backend**: FastAPI, Python 3.11
- **Database**: MongoDB (motor async driver)
- **AI**: Gemini 2.5 Flash (via Emergent LLM key)
- **SMS**: Twilio (LIVE integration)
- **Email Inbound**: Postmark Webhook

## What's Been Implemented

### Phase 1 - MVP (Completed)
- [x] User authentication (signup/login) with JWT tokens
- [x] Unique forwarding email generation per user
- [x] Shipments CRUD (create, read, delete)
- [x] Shipment stats endpoint with status breakdown
- [x] Email parsing endpoint with Gemini AI integration
- [x] Notification settings CRUD
- [x] Dashboard with traffic light shipment cards
- [x] Real-time countdown timers (d h m s format)
- [x] Status stats cards (Total, Safe, Warning, Critical, Expired)
- [x] Settings page with notification toggles

### Phase 2 - Real Integrations (Completed)
- [x] Real Twilio SMS integration
- [x] Postmark inbound email webhook (/api/inbound-lfd)
- [x] Asynchronous PDF/email parsing with background tasks
- [x] Automated reminder system (48h, 24h, 12h, 6h alerts via asyncio)
- [x] Drag & drop PDF upload on dashboard
- [x] "Picked Up" status with persistent fees savings counter
- [x] "Trucker Share" SMS button
- [x] Carrier portal payment links
- [x] Active/Picked Up/All tabs filtering

### Phase 3 - Landing Page Redesign (Completed Dec 2025)
- [x] "Next-Gen" SaaS design with dark theme (#0B0B0B)
- [x] Safety Orange accent color (#FF4F00)
- [x] Inter font family
- [x] Hero section with orange-to-white gradient headline
- [x] "Join the Beta" CTA with glass-morphism hover effect
- [x] Social proof carrier strip (MAERSK, MSC, CMA CGM, etc.)
- [x] Vertical "How It Works" layout with numbered steps
- [x] Two-tier pricing cards (Starter/Enterprise) with glow effects
- [x] Minimalist footer with contact info
- [x] Mobile responsive design

### Legal Pages (Completed)
- [x] Privacy Policy page (/privacy)
- [x] Terms of Service page (/terms)

## Key Database Schema
- **users**: {id, email, hashed_password, company_name, phone_number, inbound_email, lifetime_fees_avoided, notify_settings}
- **shipments**: {id, user_id, container_number, lfd, carrier, status, picked_up, picked_up_at, created_at, source}
- **reminders**: {id, shipment_id, user_id, schedule_time, status, hours_before}
- **sms_logs**: {id, user_id, to_number, message, status, created_at}

## Key API Endpoints
- POST /api/auth/signup - User registration
- POST /api/auth/login - User login
- GET /api/users/me - Get current user details
- GET /api/shipments - Get all shipments for current user
- POST /api/inbound-lfd - Postmark webhook for inbound emails
- POST /api/shipments/direct-upload - Drag & drop PDF upload
- POST /api/shipments/{id}/picked-up - Mark shipment as picked up
- POST /api/shipments/{id}/share-trucker - Send shipment to trucker

## Known Limitations
- **Twilio Trial Account**: Can only send SMS to pre-verified phone numbers. User needs to upgrade for production use.

## Prioritized Backlog

### P0 - Completed
- [x] Full MVP with all core features
- [x] Real integrations (Twilio, Postmark, Gemini)
- [x] Landing page redesign

### P1 - Next Phase
- [ ] **Admin Dashboard** - View all users, platform stats, revenue, SMS usage
- [ ] Multi-phone number support per user
- [ ] Custom alert schedules

### P2 - Future Enhancements
- [ ] Automated Trucker Dispatch (email/SMS/call trucking company)
- [ ] Stripe payment integration for subscriptions
- [ ] Team/organization support
- [ ] Reporting and analytics
- [ ] Webhook notifications (Slack, email)
- [ ] Demurrage cost calculator

## Next Action Items
1. Build Admin Dashboard for platform owner
2. Deploy to production (lfdclock.com)
3. Upgrade Twilio to paid account for unrestricted SMS
4. Configure Postmark MX records for lfdclock.com domain
