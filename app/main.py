from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr


#Models
class SignUp(BaseModel):
    email: EmailStr
    password: str


#App instance
app = FastAPI()

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
    return {"message": "Backend is running"}

@app.post("/signup")
def sign_up(payload: SignUp):
    # Stub implementation for local testing
    return {
        "message": "User signed up successfully",
        "user": {"email": payload.email}
    }