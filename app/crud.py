from typing import Optional, List
from datetime import datetime

from sqlmodel import Session, select

from models import Stylist, User, UserCreate, StylistSignup, UserRole, Booking, BookingStatus
from schemas import BookingCreate, BookingUpdate
import hashlib


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash"""
    try:
        # Split the stored hash format: pbkdf2_sha256$100000$salt$hash
        parts = password_hash.split('$')
        if len(parts) != 4 or parts[0] != 'pbkdf2_sha256':
            return False
        
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        stored_hash = parts[3]
        
        # Hash the provided password with the same salt and iterations
        new_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
        
        # Compare the hashes
        return stored_hash == new_hash.hex()
    except (ValueError, IndexError):
        return False


def authenticate_user(session: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user by email and password"""
    user = get_user_by_email(session, email)
    if not user:
        return None
    
    if not verify_password(password, user.password_hash):
        return None
    
    return user


def get_user_by_email(session: Session, email: str) -> Optional[User]:
    return session.exec(select(User).where(User.email == email)).first()


def get_user_by_phone(session: Session, phone: str) -> Optional[User]:
    return session.exec(select(User).where(User.phone == phone)).first()


def create_user(session: Session, name: str, email: str, phone: Optional[str], role: UserRole, password_hash: str) -> User:
    """Create a basic User record"""
    user = User(
        name=name,
        email=email,
        phone=phone,
        role=role,
        password_hash=password_hash
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_stylist_profile(session: Session, user_id: int, business_name: str, bio: str, profile_image_url: Optional[str] = None) -> Stylist:
    """Create a Stylist profile linked to a User"""
    stylist = Stylist(
        user_id=user_id,
        business_name=business_name,
        bio=bio,
        profile_image_url=profile_image_url
    )
    session.add(stylist)
    session.commit()
    session.refresh(stylist)
    return stylist


def create_stylist_user(session: Session, payload: StylistSignup, password_hash: str) -> tuple[User, Stylist]:
    """Create both User and Stylist records in one transaction"""
    # Create user first
    user = create_user(
        session=session,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        role=payload.role,
        password_hash=password_hash
    )
    
    # Create stylist profile
    stylist = create_stylist_profile(
        session=session,
        user_id=user.id,
        business_name=payload.business_name,
        bio=payload.bio,
        profile_image_url=payload.profile_image_url
    )
    
    return user, stylist


def get_stylists(session: Session, offset: int = 0, limit: int = 100) -> list[Stylist]:
    """Get all stylists with their user data"""
    return session.exec(select(Stylist).offset(offset).limit(limit)).all()


def get_stylist_by_user_id(session: Session, user_id: int) -> Optional[Stylist]:
    """Get stylist profile by user ID"""
    return session.exec(select(Stylist).where(Stylist.user_id == user_id)).first()


def get_stylist_by_id(session: Session, stylist_id: int) -> Optional[Stylist]:
    """Get stylist profile by stylist ID"""
    return session.exec(select(Stylist).where(Stylist.id == stylist_id)).first()


def get_stylist_with_user(session: Session, stylist_id: int) -> Optional[tuple[Stylist, User]]:
    """Get stylist with their user data using a join"""
    result = session.exec(
        select(Stylist, User)
        .join(User, Stylist.user_id == User.id)
        .where(Stylist.id == stylist_id)
    ).first()
    return result


def get_all_stylists_with_users(session: Session, offset: int = 0, limit: int = 100) -> list[tuple[Stylist, User]]:
    """Get all stylists with their user data using a join"""
    results = session.exec(
        select(Stylist, User)
        .join(User, Stylist.user_id == User.id)
        .offset(offset)
        .limit(limit)
    ).all()
    return results


# Future CRUD functions for other user types:
# def create_customer_profile(session: Session, user_id: int, preferences: Optional[str] = None) -> Customer:
#     customer = Customer(user_id=user_id, preferences=preferences)
#     session.add(customer)
#     session.commit()
#     session.refresh(customer)
#     return customer


# Booking CRUD operations
def create_booking(session: Session, stylist_id: int, booking_data: BookingCreate) -> Booking:
    """Create a new booking for a stylist"""
    booking = Booking(
        stylist_id=stylist_id,
        client_name=booking_data.client_name,
        client_email=booking_data.client_email,
        client_phone=booking_data.client_phone,
        service_name=booking_data.service_name,
        service_description=booking_data.service_description,
        appointment_date=booking_data.appointment_date,
        appointment_time=booking_data.appointment_time,
        duration_minutes=booking_data.duration_minutes,
        price=booking_data.price,
        currency=booking_data.currency,
        notes=booking_data.notes,
        status=BookingStatus.pending  # New bookings start as pending
    )
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking


def create_public_booking(session: Session, booking_data) -> Booking:
    """Create a new booking from public request (includes stylist_id in the data)"""
    booking = Booking(
        stylist_id=booking_data.stylist_id,
        client_name=booking_data.client_name,
        client_email=booking_data.client_email,
        client_phone=booking_data.client_phone,
        service_name=booking_data.service_name,
        service_description=booking_data.service_description,
        appointment_date=booking_data.appointment_date,
        appointment_time=booking_data.appointment_time,
        duration_minutes=booking_data.duration_minutes,
        price=booking_data.price,
        currency=booking_data.currency,
        notes=booking_data.notes,
        status=BookingStatus.pending  # New bookings start as pending
    )
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking


def get_bookings_by_stylist(session: Session, stylist_id: int, offset: int = 0, limit: int = 100) -> List[Booking]:
    """Get all bookings for a specific stylist"""
    return session.exec(
        select(Booking)
        .where(Booking.stylist_id == stylist_id)
        .order_by(Booking.appointment_date.desc(), Booking.appointment_time.desc())
        .offset(offset)
        .limit(limit)
    ).all()


def get_booking_by_id(session: Session, booking_id: int, stylist_id: Optional[int] = None) -> Optional[Booking]:
    """Get a specific booking by ID, optionally filtered by stylist"""
    query = select(Booking).where(Booking.id == booking_id)
    
    if stylist_id is not None:
        query = query.where(Booking.stylist_id == stylist_id)
    
    return session.exec(query).first()


def update_booking(session: Session, booking_id: int, booking_data: BookingUpdate, stylist_id: Optional[int] = None) -> Optional[Booking]:
    """Update an existing booking"""
    # Get the booking first
    booking = get_booking_by_id(session, booking_id, stylist_id)
    if not booking:
        return None
    
    # Update only provided fields
    update_data = booking_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if hasattr(booking, field):
            setattr(booking, field, value)
    
    # Update the timestamp
    booking.updated_at = datetime.now()
    
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking


def delete_booking(session: Session, booking_id: int, stylist_id: Optional[int] = None) -> bool:
    """Delete a booking"""
    booking = get_booking_by_id(session, booking_id, stylist_id)
    if not booking:
        return False
    
    session.delete(booking)
    session.commit()
    return True


def get_booking_with_stylist_info(session: Session, booking_id: int) -> Optional[tuple[Booking, Stylist, User]]:
    """Get booking with associated stylist and user information"""
    result = session.exec(
        select(Booking, Stylist, User)
        .join(Stylist, Booking.stylist_id == Stylist.id)
        .join(User, Stylist.user_id == User.id)
        .where(Booking.id == booking_id)
    ).first()
    return result


def count_bookings_by_stylist(session: Session, stylist_id: int) -> int:
    """Count total bookings for a stylist"""
    return session.exec(
        select(Booking)
        .where(Booking.stylist_id == stylist_id)
    ).count() or 0


def get_upcoming_bookings_by_stylist(session: Session, stylist_id: int, limit: int = 10) -> List[Booking]:
    """Get upcoming bookings for a stylist (today and future)"""
    from datetime import date
    today = date.today()
    
    return session.exec(
        select(Booking)
        .where(Booking.stylist_id == stylist_id)
        .where(Booking.appointment_date >= today)
        .where(Booking.status.in_([BookingStatus.pending, BookingStatus.confirmed]))
        .order_by(Booking.appointment_date.asc(), Booking.appointment_time.asc())
        .limit(limit)
    ).all()
