# LFD Clock - Project State

## What This Is
Logistics SaaS that tracks container Last Free Days (LFD) and sends SMS alerts before demurrage fees hit.

### Core Flow
```
Email with PDF → Postmark Webhook → Gemini AI Parse → Supabase → Twilio SMS
```

---

## Live Infrastructure

| Service | URL | Platform |
|---------|-----|----------|
| Frontend | https://lfdclock.com | Vercel |
| Backend | https://api.lfdclock.com | Railway |
| Database | Supabase (PostgreSQL) | khdoitcwioqjwxqorgtr.supabase.co |

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19, Tailwind CSS, Shadcn/UI, CRACO |
| Backend | FastAPI (Python), Uvicorn |
| Database | Supabase (PostgreSQL) via `supabase-py` v2 |
| AI/ML | Google Gemini (`google-generativeai` v0.8.6) — model: `gemini-2.5-flash-lite` |
| SMS | Twilio (trial account — must verify recipient numbers) |
| Email Inbound | Postmark Inbound Webhook |
| Auth | JWT (PyJWT) + bcrypt — NOT Supabase Auth |

---

## Migration History
Originally built on Emergent platform with:
- MongoDB (motor async driver) → **migrated to Supabase**
- `emergentintegrations` library → **migrated to `google-generativeai`**
- Emergent preview domain → **migrated to lfdclock.com**
- `@emergentbase/visual-edits` frontend package → **removed**

---

## Backend Key Patterns

### Supabase async wrapper
All Supabase calls are sync but wrapped with `asyncio.to_thread`:
```python
async def sb(query):
    result = await asyncio.to_thread(lambda: query.execute())
    if result is None:
        class _Empty:
            data = None
        return _Empty()
    return result
```
Uses **service role key** (bypasses RLS).

### Gemini helpers
Two sync functions wrapped async: `call_gemini_text` and `call_gemini_pdf`.

### Background reminders
`asyncio.create_task` runs every 5 min checking pending reminders table.

---

## Environment Variables

### Backend (Railway)
```
SUPABASE_URL=https://khdoitcwioqjwxqorgtr.supabase.co
SUPABASE_SERVICE_KEY=...
JWT_SECRET=...
GEMINI_API_KEY=...
TWILIO_ACCOUNT_SID=AC4e1abe8925f4b98749fb922cb52866cb
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+14178043751
CORS_ORIGINS=https://lfdclock.com,https://www.lfdclock.com,http://localhost:3000
```

### Frontend (Vercel)
```
REACT_APP_BACKEND_URL=https://api.lfdclock.com
DISABLE_ESLINT_PLUGIN=true
```

### Local dev
```
# frontend/.env
REACT_APP_BACKEND_URL=http://localhost:8001
WDS_SOCKET_PORT=3000

# backend/.env — same as Railway but with localhost CORS
```

---

## Supabase Tables
- `users` — auth, company info, inbound_prefix, notify_settings
- `shipments` — container tracking data
- `reminders` — scheduled SMS reminders (48h/24h/12h/6h before LFD)
- `sms_logs` — Twilio send history

RLS is **disabled** on all tables (service role key used).

---

## DNS (Cloudflare)
- `lfdclock.com` → A record `216.198.79.1` (Vercel, DNS only/grey cloud)
- `www.lfdclock.com` → CNAME `cname.dns.vercel-dns-017.com` (DNS only)
- `api.lfdclock.com` → CNAME pointing to Railway (DNS only)
- `inbound.lfdclock.com` → MX records for Postmark

---

## Postmark
- Inbound domain: `@inbound.lfdclock.com`
- Webhook URL: `https://api.lfdclock.com/api/inbound-lfd`
- Each user gets a unique `inbound_prefix` (e.g. `acme-logistics@inbound.lfdclock.com`)

---

## Known Limitations / Next Steps
1. Twilio is trial — upgrade to paid to SMS any number
2. No Stripe/payments yet
3. No admin dashboard
4. Minor UI bugs to fix
