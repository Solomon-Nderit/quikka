from __future__ import annotations

import enum
from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from typing import Optional, List
from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel


class UserRole(str, enum.Enum):
    stylist = "stylist"
    admin = "admin"
    # Easy to add: customer = "customer", freelancer = "freelancer", etc.


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
