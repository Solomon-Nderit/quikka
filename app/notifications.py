"""
Email notification system for booking confirmations
Future implementation will integrate with email service providers
"""
from models import Booking, Stylist, User, BookingStatus


def send_booking_confirmation_emails(booking: Booking, stylist: Stylist, stylist_user: User) -> None:
    """
    Send confirmation emails to both client and stylist
    
    Args:
        booking: The booking object
        stylist: The stylist profile
        stylist_user: The user object for the stylist
    """
    
    # TODO: Implement actual email sending
    # This is a placeholder for future implementation
    
    print("=== EMAIL NOTIFICATIONS ===")
    print(f"📧 Sending booking confirmation to client: {booking.client_email}")
    print(f"   - Service: {booking.service_name}")
    print(f"   - Date: {booking.appointment_date} at {booking.appointment_time}")
    print(f"   - Stylist: {stylist.business_name}")
    
    print(f"📧 Sending booking notification to stylist: {stylist_user.email}")
    print(f"   - Client: {booking.client_name}")
    print(f"   - Service: {booking.service_name}")
    print(f"   - Date: {booking.appointment_date} at {booking.appointment_time}")
    
    print("✅ Emails sent successfully!")
    print("============================")


def send_booking_update_emails(booking: Booking, stylist: Stylist, stylist_user: User, update_type: str = "updated") -> None:
    """
    Send update emails when booking status changes
    
    Args:
        booking: The updated booking object
        stylist: The stylist profile
        stylist_user: The user object for the stylist
        update_type: Type of update ("updated", "cancelled", "confirmed", etc.)
    """
    
    print("=== EMAIL UPDATE NOTIFICATIONS ===")
    print(f"📧 Sending booking {update_type} notification to client: {booking.client_email}")
    print(f"📧 Sending booking {update_type} notification to stylist: {stylist_user.email}")
    print(f"✅ Update emails sent successfully!")
    print("===================================")


def send_status_update_notification(
    booking: Booking, 
    professional: Stylist,  # Generic term for future expansion
    professional_user: User,
    new_status: BookingStatus,
    professional_type: str = "stylist"  # Default, but configurable
):
    """
    Send notification for booking status changes
    
    Args:
        booking: The booking object
        professional: Professional profile (Stylist, Therapist, etc.)
        professional_user: User object for the professional
        new_status: New booking status
        professional_type: "stylist", "therapist", "trainer", "consultant", etc.
    """
    
    professional_titles = {
        "stylist": "Hair Stylist",
        "therapist": "Massage Therapist", 
        "trainer": "Personal Trainer",
        "consultant": "Business Consultant",
        "tutor": "Tutor"
    }
    
    title = professional_titles.get(professional_type, "Professional")
    
    # Status-specific messages
    status_messages = {
        BookingStatus.completed: "Your appointment has been completed",
        BookingStatus.cancelled: "Your appointment has been cancelled",
        BookingStatus.confirmed: "Your appointment has been confirmed",
        BookingStatus.reschedule_requested: "A reschedule has been requested for your appointment",
        BookingStatus.no_show: "You were marked as a no-show for your appointment"
    }
    
    client_message = status_messages.get(new_status, f"Your appointment status has been updated to {new_status}")
    
    print("📧 BOOKING STATUS UPDATE NOTIFICATION")
    print(f"   - Client: {booking.client_email}")
    print(f"   - Message: {client_message}")
    print(f"   - {title}: {professional.business_name}")
    print(f"   - Status: {new_status.upper()}")
    print(f"   - Service: {booking.service_name}")
    print(f"   - Date: {booking.appointment_date} at {booking.appointment_time}")
    
    # Also notify the professional
    print(f"📧 PROFESSIONAL NOTIFICATION")
    print(f"   - {title}: {professional_user.email}")
    print(f"   - Booking for {booking.client_name} marked as {new_status}")
    
    print("✅ Status update notifications sent!")


def send_reschedule_notification(
    booking: Booking,
    professional: Stylist,
    professional_user: User,
    old_date: str,
    old_time: str,
    professional_type: str = "stylist"
):
    """
    Send notification when a booking is rescheduled
    """
    
    professional_titles = {
        "stylist": "Hair Stylist",
        "therapist": "Massage Therapist", 
        "trainer": "Personal Trainer",
        "consultant": "Business Consultant",
        "tutor": "Tutor"
    }
    
    title = professional_titles.get(professional_type, "Professional")
    
    print("📧 BOOKING RESCHEDULE NOTIFICATION")
    print(f"   - Client: {booking.client_email}")
    print(f"   - Your appointment has been rescheduled")
    print(f"   - Old time: {old_date} at {old_time}")
    print(f"   - New time: {booking.appointment_date} at {booking.appointment_time}")
    print(f"   - {title}: {professional.business_name}")
    print(f"   - Service: {booking.service_name}")
    if booking.reschedule_reason:
        print(f"   - Reason: {booking.reschedule_reason}")
    
    print(f"📧 PROFESSIONAL NOTIFICATION")
    print(f"   - {title}: {professional_user.email}")
    print(f"   - Booking for {booking.client_name} rescheduled to {booking.appointment_date} at {booking.appointment_time}")
    
    print("✅ Reschedule notifications sent!")


def send_no_show_notification(
    booking: Booking,
    professional: Stylist,
    professional_user: User,
    professional_type: str = "stylist"
):
    """
    Send notification when a client is marked as no-show
    """
    
    professional_titles = {
        "stylist": "Hair Stylist",
        "therapist": "Massage Therapist", 
        "trainer": "Personal Trainer",
        "consultant": "Business Consultant",
        "tutor": "Tutor"
    }
    
    title = professional_titles.get(professional_type, "Professional")
    
    print("📧 NO-SHOW NOTIFICATION")
    print(f"   - Client: {booking.client_email}")
    print(f"   - You were marked as a no-show for your appointment")
    print(f"   - {title}: {professional.business_name}")
    print(f"   - Service: {booking.service_name}")
    print(f"   - Missed appointment: {booking.appointment_date} at {booking.appointment_time}")
    print(f"   - Please contact us to reschedule if this was an error")
    
    print(f"📧 PROFESSIONAL NOTIFICATION")
    print(f"   - {title}: {professional_user.email}")
    print(f"   - Client {booking.client_name} marked as no-show for {booking.appointment_date}")
    
    print("✅ No-show notifications sent!")


# Future implementation notes:
"""
To implement actual email sending, you could use:

1. SendGrid:
   - pip install sendgrid
   - Use SendGrid API key
   
2. AWS SES:
   - pip install boto3
   - Use AWS credentials
   
3. Gmail SMTP:
   - Use smtplib (built-in)
   - Requires app password
   
4. Postmark:
   - pip install postmarker
   - Use Postmark API key

Example future implementation structure:

def send_booking_confirmation_emails(booking, stylist, stylist_user):
    # Client email
    client_email_content = render_template('booking_confirmation_client.html', 
                                         booking=booking, stylist=stylist)
    send_email(to=booking.client_email, 
              subject="Booking Confirmation", 
              content=client_email_content)
    
    # Stylist email
    stylist_email_content = render_template('booking_notification_stylist.html', 
                                          booking=booking, client=booking)
    send_email(to=stylist_user.email, 
              subject="New Booking Received", 
              content=stylist_email_content)
"""