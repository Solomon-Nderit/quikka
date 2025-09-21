
from typing import Optional, Union, Literal

from pydantic import BaseModel, EmailStr, Field, validator
from models import UserRole


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
