from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from sqlmodel import Session, select

from db import get_session, create_db_and_tables
from models import User, UserRole, Booking, Stylist
from crud import create_stylist_user, create_user, get_user_by_email, authenticate_user, get_stylist_by_user_id, create_booking, get_bookings_by_stylist, get_booking_by_id, update_booking, delete_booking, get_upcoming_bookings_by_stylist, get_stylist_by_id, create_public_booking
from schemas import SignUp, StylistSignUp, AdminSignUp, Login, BookingCreate, BookingUpdate, BookingPublic, PublicBookingCreate
from auth import create_access_token, get_current_user
from notifications import send_booking_confirmation_emails
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


@app.get("/api/profile")
def get_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get user profile information for dashboard sidebar and general user data.
    
    Returns the same structure as dashboard but focused on user profile data.
    This endpoint is used by the dashboard to populate user information in the sidebar.
    """
    # Prepare response based on user role
    profile_data = {
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "phone": current_user.phone,
            "role": current_user.role,
            "created_at": current_user.created_at.isoformat()
        }
    }
    
    # Add stylist profile information if user is a stylist
    if current_user.role == UserRole.stylist:
        session = next(get_session())
        stylist = get_stylist_by_user_id(session, current_user.id)
        
        if stylist:
            profile_data["user"]["stylist_profile"] = {
                "id": stylist.id,
                "business_name": stylist.business_name,
                "bio": stylist.bio,
                "profile_image_url": stylist.profile_image_url
            }
    
    return profile_data


@app.get("/api/bookings", response_model=dict)
def get_bookings(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """
    Get bookings for the current user (stylist).
    
    Only stylists can access their bookings. Returns real bookings from the database.
    """
    # Only stylists can access bookings
    if current_user.role != UserRole.stylist:
        raise HTTPException(status_code=403, detail="Only stylists can access bookings")
    
    # Get stylist profile
    stylist = get_stylist_by_user_id(session, current_user.id)
    if not stylist:
        raise HTTPException(status_code=404, detail="Stylist profile not found")
    
    # Get upcoming bookings
    bookings = get_upcoming_bookings_by_stylist(session, stylist.id)
    
    # Convert to response format matching the frontend expectation
    booking_list = []
    for booking in bookings:
        booking_list.append({
            "id": booking.id,
            "client_name": booking.client_name,
            "client_email": booking.client_email,
            "client_phone": booking.client_phone,
            "service_name": booking.service_name,
            "service_description": booking.service_description,
            "appointment_date": booking.appointment_date.isoformat(),
            "appointment_time": booking.appointment_time.strftime("%I:%M %p"),
            "duration_minutes": booking.duration_minutes,
            "price": booking.price,
            "status": booking.status.value,
            "notes": booking.notes,
            "created_at": booking.created_at.isoformat(),
            "updated_at": booking.updated_at.isoformat()
        })
    
    return {
        "bookings": booking_list,
        "total": len(booking_list),
        "has_more": False
    }


@app.post("/api/bookings", response_model=BookingPublic)
def create_new_booking(booking_data: BookingCreate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """
    Create a new booking for the current stylist.
    
    Only stylists can create bookings. The booking will be associated with the current stylist's profile.
    """
    # Only stylists can create bookings
    if current_user.role != UserRole.stylist:
        raise HTTPException(status_code=403, detail="Only stylists can create bookings")
    
    # Get stylist profile
    stylist = get_stylist_by_user_id(session, current_user.id)
    if not stylist:
        raise HTTPException(status_code=404, detail="Stylist profile not found")
    
    # Create the booking
    try:
        booking = create_booking(session, stylist.id, booking_data)
        return booking
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create booking: {str(e)}")


@app.get("/api/bookings/{booking_id}", response_model=BookingPublic)
def get_booking_detail(booking_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """
    Get details of a specific booking.
    
    Only stylists can access their own bookings.
    """
    # Only stylists can access bookings
    if current_user.role != UserRole.stylist:
        raise HTTPException(status_code=403, detail="Only stylists can access bookings")
    
    # Get stylist profile
    stylist = get_stylist_by_user_id(session, current_user.id)
    if not stylist:
        raise HTTPException(status_code=404, detail="Stylist profile not found")
    
    # Get the booking
    booking = get_booking_by_id(session, booking_id, stylist.id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return booking


@app.put("/api/bookings/{booking_id}", response_model=BookingPublic)
def update_booking_detail(booking_id: int, booking_data: BookingUpdate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """
    Update a specific booking.
    
    Only stylists can update their own bookings.
    """
    # Only stylists can update bookings
    if current_user.role != UserRole.stylist:
        raise HTTPException(status_code=403, detail="Only stylists can update bookings")
    
    # Get stylist profile
    stylist = get_stylist_by_user_id(session, current_user.id)
    if not stylist:
        raise HTTPException(status_code=404, detail="Stylist profile not found")
    
    # Update the booking
    updated_booking = update_booking(session, booking_id, booking_data, stylist.id)
    if not updated_booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return updated_booking


@app.delete("/api/bookings/{booking_id}")
def delete_booking_detail(booking_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """
    Delete a specific booking.
    
    Only stylists can delete their own bookings.
    """
    # Only stylists can delete bookings
    if current_user.role != UserRole.stylist:
        raise HTTPException(status_code=403, detail="Only stylists can delete bookings")
    
    # Get stylist profile
    stylist = get_stylist_by_user_id(session, current_user.id)
    if not stylist:
        raise HTTPException(status_code=404, detail="Stylist profile not found")
    
    # Delete the booking
    if not delete_booking(session, booking_id, stylist.id):
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return {"message": "Booking deleted successfully"}


@app.post("/api/public/bookings", response_model=BookingPublic)
def create_public_booking_endpoint(booking_data: PublicBookingCreate, session: Session = Depends(get_session)):
    """
    Create a new booking publicly (no authentication required).
    
    This endpoint allows anyone to create a booking with a specific stylist.
    Perfect for social media links where stylists share their booking page.
    
    Features:
    - No authentication required
    - Validates stylist exists
    - Sends confirmation emails to both client and stylist
    - Rate limiting protection (future: implement with slowapi or similar)
    """
    
    # Validate stylist exists
    stylist = get_stylist_by_id(session, booking_data.stylist_id)
    if not stylist:
        raise HTTPException(status_code=404, detail=f"Stylist with ID {booking_data.stylist_id} not found")
    
    # Get stylist user information for email notifications
    stylist_user = session.exec(select(User).where(User.id == stylist.user_id)).first()
    if not stylist_user:
        raise HTTPException(status_code=404, detail="Stylist user information not found")
    
    # Create the booking
    try:
        booking = create_public_booking(session, booking_data)
        
        # Send confirmation emails (placeholder function)
        try:
            send_booking_confirmation_emails(booking, stylist, stylist_user)
        except Exception as email_error:
            # Don't fail the booking if email sending fails
            print(f"Email sending failed (non-critical): {email_error}")
        
        return booking
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create booking: {str(e)}")


@app.get("/api/public/stylists/{stylist_id}", response_model=dict)
def get_public_stylist_info(stylist_id: int, session: Session = Depends(get_session)):
    """
    Get public stylist information for booking page.
    
    This endpoint provides stylist details that can be displayed on the public booking page.
    No authentication required - this is public information.
    """
    
    # Get stylist with user information
    result = session.exec(
        select(Stylist, User)
        .join(User, Stylist.user_id == User.id)
        .where(Stylist.id == stylist_id)
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Stylist not found")
    
    stylist, user = result
    
    return {
        "stylist": {
            "id": stylist.id,
            "business_name": stylist.business_name,
            "bio": stylist.bio,
            "profile_image_url": stylist.profile_image_url,
            "name": user.name,
            "phone": user.phone  # Public contact info
        }
    }


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