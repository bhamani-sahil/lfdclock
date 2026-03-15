from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
import hashlib
from datetime import datetime, timezone, timedelta
import jwt
from passlib.context import CryptContext
import base64
from twilio.rest import Client as TwilioClient

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'lfd-clock-secret')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

# Initialize Twilio client
twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create the main app
app = FastAPI(title="LFD Clock API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# ==================== MODELS ====================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    company_name: str
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    company_name: str
    phone: Optional[str] = None
    forwarding_email: str
    created_at: str

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

class ShipmentResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    container_number: str
    vessel_name: str
    arrival_date: str
    last_free_day: str
    notes: Optional[str] = None
    status: str
    hours_remaining: float
    created_at: str
    source: str

class EmailParseRequest(BaseModel):
    subject: str
    body: str
    from_email: str

class TestEmailSMSRequest(BaseModel):
    email_content: str
    phone_number: str

class PostmarkAttachment(BaseModel):
    Name: str
    Content: str  # Base64 encoded
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
        extra = "allow"  # Allow extra fields from Postmark

class SMSLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    shipment_id: str
    container_number: str
    message: str
    notification_type: str
    sent_at: str
    status: str

class ReminderCreate(BaseModel):
    shipment_id: str
    container_number: str
    schedule_time: str
    reminder_type: str  # 48h, 24h, 12h, 6h

class DirectUploadRequest(BaseModel):
    filename: str
    content: str  # Base64 encoded PDF

class TruckerShareRequest(BaseModel):
    shipment_id: str
    trucker_phone: str
    trucker_name: Optional[str] = None

# Carrier portal links
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

# ==================== HELPERS ====================

def generate_inbound_email(company_name: str) -> str:
    """Generate unique inbound email for customer: company-name@inbound.lfdclock.com"""
    # Clean company name: lowercase, replace spaces with hyphens, remove special chars
    import re
    clean_name = company_name.lower().strip()
    clean_name = re.sub(r'[^a-z0-9\s-]', '', clean_name)
    clean_name = re.sub(r'[\s]+', '-', clean_name)
    clean_name = re.sub(r'-+', '-', clean_name)
    # Add random suffix to ensure uniqueness
    suffix = hashlib.md5(f"{company_name}{datetime.now().isoformat()}".encode()).hexdigest()[:4]
    return f"{clean_name}-{suffix}@inbound.lfdclock.com"

def generate_forwarding_email(user_id: str) -> str:
    """Generate unique forwarding email for user (legacy)"""
    short_id = hashlib.md5(user_id.encode()).hexdigest()[:8]
    return f"fwd-{short_id}@lfdclock.com"

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(user_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def calculate_shipment_status(last_free_day: str) -> tuple:
    """Calculate status and hours remaining for a shipment"""
    try:
        lfd = datetime.fromisoformat(last_free_day.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        diff = lfd - now
        hours_remaining = diff.total_seconds() / 3600
        
        if hours_remaining <= 0:
            return "expired", hours_remaining
        elif hours_remaining <= 24:
            return "critical", hours_remaining
        elif hours_remaining <= 48:
            return "warning", hours_remaining
        else:
            return "safe", hours_remaining
    except:
        return "unknown", 0

async def create_reminders_for_shipment(shipment_id: str, user_id: str, container_number: str, last_free_day: str, user_settings: dict):
    """Create reminder records for a shipment based on user's notification settings"""
    try:
        lfd = datetime.fromisoformat(last_free_day.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        
        reminder_intervals = [
            ("48h", 48, user_settings.get("notify_48h", True)),
            ("24h", 24, user_settings.get("notify_24h", True)),
            ("12h", 12, user_settings.get("notify_12h", True)),
            ("6h", 6, user_settings.get("notify_6h", True)),
        ]
        
        # Delete existing reminders for this shipment (for updates)
        await db.reminders.delete_many({"shipment_id": shipment_id})
        
        reminders_created = []
        for reminder_type, hours_before, is_enabled in reminder_intervals:
            if not is_enabled:
                continue
                
            schedule_time = lfd - timedelta(hours=hours_before)
            
            # Only create if schedule time is in the future
            if schedule_time > now:
                reminder_doc = {
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
                }
                await db.reminders.insert_one(reminder_doc)
                reminders_created.append(reminder_type)
        
        return reminders_created
    except Exception as e:
        logger.error(f"Error creating reminders: {str(e)}")
        return []

def get_carrier_portal(carrier_name: str) -> str:
    """Get the tracking portal URL for a carrier"""
    if not carrier_name:
        return CARRIER_PORTALS["DEFAULT"]
    carrier_upper = carrier_name.upper()
    for key in CARRIER_PORTALS:
        if key in carrier_upper:
            return CARRIER_PORTALS[key]
    return CARRIER_PORTALS["DEFAULT"]

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/signup")
async def signup(user_data: UserCreate):
    # Check if user exists
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    forwarding_email = generate_forwarding_email(user_id)
    inbound_email = generate_inbound_email(user_data.company_name)
    
    # Extract email prefix for lookup
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
        "created_at": datetime.now(timezone.utc).isoformat(),
        "notification_settings": {
            "notify_48h": True,
            "notify_24h": True,
            "notify_12h": True,
            "notify_6h": True
        }
    }
    
    await db.users.insert_one(user_doc)
    
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
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
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
    shipments = await db.shipments.find(
        {"user_id": current_user["id"]}, 
        {"_id": 0}
    ).sort("last_free_day", 1).to_list(1000)
    
    # Update status for each shipment and ensure all fields are present
    result = []
    for shipment in shipments:
        # If picked up, status is "picked_up", otherwise calculate from LFD
        if shipment.get("picked_up"):
            status = "picked_up"
            hours = 0
        else:
            status, hours = calculate_shipment_status(shipment.get("last_free_day", ""))
        
        result.append({
            "id": shipment.get("id", ""),
            "user_id": shipment.get("user_id", ""),
            "container_number": shipment.get("container_number", ""),
            "vessel_name": shipment.get("vessel_name", "Unknown"),
            "carrier": shipment.get("carrier", ""),
            "arrival_date": shipment.get("arrival_date", ""),
            "last_free_day": shipment.get("last_free_day", ""),
            "notes": shipment.get("notes"),
            "status": status,
            "hours_remaining": round(hours, 1),
            "created_at": shipment.get("created_at", ""),
            "source": shipment.get("source", "manual"),
            "picked_up": shipment.get("picked_up", False),
            "picked_up_at": shipment.get("picked_up_at"),
            "fees_avoided": shipment.get("fees_avoided", 0)
        })
    
    return result

@api_router.post("/shipments")
async def create_shipment(
    shipment_data: ShipmentCreate,
    current_user: dict = Depends(get_current_user)
):
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
    
    await db.shipments.insert_one(shipment_doc)
    
    # Create reminders based on user settings
    user_settings = current_user.get("notification_settings", {})
    await create_reminders_for_shipment(
        shipment_id, 
        current_user["id"], 
        shipment_data.container_number.upper(),
        shipment_data.last_free_day,
        user_settings
    )
    
    # Return without _id (which MongoDB adds)
    if '_id' in shipment_doc:
        del shipment_doc['_id']
    return shipment_doc

@api_router.delete("/shipments/{shipment_id}")
async def delete_shipment(
    shipment_id: str,
    current_user: dict = Depends(get_current_user)
):
    # Delete shipment
    result = await db.shipments.delete_one({
        "id": shipment_id,
        "user_id": current_user["id"]
    })
    
    # Also delete associated reminders
    await db.reminders.delete_many({"shipment_id": shipment_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    return {"message": "Shipment deleted"}

@api_router.get("/shipments/stats")
async def get_shipment_stats(current_user: dict = Depends(get_current_user)):
    shipments = await db.shipments.find(
        {"user_id": current_user["id"]}, 
        {"_id": 0}
    ).to_list(1000)
    
    stats = {
        "total": len(shipments),
        "safe": 0,
        "warning": 0,
        "critical": 0,
        "expired": 0,
        "picked_up": 0,
        "potential_fees_avoided": 0
    }
    
    DEMURRAGE_RATE = 300  # $300 per container assumed savings
    
    for shipment in shipments:
        status, _ = calculate_shipment_status(shipment.get("last_free_day", ""))
        if status in stats:
            stats[status] += 1
        
        # Count picked up containers and calculate savings
        if shipment.get("picked_up"):
            stats["picked_up"] += 1
            stats["potential_fees_avoided"] += shipment.get("fees_avoided", DEMURRAGE_RATE)
    
    return stats

@api_router.post("/shipments/{shipment_id}/mark-picked-up")
async def mark_shipment_picked_up(
    shipment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark a container as picked up before LFD - records savings"""
    shipment = await db.shipments.find_one({
        "id": shipment_id,
        "user_id": current_user["id"]
    }, {"_id": 0})
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    # Calculate hours remaining when picked up
    status, hours_remaining = calculate_shipment_status(shipment.get("last_free_day", ""))
    
    # Assume $300/day demurrage avoided if picked up before LFD
    fees_avoided = 300 if hours_remaining > 0 else 0
    
    await db.shipments.update_one(
        {"id": shipment_id},
        {"$set": {
            "picked_up": True,
            "picked_up_at": datetime.now(timezone.utc).isoformat(),
            "fees_avoided": fees_avoided
        }}
    )
    
    # Delete pending reminders for this shipment
    await db.reminders.delete_many({"shipment_id": shipment_id, "status": "pending"})
    
    return {
        "message": "Container marked as picked up",
        "fees_avoided": fees_avoided
    }

# ==================== EMAIL PARSING (SIMULATED) ====================

@api_router.post("/email/parse")
async def parse_email(
    email_data: EmailParseRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Simulated email parsing endpoint.
    In production, this would be triggered by SendGrid/Postmark inbound webhook.
    Uses Gemini to extract shipment data.
    """
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="LLM API key not configured")
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"email-parse-{uuid.uuid4()}",
            system_message="""You are a logistics document parser. Extract shipment information from emails.
            Return ONLY a valid JSON object with these fields:
            - container_number: string (container ID, usually format like ABCD1234567)
            - vessel_name: string (name of the ship)
            - arrival_date: string (ISO date format YYYY-MM-DDTHH:MM:SSZ)
            - last_free_day: string (ISO date format YYYY-MM-DDTHH:MM:SSZ, the LFD/Last Free Day)
            
            If you cannot find a field, use null. Return ONLY the JSON, no explanation."""
        ).with_model("gemini", "gemini-2.5-flash")
        
        content = f"Subject: {email_data.subject}\n\nBody:\n{email_data.body}"
        
        user_message = UserMessage(text=content)
        response = await chat.send_message(user_message)
        
        # Parse the JSON response
        import json
        try:
            # Clean response - remove markdown code blocks if present
            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = clean_response.split("```")[1]
                if clean_response.startswith("json"):
                    clean_response = clean_response[4:]
            clean_response = clean_response.strip()
            
            parsed_data = json.loads(clean_response)
        except json.JSONDecodeError:
            raise HTTPException(status_code=422, detail="Could not parse shipment data from email")
        
        # Validate required fields
        if not parsed_data.get("container_number") or not parsed_data.get("last_free_day"):
            raise HTTPException(status_code=422, detail="Missing required shipment data")
        
        # Create the shipment
        shipment_id = str(uuid.uuid4())
        status, hours = calculate_shipment_status(parsed_data["last_free_day"])
        
        shipment_doc = {
            "id": shipment_id,
            "user_id": current_user["id"],
            "container_number": parsed_data["container_number"].upper(),
            "vessel_name": parsed_data.get("vessel_name", "Unknown"),
            "arrival_date": parsed_data.get("arrival_date", datetime.now(timezone.utc).isoformat()),
            "last_free_day": parsed_data["last_free_day"],
            "notes": f"Parsed from email: {email_data.subject}",
            "status": status,
            "hours_remaining": round(hours, 1),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source": "email"
        }
        
        await db.shipments.insert_one(shipment_doc)
        # Remove _id before returning
        if '_id' in shipment_doc:
            del shipment_doc['_id']
        
        return {
            "message": "Email parsed successfully",
            "shipment": shipment_doc
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email parsing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Email parsing failed: {str(e)}")

# ==================== NOTIFICATION SETTINGS ====================

@api_router.get("/settings/notifications")
async def get_notification_settings(current_user: dict = Depends(get_current_user)):
    settings = current_user.get("notification_settings", {
        "notify_48h": True,
        "notify_24h": True,
        "notify_12h": True,
        "notify_6h": True
    })
    return settings

@api_router.put("/settings/notifications")
async def update_notification_settings(
    settings: NotificationSettingsUpdate,
    current_user: dict = Depends(get_current_user)
):
    current_settings = current_user.get("notification_settings", {})
    
    update_data = {}
    if settings.notify_48h is not None:
        update_data["notification_settings.notify_48h"] = settings.notify_48h
    if settings.notify_24h is not None:
        update_data["notification_settings.notify_24h"] = settings.notify_24h
    if settings.notify_12h is not None:
        update_data["notification_settings.notify_12h"] = settings.notify_12h
    if settings.notify_6h is not None:
        update_data["notification_settings.notify_6h"] = settings.notify_6h
    
    if update_data:
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$set": update_data}
        )
    
    # Return updated settings
    user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0})
    return user.get("notification_settings")

# ==================== SMS NOTIFICATIONS (MOCKED) ====================

@api_router.get("/notifications/logs")
async def get_notification_logs(current_user: dict = Depends(get_current_user)):
    """Get SMS notification logs for the user"""
    logs = await db.sms_logs.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("sent_at", -1).to_list(100)
    return logs

@api_router.post("/notifications/check")
async def check_and_send_notifications(current_user: dict = Depends(get_current_user)):
    """
    Check all shipments and send notifications for approaching LFDs.
    MOCKED: In production, this would use Twilio to send real SMS.
    """
    settings = current_user.get("notification_settings", {})
    shipments = await db.shipments.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).to_list(1000)
    
    notifications_sent = []
    
    for shipment in shipments:
        status, hours = calculate_shipment_status(shipment["last_free_day"])
        
        # Determine which notification to send based on hours remaining
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
            # Check if we already sent this notification
            existing = await db.sms_logs.find_one({
                "shipment_id": shipment["id"],
                "notification_type": notification_type
            })
            
            if not existing:
                # MOCK: Create SMS log entry
                sms_log = {
                    "id": str(uuid.uuid4()),
                    "user_id": current_user["id"],
                    "shipment_id": shipment["id"],
                    "container_number": shipment["container_number"],
                    "message": f"[MOCK SMS] LFD Alert: Container {shipment['container_number']} expires in {notification_type}. Vessel: {shipment['vessel_name']}",
                    "notification_type": notification_type,
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                    "status": "sent_mock"
                }
                
                await db.sms_logs.insert_one(sms_log)
                # Remove _id before adding to response
                if '_id' in sms_log:
                    del sms_log['_id']
                notifications_sent.append(sms_log)
    
    return {
        "message": f"Checked {len(shipments)} shipments, sent {len(notifications_sent)} notifications (MOCKED)",
        "notifications": notifications_sent
    }

# ==================== DEMO DATA ====================

@api_router.post("/demo/seed")
async def seed_demo_data(current_user: dict = Depends(get_current_user)):
    """Create demo shipments for testing the traffic light system"""
    now = datetime.now(timezone.utc)
    
    demo_shipments = [
        {
            "container_number": "MSCU1234567",
            "vessel_name": "MSC AURORA",
            "arrival_date": (now - timedelta(days=5)).isoformat(),
            "last_free_day": (now + timedelta(hours=6)).isoformat(),
            "notes": "Demo: Critical - 6 hours remaining"
        },
        {
            "container_number": "CMAU7654321",
            "vessel_name": "CMA CGM MARCO POLO",
            "arrival_date": (now - timedelta(days=4)).isoformat(),
            "last_free_day": (now + timedelta(hours=20)).isoformat(),
            "notes": "Demo: Critical - 20 hours remaining"
        },
        {
            "container_number": "MAEU9876543",
            "vessel_name": "MAERSK EDMONTON",
            "arrival_date": (now - timedelta(days=3)).isoformat(),
            "last_free_day": (now + timedelta(hours=36)).isoformat(),
            "notes": "Demo: Warning - 36 hours remaining"
        },
        {
            "container_number": "HLXU1111111",
            "vessel_name": "HAPAG LLOYD EXPRESS",
            "arrival_date": (now - timedelta(days=2)).isoformat(),
            "last_free_day": (now + timedelta(hours=72)).isoformat(),
            "notes": "Demo: Safe - 72 hours remaining"
        },
        {
            "container_number": "EGLV2222222",
            "vessel_name": "EVERGREEN EVER GIVEN",
            "arrival_date": (now - timedelta(days=1)).isoformat(),
            "last_free_day": (now + timedelta(hours=120)).isoformat(),
            "notes": "Demo: Safe - 120 hours remaining"
        }
    ]
    
    created = []
    for data in demo_shipments:
        # Check if already exists
        existing = await db.shipments.find_one({
            "user_id": current_user["id"],
            "container_number": data["container_number"]
        })
        
        if not existing:
            shipment_id = str(uuid.uuid4())
            status, hours = calculate_shipment_status(data["last_free_day"])
            
            shipment_doc = {
                "id": shipment_id,
                "user_id": current_user["id"],
                **data,
                "status": status,
                "hours_remaining": round(hours, 1),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source": "demo"
            }
            
            await db.shipments.insert_one(shipment_doc)
            # Remove _id before adding to response
            if '_id' in shipment_doc:
                del shipment_doc['_id']
            created.append(shipment_doc)
    
    return {
        "message": f"Created {len(created)} demo shipments",
        "shipments": created
    }

# ==================== HEALTH CHECK ====================

# ==================== POSTMARK INBOUND WEBHOOK ====================

from fastapi import BackgroundTasks

@api_router.post("/inbound-lfd")
async def postmark_inbound_webhook(payload: PostmarkInboundPayload, background_tasks: BackgroundTasks):
    """
    Postmark Inbound Webhook: Receives emails sent to [customer]@inbound.lfdclock.com
    Returns immediately, processes PDF in background.
    """
    try:
        logger.info(f"Postmark webhook received: To={payload.To}, From={payload.From}, Subject={payload.Subject}")
        
        # Step 1: Extract customer from email address (prefix before @inbound.lfdclock.com)
        to_email = payload.To or ""
        if "@inbound.lfdclock.com" not in to_email.lower():
            logger.warning(f"Invalid inbound email: {to_email}")
            return {"status": "ignored", "reason": "Not an inbound.lfdclock.com address"}
        
        inbound_prefix = to_email.split('@')[0].lower()
        
        # Step 2: Look up customer by inbound_prefix
        customer = await db.users.find_one({"inbound_prefix": inbound_prefix}, {"_id": 0})
        if not customer:
            logger.warning(f"No customer found for inbound prefix: {inbound_prefix}")
            return {"status": "error", "reason": f"No customer found for {inbound_prefix}"}
        
        # Step 3: Add to background processing queue
        background_tasks.add_task(
            process_inbound_email_background,
            payload=payload,
            customer=customer,
            inbound_prefix=inbound_prefix
        )
        
        # Return immediately so Postmark doesn't timeout
        return {"status": "accepted", "message": "Processing in background", "customer": inbound_prefix}
        
    except Exception as e:
        logger.error(f"Postmark webhook error: {str(e)}")
        return {"status": "error", "detail": str(e)}


async def process_inbound_email_background(payload: PostmarkInboundPayload, customer: dict, inbound_prefix: str):
    """Background task to process inbound email"""
    import tempfile
    import os as os_module
    
    try:
        logger.info(f"Background processing started for {inbound_prefix}")
        
        customer_phone = customer.get("phone")
        if not customer_phone:
            logger.warning(f"Customer {inbound_prefix} has no phone number - will process but skip SMS")
        
        # Process attachments (look for PDFs)
        attachments = payload.Attachments or []
        pdf_attachments = [a for a in attachments if a.ContentType == "application/pdf" or a.Name.lower().endswith('.pdf')]
        
        if not pdf_attachments:
            # No PDF? Try parsing the email body instead
            logger.info("No PDF attachments, attempting to parse email body")
            text_content = payload.TextBody or payload.HtmlBody or ""
            if not text_content:
                logger.error(f"No PDF attachment and no email body to parse for {inbound_prefix}")
                return
            
            # Parse text content
            await parse_and_process_shipment(
                content=text_content,
                content_type="text",
                customer=customer,
                source="email_body"
            )
            return
        
        # Process each PDF attachment
        for attachment in pdf_attachments:
            try:
                # Decode base64 PDF
                pdf_bytes = base64.b64decode(attachment.Content)
                
                # Save to temp file
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                    tmp_file.write(pdf_bytes)
                    tmp_path = tmp_file.name
                
                try:
                    # Parse PDF with Gemini
                    await parse_and_process_shipment(
                        content=tmp_path,
                        content_type="pdf",
                        customer=customer,
                        source="pdf_attachment",
                        filename=attachment.Name
                    )
                finally:
                    # Clean up temp file
                    if os_module.path.exists(tmp_path):
                        os_module.unlink(tmp_path)
                        
            except Exception as e:
                logger.error(f"Error processing attachment {attachment.Name}: {str(e)}")
        
        logger.info(f"Background processing completed for {inbound_prefix}")
        
    except Exception as e:
        logger.error(f"Background processing error for {inbound_prefix}: {str(e)}")


async def parse_and_process_shipment(content: str, content_type: str, customer: dict, source: str, filename: str = None):
    """
    Parse content (PDF path or text) with Gemini and upsert shipment.
    Sends SMS alert based on new/update status.
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType
    import json
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        return {"status": "error", "reason": "LLM API key not configured"}
    
    try:
        # Create Gemini chat
        chat = LlmChat(
            api_key=api_key,
            session_id=f"inbound-parse-{uuid.uuid4()}",
            system_message="""You are a logistics document parser specializing in shipping/freight documents.
Extract the following information and return ONLY valid JSON:
{
    "container_id": "string (4 letters + 7 digits, e.g., MEDU4588210)",
    "lfd": "string (Last Free Day in YYYY-MM-DD format)",
    "carrier": "string (shipping line/carrier name)",
    "vessel": "string (vessel name if found)",
    "arrival_date": "string (arrival/ETA date in YYYY-MM-DD format if found)",
    "status": "string ('new' or 'update' based on context clues like 'revised', 'updated', 'amended')"
}
If a field cannot be found, use null. Return ONLY the JSON, no explanation."""
        ).with_model("gemini", "gemini-2.5-flash")
        
        # Create message based on content type
        if content_type == "pdf":
            # Use file attachment for PDF
            pdf_file = FileContentWithMimeType(
                file_path=content,
                mime_type="application/pdf"
            )
            user_message = UserMessage(
                text="Extract shipment information from this PDF document.",
                file_contents=[pdf_file]
            )
        else:
            # Plain text
            user_message = UserMessage(text=f"Extract shipment information from this email:\n\n{content}")
        
        # Send to Gemini
        response = await chat.send_message(user_message)
        
        # Parse JSON response
        clean_response = response.strip()
        if clean_response.startswith("```"):
            parts = clean_response.split("```")
            if len(parts) > 1:
                clean_response = parts[1]
                if clean_response.startswith("json"):
                    clean_response = clean_response[4:]
        clean_response = clean_response.strip()
        
        try:
            parsed_data = json.loads(clean_response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}, response: {clean_response[:200]}")
            return {"status": "error", "reason": f"Could not parse AI response"}
        
        container_id = parsed_data.get("container_id", "").upper() if parsed_data.get("container_id") else None
        lfd = parsed_data.get("lfd")
        carrier = parsed_data.get("carrier", "Unknown Carrier")
        vessel = parsed_data.get("vessel", "Unknown Vessel")
        arrival_date = parsed_data.get("arrival_date")
        doc_status = parsed_data.get("status", "new")
        
        if not container_id or not lfd:
            return {"status": "error", "reason": "Could not extract container ID or LFD from document"}
        
        # Convert LFD to ISO format if needed
        if lfd and len(lfd) == 10:  # YYYY-MM-DD format
            lfd = f"{lfd}T00:00:00Z"
        
        # Calculate shipment status
        status, hours = calculate_shipment_status(lfd)
        
        # Step: Check if container already exists (UPSERT)
        existing_shipment = await db.shipments.find_one({
            "user_id": customer["id"],
            "container_number": container_id
        })
        
        is_update = False
        old_lfd = None
        
        if existing_shipment:
            # UPDATE existing shipment
            is_update = True
            old_lfd = existing_shipment.get("last_free_day", "")[:10] if existing_shipment.get("last_free_day") else "Unknown"
            shipment_id = existing_shipment["id"]
            
            await db.shipments.update_one(
                {"id": shipment_id},
                {"$set": {
                    "carrier": carrier,
                    "vessel_name": vessel,
                    "arrival_date": arrival_date,
                    "last_free_day": lfd,
                    "status": status,
                    "hours_remaining": round(hours, 1),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "notes": f"Updated from {source} on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC"
                }}
            )
        else:
            # CREATE new shipment
            shipment_id = str(uuid.uuid4())
            
            shipment_doc = {
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
            }
            
            await db.shipments.insert_one(shipment_doc)
        
        # Step: Send SMS Alert
        customer_phone = customer.get("phone")
        if customer_phone:
            if is_update and old_lfd != lfd[:10]:
                # LFD changed - send delay alert
                sms_message = f"DELAY ALERT: Container {container_id} at {carrier} has a NEW Last Free Day of {lfd[:10]} (was {old_lfd}). Don't get hit with demurrage!"
            elif is_update:
                # Update but same LFD
                sms_message = f"LFD Confirmed: Container {container_id} at {carrier} - LFD remains {lfd[:10]}. {round(hours, 1)}h remaining."
            else:
                # New shipment
                sms_message = f"LFD Alert: Container {container_id} at {carrier} has a Last Free Day of {lfd[:10]}. Initial tracking active! Don't get hit with demurrage!"
            
            try:
                sms_result = send_real_sms(customer_phone, sms_message)
                
                # Log SMS
                sms_log = {
                    "id": str(uuid.uuid4()),
                    "user_id": customer["id"],
                    "shipment_id": shipment_id,
                    "container_number": container_id,
                    "message": sms_message,
                    "notification_type": "delay_alert" if is_update else "initial_tracking",
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                    "status": "sent_real",
                    "twilio_sid": sms_result.get("sid")
                }
                await db.sms_logs.insert_one(sms_log)
                
            except Exception as e:
                logger.error(f"SMS send error: {str(e)}")
                sms_result = {"error": str(e)}
        else:
            sms_result = {"skipped": "No phone number"}
        
        return {
            "status": "success",
            "action": "updated" if is_update else "created",
            "container_id": container_id,
            "lfd": lfd[:10],
            "carrier": carrier,
            "old_lfd": old_lfd if is_update else None,
            "sms_sent": "error" not in sms_result and "skipped" not in sms_result,
            "filename": filename
        }
        
    except Exception as e:
        logger.error(f"Parse and process error: {str(e)}")
        return {"status": "error", "reason": str(e)}


@api_router.get("/")
async def root():
    return {"message": "LFD Clock API is running"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "lfd-clock"}

# ==================== TEST EMAIL + REAL SMS ====================

def send_real_sms(to_number: str, message: str) -> dict:
    """Send a real SMS via Twilio"""
    if not twilio_client:
        raise HTTPException(status_code=500, detail="Twilio not configured")
    
    # Ensure phone number has country code
    if not to_number.startswith('+'):
        to_number = '+1' + to_number  # Default to US if no country code
    
    try:
        sms = twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_number
        )
        return {
            "sid": sms.sid,
            "status": sms.status,
            "to": to_number
        }
    except Exception as e:
        logger.error(f"Twilio SMS error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"SMS failed: {str(e)}")

@api_router.post("/test/email-sms")
async def test_email_parse_and_sms(
    request: TestEmailSMSRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    TEST ENDPOINT: Parse email content with Gemini AI and send REAL SMS immediately.
    Use this to test the full flow without email forwarding setup.
    """
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        import json
        
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="LLM API key not configured")
        
        # Step 1: Parse with Gemini
        chat = LlmChat(
            api_key=api_key,
            session_id=f"test-parse-{uuid.uuid4()}",
            system_message="""You are a logistics document parser. Extract shipment information from the text.
            Return ONLY a valid JSON object with these fields:
            - container_number: string (container ID, format like ABCD1234567 or MEDU4588210)
            - vessel_name: string (name of the ship)
            - arrival_date: string (ISO date format YYYY-MM-DDTHH:MM:SSZ)
            - last_free_day: string (ISO date format YYYY-MM-DDTHH:MM:SSZ, the LFD/Last Free Day)
            - bill_of_lading: string (B/L number if found, null otherwise)
            
            Parse dates carefully. For example "March 17, 2026" should become "2026-03-17T00:00:00Z".
            Return ONLY the JSON, no explanation."""
        ).with_model("gemini", "gemini-2.5-flash")
        
        user_message = UserMessage(text=request.email_content)
        response = await chat.send_message(user_message)
        
        # Parse JSON response
        clean_response = response.strip()
        if clean_response.startswith("```"):
            clean_response = clean_response.split("```")[1]
            if clean_response.startswith("json"):
                clean_response = clean_response[4:]
        clean_response = clean_response.strip()
        
        try:
            parsed_data = json.loads(clean_response)
        except json.JSONDecodeError:
            raise HTTPException(status_code=422, detail=f"Could not parse AI response: {clean_response[:200]}")
        
        container = parsed_data.get("container_number", "UNKNOWN").upper()
        vessel = parsed_data.get("vessel_name", "Unknown Vessel")
        lfd = parsed_data.get("last_free_day", (datetime.now(timezone.utc) + timedelta(days=5)).isoformat())
        arrival = parsed_data.get("arrival_date", datetime.now(timezone.utc).isoformat())
        bol = parsed_data.get("bill_of_lading")
        
        status, hours = calculate_shipment_status(lfd)
        
        # Step 2: Check if container already exists for this user (UPSERT logic)
        existing_shipment = await db.shipments.find_one({
            "user_id": current_user["id"],
            "container_number": container
        })
        
        is_update = False
        old_lfd = None
        
        if existing_shipment:
            # UPDATE existing shipment
            is_update = True
            old_lfd = existing_shipment.get("last_free_day", "")[:10]
            shipment_id = existing_shipment["id"]
            
            await db.shipments.update_one(
                {"id": shipment_id},
                {"$set": {
                    "vessel_name": vessel,
                    "arrival_date": arrival,
                    "last_free_day": lfd,
                    "bill_of_lading": bol,
                    "status": status,
                    "hours_remaining": round(hours, 1),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "notes": f"Updated via email parse on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC"
                }}
            )
            
            shipment_doc = {
                "id": shipment_id,
                "user_id": current_user["id"],
                "container_number": container,
                "vessel_name": vessel,
                "arrival_date": arrival,
                "last_free_day": lfd,
                "bill_of_lading": bol,
                "status": status,
                "hours_remaining": round(hours, 1),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "source": "test_email"
            }
        else:
            # CREATE new shipment
            shipment_id = str(uuid.uuid4())
            
            shipment_doc = {
                "id": shipment_id,
                "user_id": current_user["id"],
                "container_number": container,
                "vessel_name": vessel,
                "arrival_date": arrival,
                "last_free_day": lfd,
                "bill_of_lading": bol,
                "notes": "Created via Test Email Parse",
                "status": status,
                "hours_remaining": round(hours, 1),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source": "test_email"
            }
            
            await db.shipments.insert_one(shipment_doc)
            if '_id' in shipment_doc:
                del shipment_doc['_id']
        
        # Step 3: Send REAL SMS with appropriate message
        if is_update:
            sms_message = f"LFD Clock: SHIPMENT UPDATED!\n\nContainer: {container}\nVessel: {vessel}\nOld LFD: {old_lfd}\nNEW LFD: {lfd[:10]}\nStatus: {status.upper()}\nTime remaining: {round(hours, 1)}h"
        else:
            sms_message = f"LFD Clock: New shipment!\n\nContainer: {container}\nVessel: {vessel}\nLFD: {lfd[:10]}\nStatus: {status.upper()}\nTime remaining: {round(hours, 1)}h"
        
        sms_result = send_real_sms(request.phone_number, sms_message)
        
        # Log the SMS
        sms_log = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "shipment_id": shipment_id,
            "container_number": container,
            "message": sms_message,
            "notification_type": "update" if is_update else "new",
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "status": "sent_real",
            "twilio_sid": sms_result.get("sid")
        }
        await db.sms_logs.insert_one(sms_log)
        if '_id' in sms_log:
            del sms_log['_id']
        
        return {
            "success": True,
            "action": "updated" if is_update else "created",
            "message": f"Shipment {'UPDATED' if is_update else 'created'} and SMS sent!",
            "parsed_data": parsed_data,
            "shipment": shipment_doc,
            "sms": {
                "sent_to": sms_result.get("to"),
                "twilio_sid": sms_result.get("sid"),
                "status": sms_result.get("status")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test email-SMS error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

# ==================== CRON JOB - AUTOMATED REMINDERS ====================

@api_router.post("/cron/process-reminders")
async def process_pending_reminders():
    """
    CRON JOB: Run every hour to check and send pending reminders.
    Scans for reminders where schedule_time <= now and status = 'pending'.
    """
    now = datetime.now(timezone.utc)
    
    # Find all pending reminders that should be sent
    pending_reminders = await db.reminders.find({
        "status": "pending",
        "schedule_time": {"$lte": now.isoformat()}
    }, {"_id": 0}).to_list(1000)
    
    results = {
        "processed": 0,
        "sent": 0,
        "failed": 0,
        "skipped": 0,
        "details": []
    }
    
    for reminder in pending_reminders:
        results["processed"] += 1
        
        try:
            # Get the user for this reminder
            user = await db.users.find_one({"id": reminder["user_id"]}, {"_id": 0})
            if not user:
                results["skipped"] += 1
                continue
            
            # Check if user still wants this notification type
            user_settings = user.get("notification_settings", {})
            setting_key = f"notify_{reminder['reminder_type']}"
            if not user_settings.get(setting_key, True):
                # User disabled this notification type, mark as skipped
                await db.reminders.update_one(
                    {"id": reminder["id"]},
                    {"$set": {"status": "skipped", "processed_at": now.isoformat()}}
                )
                results["skipped"] += 1
                continue
            
            # Get user phone
            phone = user.get("phone")
            if not phone:
                await db.reminders.update_one(
                    {"id": reminder["id"]},
                    {"$set": {"status": "failed", "error": "No phone number", "processed_at": now.isoformat()}}
                )
                results["failed"] += 1
                continue
            
            # Send SMS
            hours_before = reminder.get("hours_before", "?")
            container = reminder.get("container_number", "UNKNOWN")
            sms_message = f"Alert: Container {container} expires in {hours_before} hours. Avoid storage fees!"
            
            sms_result = send_real_sms(phone, sms_message)
            
            # Update reminder status
            await db.reminders.update_one(
                {"id": reminder["id"]},
                {"$set": {
                    "status": "sent",
                    "processed_at": now.isoformat(),
                    "twilio_sid": sms_result.get("sid")
                }}
            )
            
            # Log the SMS
            sms_log = {
                "id": str(uuid.uuid4()),
                "user_id": reminder["user_id"],
                "shipment_id": reminder["shipment_id"],
                "container_number": container,
                "message": sms_message,
                "notification_type": f"reminder_{reminder['reminder_type']}",
                "sent_at": now.isoformat(),
                "status": "sent_real",
                "twilio_sid": sms_result.get("sid")
            }
            await db.sms_logs.insert_one(sms_log)
            
            results["sent"] += 1
            results["details"].append({
                "container": container,
                "type": reminder["reminder_type"],
                "status": "sent"
            })
            
        except Exception as e:
            logger.error(f"Error processing reminder {reminder['id']}: {str(e)}")
            await db.reminders.update_one(
                {"id": reminder["id"]},
                {"$set": {"status": "failed", "error": str(e), "processed_at": now.isoformat()}}
            )
            results["failed"] += 1
    
    return results

@api_router.get("/reminders")
async def get_user_reminders(current_user: dict = Depends(get_current_user)):
    """Get all reminders for the current user"""
    reminders = await db.reminders.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("schedule_time", 1).to_list(1000)
    return reminders

# ==================== DIRECT UPLOAD (DRAG & DROP) ====================

@api_router.post("/upload/pdf")
async def direct_upload_pdf(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Direct PDF upload: Drag & drop a PDF to parse it immediately.
    """
    import tempfile
    import os as os_module
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Read file content
        content = await file.read()
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Parse PDF with Gemini
            result = await parse_and_process_shipment(
                content=tmp_path,
                content_type="pdf",
                customer=current_user,
                source="direct_upload",
                filename=file.filename
            )
            return result
        finally:
            # Clean up temp file
            if os_module.path.exists(tmp_path):
                os_module.unlink(tmp_path)
                
    except Exception as e:
        logger.error(f"Direct upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# ==================== TRUCKER SHARE ====================

@api_router.post("/shipments/{shipment_id}/share-trucker")
async def share_with_trucker(
    shipment_id: str,
    request: TruckerShareRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Share container LFD details with a trucker via SMS.
    """
    shipment = await db.shipments.find_one({
        "id": shipment_id,
        "user_id": current_user["id"]
    }, {"_id": 0})
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    container = shipment.get("container_number", "UNKNOWN")
    vessel = shipment.get("vessel_name", "Unknown")
    lfd = shipment.get("last_free_day", "")[:10]
    carrier = shipment.get("carrier", "")
    status, hours = calculate_shipment_status(shipment.get("last_free_day", ""))
    
    trucker_name = request.trucker_name or "Driver"
    
    sms_message = f"Hi {trucker_name}, pickup needed:\n\nContainer: {container}\nVessel: {vessel}\nLFD: {lfd}\nTime left: {round(hours)}h\n\nFrom: {current_user.get('company_name', 'LFD Clock')}"
    
    try:
        sms_result = send_real_sms(request.trucker_phone, sms_message)
        
        # Log the SMS
        sms_log = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "shipment_id": shipment_id,
            "container_number": container,
            "message": sms_message,
            "notification_type": "trucker_share",
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "status": "sent_real",
            "twilio_sid": sms_result.get("sid"),
            "trucker_phone": request.trucker_phone
        }
        await db.sms_logs.insert_one(sms_log)
        
        return {
            "success": True,
            "message": f"LFD details sent to {request.trucker_phone}",
            "sms_sid": sms_result.get("sid")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send SMS: {str(e)}")

# ==================== CARRIER PORTAL LINKS ====================

@api_router.get("/shipments/{shipment_id}/carrier-portal")
async def get_carrier_portal_link(
    shipment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get the carrier tracking portal URL for a shipment"""
    shipment = await db.shipments.find_one({
        "id": shipment_id,
        "user_id": current_user["id"]
    }, {"_id": 0})
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    carrier = shipment.get("carrier", shipment.get("vessel_name", ""))
    portal_url = get_carrier_portal(carrier)
    
    return {
        "carrier": carrier,
        "portal_url": portal_url,
        "container_number": shipment.get("container_number")
    }

@api_router.get("/")
async def root():
    return {"message": "LFD Clock API is running"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "lfd-clock"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Background task for automated reminders
import asyncio

async def reminder_scheduler():
    """Background task that checks reminders every 5 minutes"""
    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes
            
            now = datetime.now(timezone.utc)
            
            # Find all pending reminders that should be sent
            pending_reminders = await db.reminders.find({
                "status": "pending",
                "schedule_time": {"$lte": now.isoformat()}
            }, {"_id": 0}).to_list(100)
            
            for reminder in pending_reminders:
                try:
                    # Get the user for this reminder
                    user = await db.users.find_one({"id": reminder["user_id"]}, {"_id": 0})
                    if not user:
                        continue
                    
                    # Check if user still wants this notification type
                    user_settings = user.get("notification_settings", {})
                    setting_key = f"notify_{reminder['reminder_type']}"
                    if not user_settings.get(setting_key, True):
                        await db.reminders.update_one(
                            {"id": reminder["id"]},
                            {"$set": {"status": "skipped", "processed_at": now.isoformat()}}
                        )
                        continue
                    
                    # Get user phone
                    phone = user.get("phone")
                    if not phone:
                        await db.reminders.update_one(
                            {"id": reminder["id"]},
                            {"$set": {"status": "failed", "error": "No phone number", "processed_at": now.isoformat()}}
                        )
                        continue
                    
                    # Send SMS
                    hours_before = reminder.get("hours_before", "?")
                    container = reminder.get("container_number", "UNKNOWN")
                    sms_message = f"Alert: Container {container} expires in {hours_before} hours. Avoid storage fees!"
                    
                    sms_result = send_real_sms(phone, sms_message)
                    
                    # Update reminder status
                    await db.reminders.update_one(
                        {"id": reminder["id"]},
                        {"$set": {
                            "status": "sent",
                            "processed_at": now.isoformat(),
                            "twilio_sid": sms_result.get("sid")
                        }}
                    )
                    
                    # Log the SMS
                    sms_log = {
                        "id": str(uuid.uuid4()),
                        "user_id": reminder["user_id"],
                        "shipment_id": reminder["shipment_id"],
                        "container_number": container,
                        "message": sms_message,
                        "notification_type": f"reminder_{reminder['reminder_type']}",
                        "sent_at": now.isoformat(),
                        "status": "sent_real",
                        "twilio_sid": sms_result.get("sid")
                    }
                    await db.sms_logs.insert_one(sms_log)
                    
                    logger.info(f"Sent {reminder['reminder_type']} reminder for {container} to {phone}")
                    
                except Exception as e:
                    logger.error(f"Error processing reminder {reminder.get('id')}: {str(e)}")
                    await db.reminders.update_one(
                        {"id": reminder["id"]},
                        {"$set": {"status": "failed", "error": str(e), "processed_at": now.isoformat()}}
                    )
                    
        except Exception as e:
            logger.error(f"Reminder scheduler error: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Start background tasks on app startup"""
    asyncio.create_task(reminder_scheduler())
    logger.info("Reminder scheduler started - checking every 5 minutes")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
