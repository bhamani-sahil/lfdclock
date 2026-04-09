-- LFD Clock - Supabase Schema
-- Run this entire file in Supabase Dashboard → SQL Editor

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    company_name TEXT NOT NULL,
    phone TEXT,
    forwarding_email TEXT,
    inbound_email TEXT,
    inbound_prefix TEXT,
    lifetime_fees_avoided INTEGER DEFAULT 0,
    notification_settings JSONB DEFAULT '{"notify_48h": true, "notify_24h": true, "notify_12h": true, "notify_6h": true}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Shipments table
CREATE TABLE IF NOT EXISTS shipments (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    container_number TEXT NOT NULL,
    vessel_name TEXT,
    carrier TEXT,
    arrival_date TEXT,
    last_free_day TEXT NOT NULL,
    notes TEXT,
    status TEXT DEFAULT 'safe',
    hours_remaining FLOAT DEFAULT 0,
    picked_up BOOLEAN DEFAULT FALSE,
    picked_up_at TEXT,
    fees_avoided INTEGER DEFAULT 0,
    bill_of_lading TEXT,
    source TEXT DEFAULT 'manual',
    created_at TEXT,
    updated_at TEXT
);

-- Reminders table
CREATE TABLE IF NOT EXISTS reminders (
    id UUID PRIMARY KEY,
    shipment_id UUID REFERENCES shipments(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    container_number TEXT,
    reminder_type TEXT,
    hours_before INTEGER,
    schedule_time TEXT,
    lfd TEXT,
    status TEXT DEFAULT 'pending',
    processed_at TEXT,
    twilio_sid TEXT,
    error TEXT,
    created_at TEXT
);

-- SMS Logs table
CREATE TABLE IF NOT EXISTS sms_logs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    shipment_id UUID,
    container_number TEXT,
    message TEXT,
    notification_type TEXT,
    sent_at TEXT,
    status TEXT,
    twilio_sid TEXT,
    trucker_phone TEXT
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_shipments_user_id ON shipments(user_id);
CREATE INDEX IF NOT EXISTS idx_shipments_container ON shipments(container_number);
CREATE INDEX IF NOT EXISTS idx_reminders_status ON reminders(status);
CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON reminders(user_id);
CREATE INDEX IF NOT EXISTS idx_sms_logs_user_id ON sms_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_users_inbound_prefix ON users(inbound_prefix);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Disable Row Level Security (service role key bypasses it anyway, but explicit is cleaner)
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE shipments DISABLE ROW LEVEL SECURITY;
ALTER TABLE reminders DISABLE ROW LEVEL SECURITY;
ALTER TABLE sms_logs DISABLE ROW LEVEL SECURITY;
