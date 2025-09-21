from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from db import get_session, create_db_and_tables
from models import User, UserRole
from crud import create_stylist_user, create_user, get_user_by_email, authenticate_user, get_stylist_by_user_id
from schemas import SignUp, StylistSignUp, AdminSignUp, Login
from auth import create_access_token, get_current_user
import hashlib
import os


#App instance
app = FastAPI()

# Configure paths for static files and templates
BASE_DIR = Path(__file__).parent.parent  # Parent of app/ directory
STATIC_DIR = BASE_DIR / "frontend"
TEMPLATES_DIR = STATIC_DIR / "templates"

# Mount static files
app.mount("/frontend", StaticFiles(directory=str(STATIC_DIR)), name="frontend")

# CORS (needed for browser fetch from a different origin/port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your front-end origin in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Serve the landing page"""
    return FileResponse(str(TEMPLATES_DIR / "landing.html"))


@app.get("/auth")
async def auth_page():
    """Serve the authentication page"""
    return FileResponse(str(TEMPLATES_DIR / "sign_up.html"))


@app.get("/dashboard")
async def dashboard_page():
    """Serve the dashboard page (HTML)"""
    return FileResponse(str(TEMPLATES_DIR / "dashboard.html"))


@app.get("/api")
async def api_root():
    """API status endpoint"""
    return {"message": "Quikka API is running", "version": "1.0.0"}

@app.on_event("startup")
def on_startup():
    create_db_and_tables()


def hash_password(password: str) -> str:
    # Simple PBKDF2-HMAC-SHA256 (you can swap to bcrypt/argon2 later)
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return f"pbkdf2_sha256$100000${salt.hex()}${dk.hex()}"


@app.post("/api/signup")
def sign_up(payload: SignUp, session = Depends(get_session)):
    """
    User signup endpoint supporting different roles.
    
    - **Stylist**: Creates user account with business profile (requires business_name and bio)
    - **Admin**: Creates admin user account with basic information only
    """
    # Validate uniqueness first
    existing = get_user_by_email(session, payload.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    
    # Handle different signup flows based on role
    if payload.role == "stylist":
        # TypeScript will narrow the type, but we can be explicit
        stylist_payload = payload if isinstance(payload, StylistSignUp) else payload
        
        # Create stylist user (both User + Stylist records)
        user, stylist = create_stylist_user(session, stylist_payload, hash_password(payload.password))
        
        return {
            "message": "Stylist account created successfully",
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "stylist_id": stylist.id,
                "business_name": stylist.business_name
            }
        }
    
    elif payload.role == "admin":
        # Create admin user (only User record)
        user = create_user(
            session=session,
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            role=UserRole.admin,
            password_hash=hash_password(payload.password)
        )
        
        return {
            "message": "Admin account created successfully",
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role
            }
        }
    
    else:
        raise HTTPException(status_code=400, detail=f"Signup not implemented for role: {payload.role}")


@app.post("/api/login")
def login(payload: Login, session = Depends(get_session)):
    """
    User login endpoint for all user types.
    
    Returns JWT access token and user information with role-specific data:
    - **Stylist**: Returns token + user info + business profile data
    - **Admin**: Returns token + user info only
    """
    # Authenticate user
    user = authenticate_user(session, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create JWT token
    access_token = create_access_token(data={"sub": user.email})
    
    # Prepare base response
    response = {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "role": user.role,
            "created_at": user.created_at.isoformat()
        }
    }
    
    # Add role-specific data
    if user.role == UserRole.stylist:
        stylist = get_stylist_by_user_id(session, user.id)
        if stylist:
            response["user"]["stylist_profile"] = {
                "id": stylist.id,
                "business_name": stylist.business_name,
                "bio": stylist.bio,
                "profile_image_url": stylist.profile_image_url
            }
    
    return response


@app.get("/api/dashboard")
def dashboard(current_user: User = Depends(get_current_user)):
    """
    Protected dashboard endpoint that requires authentication.
    
    This demonstrates how to protect any endpoint with JWT authentication.
    Only logged-in users with valid tokens can access this endpoint.
    """
    # Prepare response based on user role
    dashboard_data = {
        "message": f"Welcome to your dashboard, {current_user.name}!",
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "phone": current_user.phone,
            "role": current_user.role,
            "created_at": current_user.created_at.isoformat()
        },
        "dashboard_features": []
    }
    
    # Add role-specific dashboard features
    if current_user.role == UserRole.stylist:
        # Get stylist profile for additional context
        session = next(get_session())
        stylist = get_stylist_by_user_id(session, current_user.id)
        
        dashboard_data["dashboard_features"] = [
            "Manage appointments",
            "Update business profile",
            "View customer reviews",
            "Analytics dashboard"
        ]
        
        if stylist:
            dashboard_data["business_info"] = {
                "business_name": stylist.business_name,
                "bio": stylist.bio
            }
    
    elif current_user.role == UserRole.admin:
        dashboard_data["dashboard_features"] = [
            "User management",
            "System analytics",
            "Content moderation",
            "Platform settings"
        ]
    
    return dashboard_data


@app.post("/api/logout")
def logout(current_user: User = Depends(get_current_user)):
    """
    User logout endpoint.
    
    Note: With JWT tokens, logout is primarily handled client-side by removing 
    the token from storage. This endpoint confirms the logout action and could 
    be extended to implement token blacklisting for enhanced security.
    """
    return {
        "message": f"Successfully logged out {current_user.name}",
        "instruction": "Please remove the token from your client storage (localStorage/sessionStorage)"
    }