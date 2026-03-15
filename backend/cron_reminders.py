#!/usr/bin/env python3
"""
LFD Clock Reminder Cron Job
Run this every hour via system cron or a scheduler.

Example crontab entry:
0 * * * * /usr/bin/python3 /app/backend/cron_reminders.py >> /var/log/lfd_cron.log 2>&1
"""

import requests
import os
from datetime import datetime

BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:8001')

def run_reminder_check():
    """Call the reminder processing endpoint"""
    print(f"[{datetime.now().isoformat()}] Running reminder check...")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/cron/process-reminders",
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  Processed: {result.get('processed', 0)}")
            print(f"  Sent: {result.get('sent', 0)}")
            print(f"  Failed: {result.get('failed', 0)}")
            print(f"  Skipped: {result.get('skipped', 0)}")
        else:
            print(f"  Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"  Exception: {str(e)}")

if __name__ == "__main__":
    run_reminder_check()
