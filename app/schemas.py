
from typing import Optional, Union, Literal
from datetime import date, time, datetime

from pydantic import BaseModel, EmailStr, Field, validator
from models import UserRole, BookingStatus


class StylistSignUp(BaseModel):
    role: Literal["stylist"] = Field(default="stylist", description="User role - must be 'stylist'")
    name: str = Field(description="Full name")
    email: EmailStr = Field(description="Email address")
    password: str = Field(min_length=6, description="Password (minimum 6 characters)")
    phone: Optional[str] = Field(default=None, description="Phone number (optional)")
    
    # Required fields for stylists
    business_name: str = Field(min_length=1, description="Business name (required for stylists)")
    bio: str = Field(min_length=10, description="Professional bio (minimum 10 characters)")
    profile_image_url: Optional[str] = Field(default=None, description="Profile image URL (optional)")
    
    @validator('business_name')
    def validate_business_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Business name cannot be empty')
        return v.strip()
    
    @validator('bio')
    def validate_bio(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('Bio must be at least 10 characters long')
        return v.strip()

    class Config:
        schema_extra = {
            "example": {
                "role": "stylist",
                "name": "Jane Doe",
                "email": "jane@hairstudio.com",
                "password": "securepassword123",
                "phone": "+254712345678",
                "business_name": "Jane's Hair Studio",
                "bio": "Professional hairstylist with 5+ years of experience specializing in natural hair care and styling.",
                "profile_image_url": "https://example.com/jane-profile.jpg"
            }
        }


class AdminSignUp(BaseModel):
    role: Literal["admin"] = Field(default="admin", description="User role - must be 'admin'")
    name: str = Field(description="Full name")
    email: EmailStr = Field(description="Email address")
    password: str = Field(min_length=6, description="Password (minimum 6 characters)")
    phone: Optional[str] = Field(default=None, description="Phone number (optional)")

    class Config:
        schema_extra = {
            "example": {
                "role": "admin",
                "name": "John Smith",
                "email": "admin@quikka.com",
                "password": "adminpassword123",
                "phone": "+254787654321"
            }
        }


# Login schema
class Login(BaseModel):
    email: EmailStr = Field(description="Email address")
    password: str = Field(description="Password")

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "yourpassword"
            }
        }


# Union type for the signup endpoint - FastAPI will show both options in Swagger
SignUp = Union[StylistSignUp, AdminSignUp]


# Booking schemas
class BookingCreate(BaseModel):
    client_name: str = Field(description="Client's full name")
    client_email: EmailStr = Field(description="Client's email address")
    client_phone: Optional[str] = Field(default=None, description="Client's phone number (optional)")
    
    service_name: str = Field(description="Name of the service (e.g., 'Haircut', 'Manicure')")
    service_description: Optional[str] = Field(default=None, description="Additional service details")
    
    appointment_date: date = Field(description="Date of the appointment (YYYY-MM-DD)")
    appointment_time: time = Field(description="Time of the appointment (HH:MM)")
    duration_minutes: int = Field(default=60, ge=15, le=480, description="Duration in minutes (15-480 min)")
    
    price: float = Field(ge=0, description="Service price")
    currency: str = Field(default="KES", description="Currency code")
    
    notes: Optional[str] = Field(default=None, description="Additional notes")

    @validator('appointment_date')
    def validate_appointment_date(cls, v):
        from datetime import date as dt_date
        if v < dt_date.today():
            raise ValueError('Appointment date cannot be in the past')
        return v

    class Config:
        schema_extra = {
            "example": {
                "client_name": "Jane Doe",
                "client_email": "jane.doe@example.com",
                "client_phone": "+254712345678",
                "service_name": "Hair Cut & Style",
                "service_description": "Full haircut with styling",
                "appointment_date": "2024-12-25",
                "appointment_time": "14:30",
                "duration_minutes": 90,
                "price": 2500.0,
                "currency": "KES",
                "notes": "Client prefers natural products"
            }
        }


class BookingUpdate(BaseModel):
    client_name: Optional[str] = Field(default=None, description="Client's full name")
    client_email: Optional[EmailStr] = Field(default=None, description="Client's email address")
    client_phone: Optional[str] = Field(default=None, description="Client's phone number")
    
    service_name: Optional[str] = Field(default=None, description="Name of the service")
    service_description: Optional[str] = Field(default=None, description="Service description")
    
    appointment_date: Optional[date] = Field(default=None, description="Date of the appointment")
    appointment_time: Optional[time] = Field(default=None, description="Time of the appointment")
    duration_minutes: Optional[int] = Field(default=None, ge=15, le=480, description="Duration in minutes")
    
    price: Optional[float] = Field(default=None, ge=0, description="Service price")
    currency: Optional[str] = Field(default=None, description="Currency code")
    
    status: Optional[BookingStatus] = Field(default=None, description="Booking status")
    notes: Optional[str] = Field(default=None, description="Additional notes")
    
    # Reschedule fields
    reschedule_reason: Optional[str] = Field(default=None, description="Reason for reschedule request")

    @validator('appointment_date')
    def validate_appointment_date(cls, v):
        if v is not None:
            from datetime import date as dt_date
            if v < dt_date.today():
                raise ValueError('Appointment date cannot be in the past')
        return v


# New schema for status updates
class BookingStatusUpdate(BaseModel):
    status: BookingStatus = Field(description="New booking status")
    reason: Optional[str] = Field(default=None, description="Reason for status change")

    class Config:
        schema_extra = {
            "example": {
                "status": "completed",
                "reason": "Service completed successfully"
            }
        }


# New schema for reschedule requests
class BookingRescheduleRequest(BaseModel):
    new_appointment_date: date = Field(description="Requested new date")
    new_appointment_time: time = Field(description="Requested new time")
    reschedule_reason: str = Field(description="Reason for reschedule request")

    @validator('new_appointment_date')
    def validate_new_appointment_date(cls, v):
        from datetime import date as dt_date
        if v < dt_date.today():
            raise ValueError('New appointment date cannot be in the past')
        return v

    class Config:
        schema_extra = {
            "example": {
                "new_appointment_date": "2025-09-25",
                "new_appointment_time": "15:00",
                "reschedule_reason": "Client has a conflict with original time"
            }
        }


class BookingPublic(BaseModel):
    id: int
    stylist_id: int
    
    client_name: str
    client_email: str
    client_phone: Optional[str]
    
    service_name: str
    service_description: Optional[str]
    
    appointment_date: date
    appointment_time: time
    duration_minutes: int
    
    # Reschedule information
    original_appointment_date: Optional[date]
    original_appointment_time: Optional[time]
    reschedule_count: int
    reschedule_reason: Optional[str]
    
    # Professional type
    professional_type: str
    
    price: float
    currency: str
    
    status: BookingStatus
    notes: Optional[str]
    
    # Cancellation rules
    cancellation_deadline_hours: int
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Allows conversion from SQLModel objects


class BookingWithStylist(BookingPublic):
    """Booking response that includes stylist information"""
    stylist_business_name: str
    stylist_name: str
    stylist_email: str


class PublicBookingCreate(BaseModel):
    """Schema for public booking creation (no authentication required)"""
    stylist_id: int = Field(description="ID of the stylist to book with")
    
    client_name: str = Field(description="Client's full name")
    client_email: EmailStr = Field(description="Client's email address")
    client_phone: Optional[str] = Field(default=None, description="Client's phone number (optional)")
    
    service_name: str = Field(description="Name of the service (e.g., 'Haircut', 'Manicure')")
    service_description: Optional[str] = Field(default=None, description="Additional service details")
    
    appointment_date: date = Field(description="Date of the appointment (YYYY-MM-DD)")
    appointment_time: time = Field(description="Time of the appointment (HH:MM)")
    duration_minutes: int = Field(default=60, ge=15, le=480, description="Duration in minutes (15-480 min)")
    
    price: float = Field(ge=0, description="Service price")
    currency: str = Field(default="KES", description="Currency code")
    
    notes: Optional[str] = Field(default=None, description="Additional notes")

    @validator('appointment_date')
    def validate_appointment_date(cls, v):
        from datetime import date as dt_date
        if v < dt_date.today():
            raise ValueError('Appointment date cannot be in the past')
        return v

    class Config:
        schema_extra = {
            "example": {
                "stylist_id": 1,
                "client_name": "Jane Doe",
                "client_email": "jane.doe@example.com",
                "client_phone": "+254712345678",
                "service_name": "Hair Cut & Style",
                "service_description": "Full haircut with styling",
                "appointment_date": "2025-09-25",
                "appointment_time": "14:30",
                "duration_minutes": 90,
                "price": 3500.0,
                "currency": "KES",
                "notes": "Client prefers natural products"
            }
        }
