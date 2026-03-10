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

# ==================== HELPERS ====================

def generate_forwarding_email(user_id: str) -> str:
    """Generate unique forwarding email for user"""
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

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/signup")
async def signup(user_data: UserCreate):
    # Check if user exists
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    forwarding_email = generate_forwarding_email(user_id)
    
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "password_hash": hash_password(user_data.password),
        "company_name": user_data.company_name,
        "phone": user_data.phone,
        "forwarding_email": forwarding_email,
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
            "forwarding_email": user["forwarding_email"],
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
        "forwarding_email": current_user["forwarding_email"],
        "created_at": current_user["created_at"]
    }

# ==================== SHIPMENT ROUTES ====================

@api_router.get("/shipments", response_model=List[ShipmentResponse])
async def get_shipments(current_user: dict = Depends(get_current_user)):
    shipments = await db.shipments.find(
        {"user_id": current_user["id"]}, 
        {"_id": 0}
    ).sort("last_free_day", 1).to_list(1000)
    
    # Update status for each shipment
    for shipment in shipments:
        status, hours = calculate_shipment_status(shipment["last_free_day"])
        shipment["status"] = status
        shipment["hours_remaining"] = round(hours, 1)
    
    return shipments

@api_router.post("/shipments", response_model=ShipmentResponse)
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
        "source": "manual"
    }
    
    await db.shipments.insert_one(shipment_doc)
    return shipment_doc

@api_router.delete("/shipments/{shipment_id}")
async def delete_shipment(
    shipment_id: str,
    current_user: dict = Depends(get_current_user)
):
    result = await db.shipments.delete_one({
        "id": shipment_id,
        "user_id": current_user["id"]
    })
    
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
        "expired": 0
    }
    
    for shipment in shipments:
        status, _ = calculate_shipment_status(shipment["last_free_day"])
        if status in stats:
            stats[status] += 1
    
    return stats

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
            created.append(shipment_doc)
    
    return {
        "message": f"Created {len(created)} demo shipments",
        "shipments": created
    }

# ==================== HEALTH CHECK ====================

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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
