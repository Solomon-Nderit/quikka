from typing import Optional, List
from datetime import datetime, time, date, timedelta

from sqlmodel import Session, select

from models import Stylist, User, UserCreate, StylistSignup, UserRole, Booking, BookingStatus, StylistAvailability, DayOfWeek, ProfessionalSettings, BookingStatusHistory
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
    
    # Create default professional settings
    create_default_professional_settings(session, stylist.id, "stylist")
    
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


# Availability CRUD operations
def create_default_availability(session: Session, stylist_id: int) -> List[StylistAvailability]:
    """
    Create default availability for a stylist (Mon-Sat 8AM-5PM)
    """
    from datetime import time
    
    default_schedules = []
    
    # Monday to Saturday (0-5), 8 AM to 5 PM
    for day in range(6):  # 0 = Monday, 5 = Saturday
        availability = StylistAvailability(
            stylist_id=stylist_id,
            day_of_week=DayOfWeek(day),
            start_time=time(8, 0),  # 8:00 AM
            end_time=time(17, 0),   # 5:00 PM
            is_active=True
        )
        session.add(availability)
        default_schedules.append(availability)
    
    session.commit()
    
    # Refresh all objects
    for schedule in default_schedules:
        session.refresh(schedule)
    
    return default_schedules


def get_stylist_availability(session: Session, stylist_id: int) -> List[StylistAvailability]:
    """Get all availability schedules for a stylist"""
    return session.exec(
        select(StylistAvailability)
        .where(StylistAvailability.stylist_id == stylist_id)
        .where(StylistAvailability.is_active == True)
        .order_by(StylistAvailability.day_of_week.asc())
    ).all()


def update_stylist_availability(session: Session, stylist_id: int, day_of_week: DayOfWeek, start_time: time, end_time: time) -> Optional[StylistAvailability]:
    """Update availability for a specific day"""
    from datetime import datetime
    
    # Find existing availability for this day
    availability = session.exec(
        select(StylistAvailability)
        .where(StylistAvailability.stylist_id == stylist_id)
        .where(StylistAvailability.day_of_week == day_of_week)
    ).first()
    
    if availability:
        # Update existing
        availability.start_time = start_time
        availability.end_time = end_time
        availability.is_active = True
        availability.updated_at = datetime.now()
    else:
        # Create new
        availability = StylistAvailability(
            stylist_id=stylist_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            is_active=True
        )
        session.add(availability)
    
    session.commit()
    session.refresh(availability)
    return availability


def disable_stylist_availability(session: Session, stylist_id: int, day_of_week: DayOfWeek) -> bool:
    """Disable availability for a specific day (make stylist unavailable)"""
    from datetime import datetime
    
    availability = session.exec(
        select(StylistAvailability)
        .where(StylistAvailability.stylist_id == stylist_id)
        .where(StylistAvailability.day_of_week == day_of_week)
    ).first()
    
    if availability:
        availability.is_active = False
        availability.updated_at = datetime.now()
        session.commit()
        return True
    
    return False


# Time conflict validation functions
def check_booking_conflicts(session: Session, stylist_id: int, appointment_date: date, appointment_time: time, duration_minutes: int, exclude_booking_id: Optional[int] = None) -> List[Booking]:
    """
    Check for booking conflicts with the proposed appointment time
    
    Returns a list of conflicting bookings (empty list if no conflicts)
    """
    from datetime import timedelta, datetime as dt
    
    # Calculate end time of proposed appointment
    proposed_start = dt.combine(appointment_date, appointment_time)
    proposed_end = proposed_start + timedelta(minutes=duration_minutes)
    
    # Get all bookings for this stylist on this date (only active bookings that block time slots)
    # Excluded: cancelled, no_show (these free up the time slot)
    # Included: pending, confirmed, reschedule_requested, completed (these occupy the time slot)
    existing_bookings = session.exec(
        select(Booking)
        .where(Booking.stylist_id == stylist_id)
        .where(Booking.appointment_date == appointment_date)
        .where(Booking.status.in_([BookingStatus.pending, BookingStatus.confirmed, BookingStatus.reschedule_requested, BookingStatus.completed]))
    ).all()
    
    conflicts = []
    
    for booking in existing_bookings:
        # Skip if this is the booking we're updating
        if exclude_booking_id and booking.id == exclude_booking_id:
            continue
            
        # Calculate existing booking time range
        existing_start = dt.combine(booking.appointment_date, booking.appointment_time)
        existing_end = existing_start + timedelta(minutes=booking.duration_minutes)
        
        # Check for overlap
        if (proposed_start < existing_end) and (proposed_end > existing_start):
            conflicts.append(booking)
    
    return conflicts


def is_time_slot_available(session: Session, stylist_id: int, appointment_date: date, appointment_time: time, duration_minutes: int, exclude_booking_id: Optional[int] = None) -> tuple[bool, str]:
    """
    Check if a time slot is available for booking
    
    Returns:
        tuple[bool, str]: (is_available, reason_if_not_available)
    """
    from datetime import datetime as dt, timedelta
    
    # Check if stylist exists
    stylist = get_stylist_by_id(session, stylist_id)
    if not stylist:
        return False, "Stylist not found"
    
    # Get day of week (0=Monday, 6=Sunday)
    day_of_week = appointment_date.weekday()
    
    # Convert weekday integer to DayOfWeek enum
    day_enum = DayOfWeek(day_of_week)
    
    # Check if stylist is available on this day
    availability = session.exec(
        select(StylistAvailability)
        .where(StylistAvailability.stylist_id == stylist_id)
        .where(StylistAvailability.day_of_week == day_enum)
        .where(StylistAvailability.is_active == True)
    ).first()
    
    if not availability:
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        return False, f"Stylist is not available on {day_names[day_of_week]}"
    
    # Check if appointment time is within available hours
    proposed_start = appointment_time
    proposed_end_dt = dt.combine(appointment_date, appointment_time) + timedelta(minutes=duration_minutes)
    proposed_end = proposed_end_dt.time()
    
    if proposed_start < availability.start_time:
        return False, f"Appointment starts before available hours ({availability.start_time.strftime('%H:%M')})"
    
    if proposed_end > availability.end_time:
        return False, f"Appointment ends after available hours ({availability.end_time.strftime('%H:%M')})"
    
    # Check for booking conflicts
    conflicts = check_booking_conflicts(session, stylist_id, appointment_date, appointment_time, duration_minutes, exclude_booking_id)
    
    if conflicts:
        conflict_times = []
        for conflict in conflicts:
            start_time = conflict.appointment_time.strftime('%H:%M')
            end_dt = dt.combine(conflict.appointment_date, conflict.appointment_time) + timedelta(minutes=conflict.duration_minutes)
            end_time = end_dt.time().strftime('%H:%M')
            conflict_times.append(f"{start_time}-{end_time}")
        
        return False, f"Time slot conflicts with existing bookings: {', '.join(conflict_times)}"
    
    return True, "Time slot is available"


def get_available_time_slots(session: Session, stylist_id: int, appointment_date: date, duration_minutes: int = 60, slot_interval_minutes: int = 30) -> List[dict]:
    """
    Get list of available time slots for a stylist on a specific date
    
    Args:
        stylist_id: ID of the stylist
        appointment_date: Date to check availability
        duration_minutes: Duration of the appointment
        slot_interval_minutes: Interval between time slots (e.g., 30 min intervals)
    
    Returns:
        List of available time slots with start_time and end_time
    """
    from datetime import datetime as dt, timedelta
    
    # Get stylist availability for this day
    day_of_week = appointment_date.weekday()
    
    # Convert weekday integer to DayOfWeek enum
    day_enum = DayOfWeek(day_of_week)
    
    availability = session.exec(
        select(StylistAvailability)
        .where(StylistAvailability.stylist_id == stylist_id)
        .where(StylistAvailability.day_of_week == day_enum)
        .where(StylistAvailability.is_active == True)
    ).first()
    
    if not availability:
        return []
    
    available_slots = []
    
    # Generate time slots from start to end time
    current_time = dt.combine(appointment_date, availability.start_time)
    end_of_day = dt.combine(appointment_date, availability.end_time)
    
    while current_time + timedelta(minutes=duration_minutes) <= end_of_day:
        # Check if this slot is available
        slot_time = current_time.time()
        is_available, _ = is_time_slot_available(session, stylist_id, appointment_date, slot_time, duration_minutes)
        
        if is_available:
            slot_end = current_time + timedelta(minutes=duration_minutes)
            available_slots.append({
                "start_time": slot_time.strftime('%H:%M'),
                "end_time": slot_end.time().strftime('%H:%M'),
                "duration_minutes": duration_minutes
            })
        
        # Move to next slot interval
        current_time += timedelta(minutes=slot_interval_minutes)
    
    return available_slots


# Professional Settings CRUD operations
def create_default_professional_settings(session: Session, stylist_id: int, professional_type: str = "stylist") -> ProfessionalSettings:
    """Create default professional settings for a new professional"""
    settings = ProfessionalSettings(
        stylist_id=stylist_id if professional_type == "stylist" else None,
        professional_type=professional_type,
        cancellation_deadline_hours=24,
        max_reschedules_allowed=2,
        no_show_grace_period_minutes=60,
        auto_confirm_bookings=False,
        require_prepayment=False
    )
    session.add(settings)
    session.commit()
    session.refresh(settings)
    return settings


def get_professional_settings(session: Session, stylist_id: int, professional_type: str = "stylist") -> Optional[ProfessionalSettings]:
    """Get professional settings for a stylist/professional"""
    return session.exec(
        select(ProfessionalSettings)
        .where(ProfessionalSettings.stylist_id == stylist_id)
        .where(ProfessionalSettings.professional_type == professional_type)
    ).first()


def update_professional_settings(session: Session, stylist_id: int, settings_data: dict, professional_type: str = "stylist") -> Optional[ProfessionalSettings]:
    """Update professional settings"""
    settings = get_professional_settings(session, stylist_id, professional_type)
    
    if not settings:
        # Create default settings if they don't exist
        settings = create_default_professional_settings(session, stylist_id, professional_type)
    
    # Update fields
    for field, value in settings_data.items():
        if hasattr(settings, field):
            setattr(settings, field, value)
    
    settings.updated_at = datetime.now()
    session.add(settings)
    session.commit()
    session.refresh(settings)
    return settings


# Booking Status Management
def update_booking_status_with_history(session: Session, booking_id: int, new_status: BookingStatus, changed_by_user_id: int, reason: Optional[str] = None, stylist_id: Optional[int] = None) -> Optional[Booking]:
    """Update booking status and record the change in history"""
    
    # Get the booking
    booking = get_booking_by_id(session, booking_id, stylist_id)
    if not booking:
        return None
    
    old_status = booking.status
    
    # Update booking status
    booking.status = new_status
    booking.updated_at = datetime.now()
    
    # Add special handling for reschedule status
    if new_status == BookingStatus.reschedule_requested:
        booking.reschedule_requested_at = datetime.now()
    
    session.add(booking)
    
    # Record status change in history
    history = BookingStatusHistory(
        booking_id=booking_id,
        old_status=old_status,
        new_status=new_status,
        changed_by_user_id=changed_by_user_id,
        change_reason=reason
    )
    session.add(history)
    
    session.commit()
    session.refresh(booking)
    session.refresh(booking)
    return booking


def reschedule_booking(session: Session, booking_id: int, new_date: date, new_time: time, reschedule_reason: str, stylist_id: Optional[int] = None) -> Optional[Booking]:
    """Reschedule a booking to a new date/time"""
    
    booking = get_booking_by_id(session, booking_id, stylist_id)
    if not booking:
        return None
    
    # Get professional settings to check reschedule limits
    settings = get_professional_settings(session, booking.stylist_id)
    max_reschedules = settings.max_reschedules_allowed if settings else 2
    
    if booking.reschedule_count >= max_reschedules:
        raise ValueError(f"Maximum reschedules ({max_reschedules}) exceeded for this booking")
    
    # Check if new slot is available
    is_available, availability_message = is_time_slot_available(
        session, 
        booking.stylist_id, 
        new_date, 
        new_time, 
        booking.duration_minutes,
        exclude_booking_id=booking_id
    )
    
    if not is_available:
        raise ValueError(f"New time slot not available: {availability_message}")
    
    # Store original appointment if this is the first reschedule
    if booking.reschedule_count == 0:
        booking.original_appointment_date = booking.appointment_date
        booking.original_appointment_time = booking.appointment_time
    
    # Update booking with new time
    booking.appointment_date = new_date
    booking.appointment_time = new_time
    booking.reschedule_count += 1
    booking.reschedule_reason = reschedule_reason
    booking.reschedule_requested_at = datetime.now()
    booking.status = BookingStatus.confirmed  # Confirm the rescheduled booking
    booking.updated_at = datetime.now()
    
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking


def get_booking_status_history(session: Session, booking_id: int) -> List[BookingStatusHistory]:
    """Get status change history for a booking"""
    return session.exec(
        select(BookingStatusHistory)
        .where(BookingStatusHistory.booking_id == booking_id)
        .order_by(BookingStatusHistory.changed_at.asc())
    ).all()


def check_for_no_shows(session: Session) -> List[Booking]:
    """
    Check for bookings that should be marked as no-show
    This can be run as a scheduled task
    """
    from datetime import datetime as dt, timedelta
    
    current_time = dt.now()
    
    # Get all confirmed bookings that are past their appointment time
    past_bookings = session.exec(
        select(Booking)
        .where(Booking.status == BookingStatus.confirmed)
        .where(Booking.appointment_date <= current_time.date())
    ).all()
    
    no_show_bookings = []
    
    for booking in past_bookings:
        # Get professional settings for grace period
        settings = get_professional_settings(session, booking.stylist_id)
        grace_period = settings.no_show_grace_period_minutes if settings else 60
        
        # Calculate appointment datetime
        appointment_datetime = dt.combine(booking.appointment_date, booking.appointment_time)
        grace_deadline = appointment_datetime + timedelta(minutes=grace_period)
        
        # Check if grace period has passed
        if current_time > grace_deadline:
            booking.status = BookingStatus.no_show
            booking.updated_at = current_time
            session.add(booking)
            
            # Record in history
            history = BookingStatusHistory(
                booking_id=booking.id,
                old_status=BookingStatus.confirmed,
                new_status=BookingStatus.no_show,
                changed_by_user_id=1,  # System user ID (you might want to create a system user)
                change_reason="Automatic no-show detection after grace period"
            )
            session.add(history)
            
            no_show_bookings.append(booking)
    
    if no_show_bookings:
        session.commit()
    
    return no_show_bookings
