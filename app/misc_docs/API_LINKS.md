# API Links

This document maps UI buttons and flows to the expected backend API endpoints. It covers the landing page CTAs and the combined Sign up / Log in page.

You can change paths or the base URL to match your backend, but keeping the shapes consistent will simplify integration.

- Base API URL (production): https://api.quikka.com
- Base API URL (local dev): http://localhost:8000
- API version (suggested): v1

---

## Authentication

### 1) Sign up (form submit)
- Trigger: `sign_up.html` → "Sign up" button
- Method: POST
- URL: `/api/v1/auth/signup`
- Request (JSON):
  {
    "email": "user@example.com",
    "password": "string (>= 6 chars)"
  }
- Success: 201 Created
- Response (JSON):
  {
    "user": {"id": "uuid", "email": "user@example.com"},
    "accessToken": "jwt",
    "refreshToken": "jwt"
  }
- Notes: Return 409 if email already in use; 400 for validation errors.

### 2) Log in (form submit)
- Trigger: `sign_up.html` → toggle to Log in → "Log in" button
- Method: POST
- URL: `/api/v1/auth/login`
- Request (JSON):
  {
    "email": "user@example.com",
    "password": "string"
  }
- Success: 200 OK
- Response (JSON):
  {
    "user": {"id": "uuid", "email": "user@example.com"},
    "accessToken": "jwt",
    "refreshToken": "jwt"
  }
- Notes: Return 401 for invalid credentials; consider lockout/backoff.

### 3) Continue with Google (OAuth)
- Trigger: `sign_up.html` → "Continue with Google" button
- Start OAuth: GET `/api/v1/auth/google/start` → redirects to Google
- Callback: GET `/api/v1/auth/google/callback?code=...&state=...`
- Success: 302 → front-end session page; and/or 200 JSON with tokens
- JSON (on success if returning tokens):
  {
    "user": {"id": "uuid", "email": "user@example.com"},
    "accessToken": "jwt",
    "refreshToken": "jwt"
  }
- Notes: CSRF-protect with `state`; support PKCE if doing OAuth on SPA.

### 4) Log out (future)
- Trigger: navbar/profile (not in UI yet)
- Method: POST
- URL: `/api/v1/auth/logout`
- Headers: `Authorization: Bearer <accessToken>`
- Success: 204 No Content

---

## Landing CTAs

### 5) Join Waitlist
- Trigger: `landing.html` → "Join Waitlist"
- Method: POST
- URL: `/api/v1/waitlist`
- Request (JSON):
  {
    "email": "visitor@example.com",
    "source": "landing-hero"
  }
- Success: 202 Accepted
- Notes: If you prefer, this CTA can navigate to the combined auth page with `#signup` instead of calling the API. This entry is for a direct waitlist flow.

### 6) Get Started
- Trigger: `landing.html` → "Get Started"
- Action: Navigate to `/frontend/templates/sign_up.html#signup` (front-end route) or your app route `/signup`
- Notes: No API call; it’s a navigation shortcut to the Sign up form.

---

## Common error shapes (suggested)
- 400 Bad Request:
  {
    "error": {"code": "VALIDATION_ERROR", "message": "<details>", "fields": {"email": "Invalid"}}
  }
- 401 Unauthorized:
  {
    "error": {"code": "UNAUTHORIZED", "message": "Invalid credentials"}
  }
- 409 Conflict:
  {
    "error": {"code": "EMAIL_IN_USE", "message": "Email already registered"}
  }

## Security notes
- Prefer HTTP-only, Secure cookies for tokens on web.
- If returning tokens to JS, rotate refresh tokens and set short-lived access tokens.
- Add rate limiting to `/auth/login` and `/auth/signup`.
- Enforce CORS only for allowed front-end origins in production.

## Quick mapping by UI control
- Sign up button → POST `/api/v1/auth/signup`
- Log in button → POST `/api/v1/auth/login`
- Continue with Google → GET `/api/v1/auth/google/start` → callback `/api/v1/auth/google/callback`
- Join Waitlist → POST `/api/v1/waitlist`
- Get Started → navigate to auth page (no API)
