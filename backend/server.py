from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import asyncio
import os
import logging
import json
import re
import tempfile
import uuid
import hashlib
import base64
from pathlib import Path
from pydantic import BaseModel, ConfigDict, EmailStr
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import jwt
from passlib.context import CryptContext
from supabase import create_client, Client
from twilio.rest import Client as TwilioClient
import google.generativeai as genai

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== CONNECTIONS ====================

# Supabase
SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_SERVICE_KEY']
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# JWT
JWT_SECRET = os.environ.get('JWT_SECRET', 'lfd-clock-secret')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Twilio
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Gemini
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(title="LFD Clock API")
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# ==================== CARRIER PORTALS ====================

CARRIER_PORTALS = {
    "MSC": "https://www.msc.com/track-a-shipment",
    "MAERSK": "https://www.maersk.com/tracking",
    "CMA CGM": "https://www.cma-cgm.com/ebusiness/tracking",
    "HAPAG-LLOYD": "https://www.hapag-lloyd.com/en/online-business/track/track-by-container-solution.html",
    "EVERGREEN": "https://www.evergreen-line.com/twe1/jsp/TW1_Tracking.jsp",
    "COSCO": "https://elines.coscoshipping.com/ebusiness/cargoTracking",
    "ONE": "https://ecomm.one-line.com/ecom/CUP_HOM_3301GS.do",
    "YANG MING": "https://www.yangming.com/e-service/track_trace/track_trace_cargo_tracking.aspx",
    "ZIM": "https://www.zim.com/tools/track-a-shipment",
    "DEFAULT": "https://www.google.com/search?q=container+tracking"
}

# ==================== MODELS ====================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    company_name: str
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class NotificationSettings(BaseModel):
    notify_48h: bool = True
    notify_24h: bool = True
    notify_12h: bool = True
    notify_6h: bool = True

class NotificationSettingsUpdate(BaseModel):
    notify_48h: Optional[bool] = None
    notify_24h: Optional[bool] = None
    notify_12h: Optional[bool] = None
    notify_6h: Optional[bool] = None

class ShipmentCreate(BaseModel):
    container_number: str
    vessel_name: str
    arrival_date: str
    last_free_day: str
    notes: Optional[str] = None

class EmailParseRequest(BaseModel):
    subject: str
    body: str
    from_email: str

class TestEmailSMSRequest(BaseModel):
    email_content: str
    phone_number: str

class PostmarkAttachment(BaseModel):
    Name: str
    Content: str
    ContentType: str
    ContentLength: Optional[int] = None

class PostmarkInboundPayload(BaseModel):
    From: Optional[str] = None
    FromName: Optional[str] = None
    To: Optional[str] = None
    Subject: Optional[str] = None
    TextBody: Optional[str] = None
    HtmlBody: Optional[str] = None
    Attachments: Optional[List[PostmarkAttachment]] = []

    class Config:
        extra = "allow"

class TruckerShareRequest(BaseModel):
    shipment_id: str
    trucker_phone: str
    trucker_name: Optional[str] = None

# ==================== SUPABASE HELPER ====================

async def sb(query):
    """Run a synchronous supabase query in a thread pool"""
    result = await asyncio.to_thread(lambda: query.execute())
    if result is None:
        class _Empty:
            data = None
        return _Empty()
    return result

# ==================== AUTH HELPERS ====================

def generate_inbound_email(company_name: str) -> str:
    clean_name = company_name.lower().strip()
    clean_name = re.sub(r'[^a-z0-9\s-]', '', clean_name)
    clean_name = re.sub(r'[\s]+', '-', clean_name)
    clean_name = re.sub(r'-+', '-', clean_name)
    suffix = hashlib.md5(f"{company_name}{datetime.now().isoformat()}".encode()).hexdigest()[:4]
    return f"{clean_name}-{suffix}@inbound.lfdclock.com"

def generate_forwarding_email(user_id: str) -> str:
    short_id = hashlib.md5(user_id.encode()).hexdigest()[:8]
    return f"fwd-{short_id}@lfdclock.com"

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(user_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    return jwt.encode(
        {"sub": user_id, "email": email, "exp": expire},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        result = await sb(supabase.table('users').select('*').eq('id', user_id).maybe_single())
        if not result.data:
            raise HTTPException(status_code=401, detail="User not found")
        return result.data
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==================== SHIPMENT HELPERS ====================

def calculate_shipment_status(last_free_day: str) -> tuple:
    try:
        lfd = datetime.fromisoformat(last_free_day.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        hours = (lfd - now).total_seconds() / 3600
        if hours <= 0:
            return "expired", hours
        elif hours <= 24:
            return "critical", hours
        elif hours <= 48:
            return "warning", hours
        else:
            return "safe", hours
    except:
        return "unknown", 0

async def create_reminders_for_shipment(shipment_id: str, user_id: str, container_number: str, last_free_day: str, user_settings: dict):
    try:
        lfd = datetime.fromisoformat(last_free_day.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)

        # Delete existing reminders for this shipment
        await sb(supabase.table('reminders').delete().eq('shipment_id', shipment_id))

        intervals = [
            ("48h", 48, user_settings.get("notify_48h", True)),
            ("24h", 24, user_settings.get("notify_24h", True)),
            ("12h", 12, user_settings.get("notify_12h", True)),
            ("6h",  6,  user_settings.get("notify_6h",  True)),
        ]

        created = []
        for reminder_type, hours_before, enabled in intervals:
            if not enabled:
                continue
            schedule_time = lfd - timedelta(hours=hours_before)
            if schedule_time > now:
                await sb(supabase.table('reminders').insert({
                    "id": str(uuid.uuid4()),
                    "shipment_id": shipment_id,
                    "user_id": user_id,
                    "container_number": container_number,
                    "reminder_type": reminder_type,
                    "hours_before": hours_before,
                    "schedule_time": schedule_time.isoformat(),
                    "lfd": last_free_day,
                    "status": "pending",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }))
                created.append(reminder_type)
        return created
    except Exception as e:
        logger.error(f"Error creating reminders: {e}")
        return []

def get_carrier_portal(carrier_name: str) -> str:
    if not carrier_name:
        return CARRIER_PORTALS["DEFAULT"]
    carrier_upper = carrier_name.upper()
    for key in CARRIER_PORTALS:
        if key in carrier_upper:
            return CARRIER_PORTALS[key]
    return CARRIER_PORTALS["DEFAULT"]

# ==================== GEMINI HELPERS ====================

def _call_gemini_text(prompt: str) -> str:
    model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
    response = model.generate_content(prompt)
    return response.text

def _call_gemini_pdf(pdf_path: str, prompt: str) -> str:
    uploaded = genai.upload_file(pdf_path, mime_type='application/pdf')
    model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
    response = model.generate_content([uploaded, prompt])
    return response.text

async def call_gemini_text(prompt: str) -> str:
    return await asyncio.to_thread(_call_gemini_text, prompt)

async def call_gemini_pdf(pdf_path: str, prompt: str) -> str:
    return await asyncio.to_thread(_call_gemini_pdf, pdf_path, prompt)

def clean_json_response(text: str) -> dict:
    clean = text.strip()
    if clean.startswith("```"):
        parts = clean.split("```")
        if len(parts) > 1:
            clean = parts[1]
            if clean.startswith("json"):
                clean = clean[4:]
    return json.loads(clean.strip())

# ==================== SMS HELPER ====================

def send_real_sms(to_number: str, message: str) -> dict:
    if not twilio_client:
        raise HTTPException(status_code=500, detail="Twilio not configured")
    if not to_number.startswith('+'):
        to_number = '+1' + to_number
    try:
        sms = twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_number
        )
        return {"sid": sms.sid, "status": sms.status, "to": to_number}
    except Exception as e:
        logger.error(f"Twilio error: {e}")
        raise HTTPException(status_code=500, detail=f"SMS failed: {str(e)}")

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/signup")
async def signup(user_data: UserCreate):
    result = await sb(supabase.table('users').select('id').eq('email', user_data.email).maybe_single())
    if result.data:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid.uuid4())
    forwarding_email = generate_forwarding_email(user_id)
    inbound_email = generate_inbound_email(user_data.company_name)
    inbound_prefix = inbound_email.split('@')[0]

    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "password_hash": hash_password(user_data.password),
        "company_name": user_data.company_name,
        "phone": user_data.phone,
        "forwarding_email": forwarding_email,
        "inbound_email": inbound_email,
        "inbound_prefix": inbound_prefix,
        "lifetime_fees_avoided": 0,
        "notification_settings": {
            "notify_48h": True, "notify_24h": True,
            "notify_12h": True, "notify_6h": True
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    await sb(supabase.table('users').insert(user_doc))
    token = create_access_token(user_id, user_data.email)

    return {
        "token": token,
        "user": {
            "id": user_id,
            "email": user_data.email,
            "company_name": user_data.company_name,
            "phone": user_data.phone,
            "forwarding_email": forwarding_email,
            "inbound_email": inbound_email,
            "created_at": user_doc["created_at"]
        }
    }

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    result = await sb(supabase.table('users').select('*').eq('email', credentials.email).maybe_single())
    user = result.data
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user["id"], user["email"])
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "company_name": user["company_name"],
            "phone": user.get("phone"),
            "forwarding_email": user.get("forwarding_email"),
            "inbound_email": user.get("inbound_email"),
            "created_at": user["created_at"]
        }
    }

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "company_name": current_user["company_name"],
        "phone": current_user.get("phone"),
        "forwarding_email": current_user.get("forwarding_email"),
        "inbound_email": current_user.get("inbound_email"),
        "created_at": current_user["created_at"]
    }

# ==================== SHIPMENT ROUTES ====================

@api_router.get("/shipments")
async def get_shipments(current_user: dict = Depends(get_current_user)):
    result = await sb(
        supabase.table('shipments')
        .select('*')
        .eq('user_id', current_user['id'])
        .order('last_free_day', desc=False)
    )
    shipments = result.data or []

    output = []
    for s in shipments:
        if s.get("picked_up"):
            status, hours = "picked_up", 0
        else:
            status, hours = calculate_shipment_status(s.get("last_free_day", ""))
        output.append({
            "id": s.get("id", ""),
            "user_id": s.get("user_id", ""),
            "container_number": s.get("container_number", ""),
            "vessel_name": s.get("vessel_name", "Unknown"),
            "carrier": s.get("carrier", ""),
            "arrival_date": s.get("arrival_date", ""),
            "last_free_day": s.get("last_free_day", ""),
            "notes": s.get("notes"),
            "status": status,
            "hours_remaining": round(hours, 1),
            "created_at": s.get("created_at", ""),
            "source": s.get("source", "manual"),
            "picked_up": s.get("picked_up", False),
            "picked_up_at": s.get("picked_up_at"),
            "fees_avoided": s.get("fees_avoided", 0)
        })
    return output

@api_router.post("/shipments")
async def create_shipment(shipment_data: ShipmentCreate, current_user: dict = Depends(get_current_user)):
    shipment_id = str(uuid.uuid4())
    status, hours = calculate_shipment_status(shipment_data.last_free_day)

    shipment_doc = {
        "id": shipment_id,
        "user_id": current_user["id"],
        "container_number": shipment_data.container_number.upper(),
        "vessel_name": shipment_data.vessel_name,
        "arrival_date": shipment_data.arrival_date,
        "last_free_day": shipment_data.last_free_day,
        "notes": shipment_data.notes,
        "status": status,
        "hours_remaining": round(hours, 1),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "manual",
        "fees_avoided": 0,
        "picked_up": False
    }

    await sb(supabase.table('shipments').insert(shipment_doc))

    user_settings = current_user.get("notification_settings") or {}
    await create_reminders_for_shipment(
        shipment_id,
        current_user["id"],
        shipment_data.container_number.upper(),
        shipment_data.last_free_day,
        user_settings
    )

    return shipment_doc

@api_router.delete("/shipments/{shipment_id}")
async def delete_shipment(shipment_id: str, current_user: dict = Depends(get_current_user)):
    result = await sb(
        supabase.table('shipments')
        .select('id')
        .eq('id', shipment_id)
        .eq('user_id', current_user['id'])
        .maybe_single()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Shipment not found")

    await sb(supabase.table('reminders').delete().eq('shipment_id', shipment_id))
    await sb(supabase.table('shipments').delete().eq('id', shipment_id).eq('user_id', current_user['id']))

    return {"message": "Shipment deleted"}

@api_router.get("/shipments/stats")
async def get_shipment_stats(current_user: dict = Depends(get_current_user)):
    result = await sb(supabase.table('shipments').select('*').eq('user_id', current_user['id']))
    shipments = result.data or []

    user_result = await sb(supabase.table('users').select('lifetime_fees_avoided').eq('id', current_user['id']).maybe_single())
    lifetime_savings = (user_result.data or {}).get('lifetime_fees_avoided', 0)

    stats = {
        "total": len(shipments),
        "safe": 0, "warning": 0, "critical": 0, "expired": 0,
        "picked_up": 0, "active": 0,
        "potential_fees_avoided": lifetime_savings
    }

    for s in shipments:
        if s.get("picked_up"):
            stats["picked_up"] += 1
        else:
            stats["active"] += 1
            status, _ = calculate_shipment_status(s.get("last_free_day", ""))
            if status in stats:
                stats[status] += 1

    return stats

@api_router.post("/shipments/{shipment_id}/mark-picked-up")
async def mark_shipment_picked_up(shipment_id: str, current_user: dict = Depends(get_current_user)):
    result = await sb(
        supabase.table('shipments')
        .select('*')
        .eq('id', shipment_id)
        .eq('user_id', current_user['id'])
        .maybe_single()
    )
    shipment = result.data
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    _, hours_remaining = calculate_shipment_status(shipment.get("last_free_day", ""))
    fees_avoided = 300 if hours_remaining > 0 else 0

    await sb(supabase.table('shipments').update({
        "picked_up": True,
        "picked_up_at": datetime.now(timezone.utc).isoformat(),
        "fees_avoided": fees_avoided
    }).eq('id', shipment_id))

    # Increment lifetime savings
    user_result = await sb(supabase.table('users').select('lifetime_fees_avoided').eq('id', current_user['id']).maybe_single())
    current_savings = (user_result.data or {}).get('lifetime_fees_avoided', 0)
    await sb(supabase.table('users').update({
        'lifetime_fees_avoided': current_savings + fees_avoided
    }).eq('id', current_user['id']))

    await sb(supabase.table('reminders').delete().eq('shipment_id', shipment_id).eq('status', 'pending'))

    return {"message": "Container marked as picked up", "fees_avoided": fees_avoided}

# ==================== EMAIL PARSE ====================

SHIPMENT_PARSE_PROMPT = """You are a logistics document parser. Extract shipment information and return ONLY valid JSON:
{
    "container_id": "string (4 letters + 7 digits, e.g., MEDU4588210)",
    "lfd": "string (Last Free Day in YYYY-MM-DD format)",
    "carrier": "string (shipping line/carrier name)",
    "vessel": "string (vessel name if found)",
    "arrival_date": "string (arrival/ETA date in YYYY-MM-DD format if found)",
    "status": "string ('new' or 'update' based on context clues like 'revised', 'updated', 'amended')"
}
If a field cannot be found, use null. Return ONLY the JSON, no explanation."""

@api_router.post("/email/parse")
async def parse_email(email_data: EmailParseRequest, current_user: dict = Depends(get_current_user)):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")

    prompt = f"{SHIPMENT_PARSE_PROMPT}\n\nSubject: {email_data.subject}\n\nBody:\n{email_data.body}"

    try:
        raw = await call_gemini_text(prompt)
        parsed = clean_json_response(raw)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not parse email: {str(e)}")

    if not parsed.get("container_id") or not parsed.get("lfd"):
        raise HTTPException(status_code=422, detail="Missing required shipment data")

    lfd = parsed["lfd"]
    if len(lfd) == 10:
        lfd = f"{lfd}T23:59:59Z"

    shipment_id = str(uuid.uuid4())
    status, hours = calculate_shipment_status(lfd)
    container = parsed["container_id"].upper()

    shipment_doc = {
        "id": shipment_id,
        "user_id": current_user["id"],
        "container_number": container,
        "vessel_name": parsed.get("vessel") or "Unknown",
        "carrier": parsed.get("carrier") or "Unknown",
        "arrival_date": parsed.get("arrival_date") or datetime.now(timezone.utc).isoformat(),
        "last_free_day": lfd,
        "notes": f"Parsed from email: {email_data.subject}",
        "status": status,
        "hours_remaining": round(hours, 1),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "email"
    }

    await sb(supabase.table('shipments').insert(shipment_doc))
    return {"message": "Email parsed successfully", "shipment": shipment_doc}

# ==================== POSTMARK INBOUND WEBHOOK ====================

@api_router.post("/inbound-lfd")
async def postmark_inbound_webhook(payload: PostmarkInboundPayload, background_tasks: BackgroundTasks):
    try:
        to_email = payload.To or ""
        if "@inbound.lfdclock.com" not in to_email.lower():
            return {"status": "ignored", "reason": "Not an inbound.lfdclock.com address"}

        inbound_prefix = to_email.split('@')[0].lower()

        result = await sb(supabase.table('users').select('*').eq('inbound_prefix', inbound_prefix).maybe_single())
        customer = result.data
        if not customer:
            return {"status": "error", "reason": f"No customer found for {inbound_prefix}"}

        background_tasks.add_task(process_inbound_email_background, payload=payload, customer=customer, inbound_prefix=inbound_prefix)
        return {"status": "accepted", "message": "Processing in background", "customer": inbound_prefix}

    except Exception as e:
        logger.error(f"Postmark webhook error: {e}")
        return {"status": "error", "detail": str(e)}


async def process_inbound_email_background(payload: PostmarkInboundPayload, customer: dict, inbound_prefix: str):
    try:
        attachments = payload.Attachments or []
        pdf_attachments = [a for a in attachments if a.ContentType == "application/pdf" or a.Name.lower().endswith('.pdf')]

        if not pdf_attachments:
            text_content = payload.TextBody or payload.HtmlBody or ""
            if not text_content:
                logger.error(f"No PDF and no body for {inbound_prefix}")
                return
            await parse_and_process_shipment(content=text_content, content_type="text", customer=customer, source="email_body")
            return

        for attachment in pdf_attachments:
            try:
                pdf_bytes = base64.b64decode(attachment.Content)
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                    tmp.write(pdf_bytes)
                    tmp_path = tmp.name
                try:
                    await parse_and_process_shipment(content=tmp_path, content_type="pdf", customer=customer, source="pdf_attachment", filename=attachment.Name)
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
            except Exception as e:
                logger.error(f"Error processing attachment {attachment.Name}: {e}")

    except Exception as e:
        logger.error(f"Background processing error for {inbound_prefix}: {e}")


async def parse_and_process_shipment(content: str, content_type: str, customer: dict, source: str, filename: str = None):
    if not GEMINI_API_KEY:
        return {"status": "error", "reason": "Gemini API key not configured"}

    try:
        if content_type == "pdf":
            raw = await call_gemini_pdf(content, SHIPMENT_PARSE_PROMPT)
        else:
            raw = await call_gemini_text(f"{SHIPMENT_PARSE_PROMPT}\n\nDocument:\n{content}")

        try:
            parsed = clean_json_response(raw)
        except Exception as e:
            logger.error(f"JSON parse error: {e}, response: {raw[:200]}")
            return {"status": "error", "reason": "Could not parse AI response"}

        container_id = (parsed.get("container_id") or "").upper() or None
        lfd = parsed.get("lfd")
        carrier = parsed.get("carrier") or "Unknown Carrier"
        vessel = parsed.get("vessel") or "Unknown Vessel"
        arrival_date = parsed.get("arrival_date")

        if not container_id or not lfd:
            return {"status": "error", "reason": "Could not extract container ID or LFD"}

        if len(lfd) == 10:
            lfd = f"{lfd}T23:59:59Z"

        status, hours = calculate_shipment_status(lfd)

        # UPSERT logic
        existing = await sb(
            supabase.table('shipments')
            .select('*')
            .eq('user_id', customer['id'])
            .eq('container_number', container_id)
            .maybe_single()
        )
        existing_shipment = existing.data

        is_update = False
        old_lfd = None

        if existing_shipment:
            is_update = True
            old_lfd = (existing_shipment.get("last_free_day") or "")[:10] or "Unknown"
            shipment_id = existing_shipment["id"]

            await sb(supabase.table('shipments').update({
                "carrier": carrier,
                "vessel_name": vessel,
                "arrival_date": arrival_date,
                "last_free_day": lfd,
                "status": status,
                "hours_remaining": round(hours, 1),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "notes": f"Updated from {source} on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC"
            }).eq('id', shipment_id))
        else:
            shipment_id = str(uuid.uuid4())
            await sb(supabase.table('shipments').insert({
                "id": shipment_id,
                "user_id": customer["id"],
                "container_number": container_id,
                "carrier": carrier,
                "vessel_name": vessel,
                "arrival_date": arrival_date,
                "last_free_day": lfd,
                "status": status,
                "hours_remaining": round(hours, 1),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source": source
            }))

        # Send SMS
        customer_phone = customer.get("phone")
        sms_result = {"skipped": "No phone number"}
        if customer_phone:
            if is_update and old_lfd != lfd[:10]:
                msg = f"DELAY ALERT: Container {container_id} at {carrier} has a NEW Last Free Day of {lfd[:10]} (was {old_lfd}). Don't get hit with demurrage!"
            elif is_update:
                msg = f"LFD Confirmed: Container {container_id} at {carrier} - LFD remains {lfd[:10]}. {round(hours, 1)}h remaining."
            else:
                msg = f"LFD Alert: Container {container_id} at {carrier} has a Last Free Day of {lfd[:10]}. Initial tracking active!"

            try:
                sms_result = send_real_sms(customer_phone, msg)
                await sb(supabase.table('sms_logs').insert({
                    "id": str(uuid.uuid4()),
                    "user_id": customer["id"],
                    "shipment_id": shipment_id,
                    "container_number": container_id,
                    "message": msg,
                    "notification_type": "delay_alert" if is_update else "initial_tracking",
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                    "status": "sent_real",
                    "twilio_sid": sms_result.get("sid")
                }))
            except Exception as e:
                logger.error(f"SMS send error: {e}")
                sms_result = {"error": str(e)}

        return {
            "status": "success",
            "action": "updated" if is_update else "created",
            "container_id": container_id,
            "lfd": lfd[:10],
            "carrier": carrier,
            "filename": filename
        }

    except Exception as e:
        logger.error(f"Parse and process error: {e}")
        return {"status": "error", "reason": str(e)}

# ==================== NOTIFICATION SETTINGS ====================

@api_router.get("/settings/notifications")
async def get_notification_settings(current_user: dict = Depends(get_current_user)):
    settings = current_user.get("notification_settings") or {
        "notify_48h": True, "notify_24h": True, "notify_12h": True, "notify_6h": True
    }
    return settings

@api_router.put("/settings/notifications")
async def update_notification_settings(settings: NotificationSettingsUpdate, current_user: dict = Depends(get_current_user)):
    current = current_user.get("notification_settings") or {
        "notify_48h": True, "notify_24h": True, "notify_12h": True, "notify_6h": True
    }
    updated = dict(current)
    if settings.notify_48h is not None:
        updated["notify_48h"] = settings.notify_48h
    if settings.notify_24h is not None:
        updated["notify_24h"] = settings.notify_24h
    if settings.notify_12h is not None:
        updated["notify_12h"] = settings.notify_12h
    if settings.notify_6h is not None:
        updated["notify_6h"] = settings.notify_6h

    await sb(supabase.table('users').update({"notification_settings": updated}).eq('id', current_user['id']))
    return updated

# ==================== SMS LOGS ====================

@api_router.get("/notifications/logs")
async def get_notification_logs(current_user: dict = Depends(get_current_user)):
    result = await sb(
        supabase.table('sms_logs')
        .select('*')
        .eq('user_id', current_user['id'])
        .order('sent_at', desc=True)
        .limit(100)
    )
    return result.data or []

@api_router.post("/notifications/check")
async def check_and_send_notifications(current_user: dict = Depends(get_current_user)):
    settings = current_user.get("notification_settings") or {}
    result = await sb(supabase.table('shipments').select('*').eq('user_id', current_user['id']))
    shipments = result.data or []

    notifications_sent = []
    for s in shipments:
        status, hours = calculate_shipment_status(s["last_free_day"])

        notification_type = None
        if 5.5 <= hours <= 6.5 and settings.get("notify_6h", True):
            notification_type = "6h"
        elif 11.5 <= hours <= 12.5 and settings.get("notify_12h", True):
            notification_type = "12h"
        elif 23.5 <= hours <= 24.5 and settings.get("notify_24h", True):
            notification_type = "24h"
        elif 47.5 <= hours <= 48.5 and settings.get("notify_48h", True):
            notification_type = "48h"

        if notification_type:
            existing = await sb(
                supabase.table('sms_logs')
                .select('id')
                .eq('shipment_id', s['id'])
                .eq('notification_type', notification_type)
                .maybe_single()
            )
            if not existing.data:
                log = {
                    "id": str(uuid.uuid4()),
                    "user_id": current_user["id"],
                    "shipment_id": s["id"],
                    "container_number": s["container_number"],
                    "message": f"LFD Alert: Container {s['container_number']} expires in {notification_type}. Vessel: {s['vessel_name']}",
                    "notification_type": notification_type,
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                    "status": "sent_mock"
                }
                await sb(supabase.table('sms_logs').insert(log))
                notifications_sent.append(log)

    return {
        "message": f"Checked {len(shipments)} shipments, sent {len(notifications_sent)} notifications",
        "notifications": notifications_sent
    }

# ==================== DEMO DATA ====================

@api_router.post("/demo/seed")
async def seed_demo_data(current_user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    demo_shipments = [
        {"container_number": "MSCU1234567", "vessel_name": "MSC AURORA",          "arrival_date": (now - timedelta(days=5)).isoformat(), "last_free_day": (now + timedelta(hours=6)).isoformat(),   "notes": "Demo: Critical - 6 hours remaining"},
        {"container_number": "CMAU7654321", "vessel_name": "CMA CGM MARCO POLO",  "arrival_date": (now - timedelta(days=4)).isoformat(), "last_free_day": (now + timedelta(hours=20)).isoformat(),  "notes": "Demo: Critical - 20 hours remaining"},
        {"container_number": "MAEU9876543", "vessel_name": "MAERSK EDMONTON",     "arrival_date": (now - timedelta(days=3)).isoformat(), "last_free_day": (now + timedelta(hours=36)).isoformat(),  "notes": "Demo: Warning - 36 hours remaining"},
        {"container_number": "HLXU1111111", "vessel_name": "HAPAG LLOYD EXPRESS", "arrival_date": (now - timedelta(days=2)).isoformat(), "last_free_day": (now + timedelta(hours=72)).isoformat(),  "notes": "Demo: Safe - 72 hours remaining"},
        {"container_number": "EGLV2222222", "vessel_name": "EVERGREEN EVER GIVEN","arrival_date": (now - timedelta(days=1)).isoformat(), "last_free_day": (now + timedelta(hours=120)).isoformat(), "notes": "Demo: Safe - 120 hours remaining"},
    ]

    created = []
    for data in demo_shipments:
        existing = await sb(
            supabase.table('shipments')
            .select('id')
            .eq('user_id', current_user['id'])
            .eq('container_number', data["container_number"])
            .maybe_single()
        )
        if not existing.data:
            shipment_id = str(uuid.uuid4())
            status, hours = calculate_shipment_status(data["last_free_day"])
            doc = {
                "id": shipment_id,
                "user_id": current_user["id"],
                **data,
                "status": status,
                "hours_remaining": round(hours, 1),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source": "demo"
            }
            await sb(supabase.table('shipments').insert(doc))
            created.append(doc)

    return {"message": f"Created {len(created)} demo shipments", "shipments": created}

# ==================== TEST EMAIL + SMS ====================

@api_router.post("/test/email-sms")
async def test_email_parse_and_sms(request: TestEmailSMSRequest, current_user: dict = Depends(get_current_user)):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")

    prompt = f"""You are a logistics document parser. Extract shipment information from the text.
Return ONLY a valid JSON object with these fields:
- container_number: string (container ID, format like ABCD1234567 or MEDU4588210)
- vessel_name: string (name of the ship)
- arrival_date: string (ISO date format YYYY-MM-DDTHH:MM:SSZ)
- last_free_day: string (ISO date format YYYY-MM-DDTHH:MM:SSZ, the LFD/Last Free Day)
- bill_of_lading: string (B/L number if found, null otherwise)

Parse dates carefully. For example "March 17, 2026" should become "2026-03-17T00:00:00Z".
Return ONLY the JSON, no explanation.

{request.email_content}"""

    try:
        raw = await call_gemini_text(prompt)
        parsed = clean_json_response(raw)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not parse AI response: {str(e)}")

    container = (parsed.get("container_number") or "UNKNOWN").upper()
    vessel = parsed.get("vessel_name") or "Unknown Vessel"
    lfd = parsed.get("last_free_day") or (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    arrival = parsed.get("arrival_date") or datetime.now(timezone.utc).isoformat()
    bol = parsed.get("bill_of_lading")

    status, hours = calculate_shipment_status(lfd)

    # UPSERT
    existing = await sb(
        supabase.table('shipments')
        .select('*')
        .eq('user_id', current_user['id'])
        .eq('container_number', container)
        .maybe_single()
    )
    existing_shipment = existing.data
    is_update = bool(existing_shipment)
    old_lfd = None

    if is_update:
        old_lfd = (existing_shipment.get("last_free_day") or "")[:10]
        shipment_id = existing_shipment["id"]
        await sb(supabase.table('shipments').update({
            "vessel_name": vessel,
            "arrival_date": arrival,
            "last_free_day": lfd,
            "bill_of_lading": bol,
            "status": status,
            "hours_remaining": round(hours, 1),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "notes": f"Updated via email parse on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC"
        }).eq('id', shipment_id))
        shipment_doc = {
            "id": shipment_id, "user_id": current_user["id"],
            "container_number": container, "vessel_name": vessel,
            "arrival_date": arrival, "last_free_day": lfd,
            "status": status, "hours_remaining": round(hours, 1), "source": "test_email"
        }
    else:
        shipment_id = str(uuid.uuid4())
        shipment_doc = {
            "id": shipment_id, "user_id": current_user["id"],
            "container_number": container, "vessel_name": vessel,
            "arrival_date": arrival, "last_free_day": lfd,
            "bill_of_lading": bol, "notes": "Created via Test Email Parse",
            "status": status, "hours_remaining": round(hours, 1),
            "created_at": datetime.now(timezone.utc).isoformat(), "source": "test_email"
        }
        await sb(supabase.table('shipments').insert(shipment_doc))

    # Send SMS
    if is_update:
        sms_message = f"LFD Clock: SHIPMENT UPDATED!\n\nContainer: {container}\nVessel: {vessel}\nOld LFD: {old_lfd}\nNEW LFD: {lfd[:10]}\nStatus: {status.upper()}\nTime remaining: {round(hours, 1)}h"
    else:
        sms_message = f"LFD Clock: New shipment!\n\nContainer: {container}\nVessel: {vessel}\nLFD: {lfd[:10]}\nStatus: {status.upper()}\nTime remaining: {round(hours, 1)}h"

    sms_result = send_real_sms(request.phone_number, sms_message)

    await sb(supabase.table('sms_logs').insert({
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "shipment_id": shipment_id,
        "container_number": container,
        "message": sms_message,
        "notification_type": "update" if is_update else "new",
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "status": "sent_real",
        "twilio_sid": sms_result.get("sid")
    }))

    return {
        "success": True,
        "action": "updated" if is_update else "created",
        "message": f"Shipment {'UPDATED' if is_update else 'created'} and SMS sent!",
        "parsed_data": parsed,
        "shipment": shipment_doc,
        "sms": {
            "sent_to": sms_result.get("to"),
            "twilio_sid": sms_result.get("sid"),
            "status": sms_result.get("status")
        }
    }

# ==================== CRON - PROCESS REMINDERS ====================

@api_router.post("/cron/process-reminders")
async def process_pending_reminders():
    now = datetime.now(timezone.utc)

    result = await sb(
        supabase.table('reminders')
        .select('*')
        .eq('status', 'pending')
        .lte('schedule_time', now.isoformat())
        .limit(1000)
    )
    pending = result.data or []

    results = {"processed": 0, "sent": 0, "failed": 0, "skipped": 0, "details": []}

    for reminder in pending:
        results["processed"] += 1
        try:
            user_result = await sb(supabase.table('users').select('*').eq('id', reminder['user_id']).maybe_single())
            user = user_result.data
            if not user:
                results["skipped"] += 1
                continue

            user_settings = user.get("notification_settings") or {}
            setting_key = f"notify_{reminder['reminder_type']}"
            if not user_settings.get(setting_key, True):
                await sb(supabase.table('reminders').update({"status": "skipped", "processed_at": now.isoformat()}).eq('id', reminder['id']))
                results["skipped"] += 1
                continue

            phone = user.get("phone")
            if not phone:
                await sb(supabase.table('reminders').update({"status": "failed", "error": "No phone number", "processed_at": now.isoformat()}).eq('id', reminder['id']))
                results["failed"] += 1
                continue

            container = reminder.get("container_number", "UNKNOWN")
            hours_before = reminder.get("hours_before", "?")
            msg = f"Alert: Container {container} expires in {hours_before} hours. Avoid storage fees!"

            sms_result = send_real_sms(phone, msg)

            await sb(supabase.table('reminders').update({
                "status": "sent",
                "processed_at": now.isoformat(),
                "twilio_sid": sms_result.get("sid")
            }).eq('id', reminder['id']))

            await sb(supabase.table('sms_logs').insert({
                "id": str(uuid.uuid4()),
                "user_id": reminder["user_id"],
                "shipment_id": reminder["shipment_id"],
                "container_number": container,
                "message": msg,
                "notification_type": f"reminder_{reminder['reminder_type']}",
                "sent_at": now.isoformat(),
                "status": "sent_real",
                "twilio_sid": sms_result.get("sid")
            }))

            results["sent"] += 1
            results["details"].append({"container": container, "type": reminder["reminder_type"], "status": "sent"})

        except Exception as e:
            logger.error(f"Error processing reminder {reminder.get('id')}: {e}")
            await sb(supabase.table('reminders').update({"status": "failed", "error": str(e), "processed_at": now.isoformat()}).eq('id', reminder['id']))
            results["failed"] += 1

    return results

@api_router.get("/reminders")
async def get_user_reminders(current_user: dict = Depends(get_current_user)):
    result = await sb(
        supabase.table('reminders')
        .select('*')
        .eq('user_id', current_user['id'])
        .order('schedule_time', desc=False)
    )
    return result.data or []

# ==================== DIRECT PDF UPLOAD ====================

@api_router.post("/upload/pdf")
async def direct_upload_pdf(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = await parse_and_process_shipment(
            content=tmp_path,
            content_type="pdf",
            customer=current_user,
            source="direct_upload",
            filename=file.filename
        )
        return result
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

# ==================== TRUCKER SHARE ====================

@api_router.post("/shipments/{shipment_id}/share-trucker")
async def share_with_trucker(shipment_id: str, request: TruckerShareRequest, current_user: dict = Depends(get_current_user)):
    result = await sb(
        supabase.table('shipments')
        .select('*')
        .eq('id', shipment_id)
        .eq('user_id', current_user['id'])
        .maybe_single()
    )
    shipment = result.data
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    container = shipment.get("container_number", "UNKNOWN")
    vessel = shipment.get("vessel_name", "Unknown")
    lfd = (shipment.get("last_free_day") or "")[:10]
    carrier = shipment.get("carrier", "")
    _, hours = calculate_shipment_status(shipment.get("last_free_day", ""))

    trucker_name = request.trucker_name or "Driver"
    msg = f"Hi {trucker_name}, pickup needed:\n\nContainer: {container}\nVessel: {vessel}\nLFD: {lfd}\nTime left: {round(hours)}h\n\nFrom: {current_user.get('company_name', 'LFD Clock')}"

    sms_result = send_real_sms(request.trucker_phone, msg)

    await sb(supabase.table('sms_logs').insert({
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "shipment_id": shipment_id,
        "container_number": container,
        "message": msg,
        "notification_type": "trucker_share",
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "status": "sent_real",
        "twilio_sid": sms_result.get("sid"),
        "trucker_phone": request.trucker_phone
    }))

    return {"success": True, "message": f"LFD details sent to {request.trucker_phone}", "sms_sid": sms_result.get("sid")}

# ==================== CARRIER PORTAL ====================

@api_router.get("/shipments/{shipment_id}/carrier-portal")
async def get_carrier_portal_link(shipment_id: str, current_user: dict = Depends(get_current_user)):
    result = await sb(
        supabase.table('shipments')
        .select('*')
        .eq('id', shipment_id)
        .eq('user_id', current_user['id'])
        .maybe_single()
    )
    shipment = result.data
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    carrier = shipment.get("carrier") or shipment.get("vessel_name", "")
    portal_url = get_carrier_portal(carrier)

    return {"carrier": carrier, "portal_url": portal_url, "container_number": shipment.get("container_number")}

# ==================== HEALTH ====================

@api_router.get("/")
async def root():
    return {"message": "LFD Clock API is running"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "lfd-clock"}

# ==================== APP SETUP ====================

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== BACKGROUND REMINDER SCHEDULER ====================

async def reminder_scheduler():
    """Checks reminders every 5 minutes and sends SMS via Twilio"""
    while True:
        try:
            await asyncio.sleep(300)
            now = datetime.now(timezone.utc)

            result = await sb(
                supabase.table('reminders')
                .select('*')
                .eq('status', 'pending')
                .lte('schedule_time', now.isoformat())
                .limit(100)
            )
            pending = result.data or []

            for reminder in pending:
                try:
                    user_result = await sb(supabase.table('users').select('*').eq('id', reminder['user_id']).maybe_single())
                    user = user_result.data
                    if not user:
                        continue

                    user_settings = user.get("notification_settings") or {}
                    setting_key = f"notify_{reminder['reminder_type']}"
                    if not user_settings.get(setting_key, True):
                        await sb(supabase.table('reminders').update({"status": "skipped", "processed_at": now.isoformat()}).eq('id', reminder['id']))
                        continue

                    phone = user.get("phone")
                    if not phone:
                        await sb(supabase.table('reminders').update({"status": "failed", "error": "No phone number", "processed_at": now.isoformat()}).eq('id', reminder['id']))
                        continue

                    container = reminder.get("container_number", "UNKNOWN")
                    hours_before = reminder.get("hours_before", "?")
                    msg = f"Alert: Container {container} expires in {hours_before} hours. Avoid storage fees!"

                    sms_result = send_real_sms(phone, msg)

                    await sb(supabase.table('reminders').update({
                        "status": "sent",
                        "processed_at": now.isoformat(),
                        "twilio_sid": sms_result.get("sid")
                    }).eq('id', reminder['id']))

                    await sb(supabase.table('sms_logs').insert({
                        "id": str(uuid.uuid4()),
                        "user_id": reminder["user_id"],
                        "shipment_id": reminder["shipment_id"],
                        "container_number": container,
                        "message": msg,
                        "notification_type": f"reminder_{reminder['reminder_type']}",
                        "sent_at": now.isoformat(),
                        "status": "sent_real",
                        "twilio_sid": sms_result.get("sid")
                    }))

                    logger.info(f"Sent {reminder['reminder_type']} reminder for {container}")

                except Exception as e:
                    logger.error(f"Reminder {reminder.get('id')} error: {e}")
                    await sb(supabase.table('reminders').update({"status": "failed", "error": str(e), "processed_at": now.isoformat()}).eq('id', reminder['id']))

        except Exception as e:
            logger.error(f"Reminder scheduler error: {e}")


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(reminder_scheduler())
    logger.info("LFD Clock API started — reminder scheduler running every 5 minutes")
