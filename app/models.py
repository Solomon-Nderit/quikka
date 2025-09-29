from __future__ import annotations

import enum
from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from typing import Optional, List
from datetime import datetime, date, time

from sqlmodel import Field, SQLModel


class UserRole(str, enum.Enum):
    stylist = "stylist"
    admin = "admin"
    # Easy to add: customer = "customer", freelancer = "freelancer", etc.


class BookingStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    reschedule_requested = "reschedule_requested"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"


class DayOfWeek(int, enum.Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


# Main User table - common fields for all user types
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(index=True, sa_column_kwargs={"unique": True})
    phone: Optional[str] = Field(default=None, index=True, sa_column_kwargs={"unique": True})
    password_hash: str
    role: UserRole = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)

# Stylist-specific table
class Stylist(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)  # One-to-one with User
    business_name: str  # Required for stylists
    bio: str  # Required for stylists
    profile_image_url: Optional[str] = None


# Booking table - for appointments/bookings made with stylists
class Booking(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Stylist relationship (who is providing the service) - simple foreign key
    stylist_id: int = Field(foreign_key="stylist.id")
    
    # Client information (for now storing as text, can be normalized later to separate Client table)
    client_name: str
    client_email: str
    client_phone: Optional[str] = None
    
    # Service details
    service_name: str  # e.g., "Haircut", "Manicure", "Facial"
    service_description: Optional[str] = None
    
    # Appointment timing
    appointment_date: date
    appointment_time: time
    duration_minutes: int = Field(default=60)  # Default 1 hour
    
    # Reschedule tracking
    original_appointment_date: Optional[date] = None
    original_appointment_time: Optional[time] = None
    reschedule_count: int = Field(default=0)  # Track number of reschedules
    reschedule_reason: Optional[str] = None
    reschedule_requested_at: Optional[datetime] = None
    
    # Professional type for future expansion
    professional_type: str = Field(default="stylist")
    
    # Pricing
    price: float = Field(default=0.0)  # Service price
    currency: str = Field(default="KES")  # Kenyan Shillings
    
    # Status and metadata
    status: BookingStatus = Field(default=BookingStatus.pending)
    notes: Optional[str] = None  # Additional notes from client or stylist
    
    # Cancellation rules (can be overridden by professional settings)
    cancellation_deadline_hours: int = Field(default=24)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


# Stylist availability table - defines when stylists are available for bookings
class StylistAvailability(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Stylist relationship
    stylist_id: int = Field(foreign_key="stylist.id")
    
    # Day of the week (0=Monday, 1=Tuesday, ..., 6=Sunday)
    day_of_week: DayOfWeek
    
    # Available time range for this day
    start_time: time = Field(description="Start of available hours (e.g., 08:00)")
    end_time: time = Field(description="End of available hours (e.g., 17:00)")
    
    # Active flag (allows temporary disabling without deletion)
    is_active: bool = Field(default=True)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


# Professional settings table - for business rules and preferences
class ProfessionalSettings(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Links to existing professional (stylist for now)
    stylist_id: Optional[int] = Field(foreign_key="stylist.id", default=None)
    # Future: therapist_id, trainer_id, etc.
    
    # Professional type identifier
    professional_type: str = Field(default="stylist")
    
    # Cancellation and reschedule rules
    cancellation_deadline_hours: int = Field(default=24, description="Hours before appointment when cancellation is allowed")
    max_reschedules_allowed: int = Field(default=2, description="Maximum reschedules per booking")
    no_show_grace_period_minutes: int = Field(default=60, description="Minutes after appointment time before marking as no-show")
    
    # Auto-confirmation settings (for future payment integration)
    auto_confirm_bookings: bool = Field(default=False, description="Automatically confirm bookings without manual approval")
    require_prepayment: bool = Field(default=False, description="Require payment before confirming booking")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


# Booking status history table - tracks all status changes
class BookingStatusHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    booking_id: int = Field(foreign_key="booking.id")
    
    old_status: Optional[BookingStatus] = None
    new_status: BookingStatus
    
    # Who made the change
    changed_by_user_id: int = Field(foreign_key="user.id")
    change_reason: Optional[str] = None
    
    # Timestamp
    changed_at: datetime = Field(default_factory=datetime.now)
 

# Request schemas
class UserCreate(SQLModel):
    name: str
    email: str
    phone: Optional[str] = None
    password: str
    role: UserRole


class StylistSignup(SQLModel):
    # User fields
    name: str
    email: str
    phone: Optional[str] = None
    password: str
    role: UserRole = Field(default=UserRole.stylist)
    
    # Required stylist fields
    business_name: str
    bio: str
    profile_image_url: Optional[str] = None


# Response schemas
class UserPublic(SQLModel):
    id: int
    name: str
    email: str
    phone: Optional[str]
    role: UserRole
    created_at: datetime


class StylistPublic(SQLModel):
    id: int
    user_id: int
    business_name: str
    bio: str
    profile_image_url: Optional[str]
    # Include user data
    user: UserPublic
