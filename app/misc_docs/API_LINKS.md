# API Links

This document maps UI buttons and flows to the expected backend API endpoints. It covers authentication, dashboard functionality, and booking management.

You can change paths or the base URL to match your backend, but keeping the shapes consistent will simplify integration.

- Base API URL (production): https://api.quikka.com
- Base API URL (local dev): http://localhost:8000
- API version (suggested): v1

---

## Authentication

### 1) Sign up (form submit)
- Trigger: `sign_up.html` → "Sign up" button
- Method: POST
- URL: `/api/signup` (current: no versioning)
- Request (JSON):
  ```json
  {
    "role": "stylist|admin",
    "name": "Full Name",
    "email": "user@example.com",
    "password": "string (>= 6 chars)",
    "phone": "optional",
    // For stylists:
    "business_name": "Business Name",
    "bio": "Professional bio (>= 10 chars)",
    "profile_image_url": "optional"
  }
  ```
- Success: 201 Created
- Response (JSON):
  ```json
  {
    "message": "Account created successfully",
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "role": "stylist|admin",
      "stylist_id": "uuid (if stylist)",
      "business_name": "string (if stylist)"
    }
  }
  ```

### 2) Log in (form submit)
- Trigger: `sign_up.html` → toggle to Log in → "Log in" button
- Method: POST
- URL: `/api/login`
- Request (JSON):
  ```json
  {
    "email": "user@example.com",
    "password": "string"
  }
  ```
- Success: 200 OK
- Response (JSON):
  ```json
  {
    "message": "Login successful",
    "access_token": "jwt",
    "token_type": "bearer",
    "user": {
      "id": "uuid",
      "name": "Full Name",
      "email": "user@example.com",
      "phone": "optional",
      "role": "stylist|admin",
      "created_at": "2024-01-01T00:00:00.000000",
      "stylist_profile": {
        "id": "uuid",
        "business_name": "Business Name",
        "bio": "Professional bio",
        "profile_image_url": "optional"
      }
    }
  }
  ```

### 3) Log out
- Trigger: Dashboard sidebar → "Logout" button
- Method: POST
- URL: `/api/logout`
- Headers: `Authorization: Bearer <accessToken>`
- Success: 200 OK
- Response (JSON):
  ```json
  {
    "message": "Successfully logged out <user_name>",
    "instruction": "Please remove the token from your client storage"
  }
  ```

---

## Dashboard APIs

### 4) Get User Profile
- Trigger: Dashboard page load → load user info for sidebar
- Method: GET
- URL: `/api/profile`
- Headers: `Authorization: Bearer <accessToken>`
- Success: 200 OK
- Response (JSON):
  ```json
  {
    "user": {
      "id": "uuid",
      "name": "Full Name",
      "email": "user@example.com",
      "phone": "optional",
      "role": "stylist|admin",
      "created_at": "2024-01-01T00:00:00.000000",
      "stylist_profile": {
        "id": "uuid",
        "business_name": "Business Name",
        "bio": "Professional bio",
        "profile_image_url": "optional"
      }
    }
  }
  ```

### 5) Get Dashboard Data (Legacy - still used)
- Trigger: Dashboard page load (general dashboard info)
- Method: GET
- URL: `/api/dashboard`
- Headers: `Authorization: Bearer <accessToken>`
- Success: 200 OK
- Response (JSON):
  ```json
  {
    "message": "Welcome to your dashboard, <user_name>!",
    "user": {
      "id": "uuid",
      "name": "Full Name",
      "email": "user@example.com",
      "phone": "optional",
      "role": "stylist|admin",
      "created_at": "2024-01-01T00:00:00.000000"
    },
    "dashboard_features": [
      "Manage appointments",
      "Update business profile",
      "View customer reviews",
      "Analytics dashboard"
    ],
    "business_info": {
      "business_name": "Business Name",
      "bio": "Professional bio"
    }
  }
  ```

---

## Booking Management APIs

### 6) Get Bookings
- Trigger: Dashboard bookings section load → populate bookings table
- Method: GET
- URL: `/api/bookings`
- Headers: `Authorization: Bearer <accessToken>`
- Query Parameters:
  - `status`: `upcoming|completed|cancelled|all` (default: upcoming)
  - `limit`: number (default: 50)
  - `offset`: number (default: 0)
  - `date_from`: ISO date (optional)
  - `date_to`: ISO date (optional)
- Success: 200 OK
- Response (JSON):
  ```json
  {
    "bookings": [
      {
        "id": "uuid",
        "client_name": "Client Name",
        "client_email": "client@example.com",
        "client_phone": "optional",
        "service_id": "uuid",
        "service_name": "Haircut",
        "appointment_date": "2024-07-22",
        "appointment_time": "10:00 AM",
        "duration_minutes": 60,
        "price": 50.00,
        "status": "confirmed|pending|completed|cancelled",
        "notes": "optional client notes",
        "created_at": "2024-01-01T00:00:00.000000",
        "updated_at": "2024-01-01T00:00:00.000000"
      }
    ],
    "total": 123,
    "has_more": true
  }
  ```

### 7) Create Booking
- Trigger: Dashboard → "Add Booking" button (future feature)
- Method: POST
- URL: `/api/bookings`
- Headers: `Authorization: Bearer <accessToken>`
- Request (JSON):
  ```json
  {
    "client_name": "Client Name",
    "client_email": "client@example.com",
    "client_phone": "optional",
    "service_id": "uuid",
    "appointment_date": "2024-07-22",
    "appointment_time": "10:00",
    "notes": "optional"
  }
  ```
- Success: 201 Created
- Response (JSON):
  ```json
  {
    "message": "Booking created successfully",
    "booking": { /* full booking object */ }
  }
  ```

### 8) Update Booking
- Trigger: Dashboard → click booking row → update status/details
- Method: PUT
- URL: `/api/bookings/{booking_id}`
- Headers: `Authorization: Bearer <accessToken>`
- Request (JSON):
  ```json
  {
    "status": "confirmed|completed|cancelled",
    "appointment_date": "2024-07-22",
    "appointment_time": "10:00",
    "notes": "updated notes"
  }
  ```
- Success: 200 OK
- Response (JSON):
  ```json
  {
    "message": "Booking updated successfully",
    "booking": { /* updated booking object */ }
  }
  ```

### 9) Delete Booking
- Trigger: Dashboard → booking row → delete action
- Method: DELETE
- URL: `/api/bookings/{booking_id}`
- Headers: `Authorization: Bearer <accessToken>`
- Success: 204 No Content

---

## Service Management APIs

### 10) Get Services
- Trigger: Dashboard → Services section → load stylist's services
- Method: GET
- URL: `/api/services`
- Headers: `Authorization: Bearer <accessToken>`
- Success: 200 OK
- Response (JSON):
  ```json
  {
    "services": [
      {
        "id": "uuid",
        "name": "Haircut",
        "description": "Basic haircut service",
        "duration_minutes": 60,
        "price": 50.00,
        "is_active": true,
        "created_at": "2024-01-01T00:00:00.000000"
      }
    ]
  }
  ```

### 11) Create Service
- Trigger: Dashboard → Services → "Add Service" button
- Method: POST
- URL: `/api/services`
- Headers: `Authorization: Bearer <accessToken>`
- Request (JSON):
  ```json
  {
    "name": "Service Name",
    "description": "Service description",
    "duration_minutes": 60,
    "price": 50.00,
    "is_active": true
  }
  ```
- Success: 201 Created

---

## Calendar APIs

### 12) Get Calendar Availability
- Trigger: Dashboard → Calendar view → load availability for date range
- Method: GET
- URL: `/api/calendar/availability`
- Headers: `Authorization: Bearer <accessToken>`
- Query Parameters:
  - `date_from`: ISO date (required)
  - `date_to`: ISO date (required)
- Success: 200 OK
- Response (JSON):
  ```json
  {
    "availability": [
      {
        "date": "2024-07-22",
        "slots": [
          {
            "time": "10:00",
            "available": true,
            "booking_id": "uuid (if booked)"
          }
        ]
      }
    ]
  }
  ```

---

## Error Handling

### Common Error Responses
- **400 Bad Request**:
  ```json
  {
    "detail": "Validation error details"
  }
  ```
- **401 Unauthorized**:
  ```json
  {
    "detail": "Could not validate credentials"
  }
  ```
- **403 Forbidden**:
  ```json
  {
    "detail": "Not enough permissions"
  }
  ```
- **404 Not Found**:
  ```json
  {
    "detail": "Resource not found"
  }
  ```
- **409 Conflict**:
  ```json
  {
    "detail": "Email already registered"
  }
  ```

---

## Quick Reference by UI Component

### Authentication Pages
- Sign up form → POST `/api/signup`
- Login form → POST `/api/login`
- Logout button → POST `/api/logout`

### Dashboard Sidebar
- User profile load → GET `/api/profile`
- Navigation → Update UI only (no API calls)

### Bookings Section
- Load bookings table → GET `/api/bookings`
- Create booking → POST `/api/bookings`
- Update booking → PUT `/api/bookings/{id}`
- Delete booking → DELETE `/api/bookings/{id}`

### Calendar Component
- Load calendar availability → GET `/api/calendar/availability?date_from=X&date_to=Y`

### Services Section
- Load services → GET `/api/services`
- Create service → POST `/api/services`

---

## Implementation Priority

1. **Phase 1 (Current)**: Authentication endpoints ✅
2. **Phase 2 (Next)**: User profile, basic dashboard data ✅ 
3. **Phase 3 (Required for UI)**: Bookings CRUD, Services CRUD
4. **Phase 4 (Enhanced)**: Calendar availability, advanced booking features

---

## Security Notes
- All protected endpoints require `Authorization: Bearer <jwt_token>` header
- JWT tokens expire after 24 hours (configurable)
- Implement rate limiting on authentication endpoints
- Use HTTPS in production
- Validate all input data and sanitize outputs