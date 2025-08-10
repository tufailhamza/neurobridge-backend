from pydantic import BaseModel, EmailStr
from typing import Optional
from .models.user import UserRole
from datetime import datetime

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class UserResponse(BaseModel):
    user_id: int
    email: str
    name: Optional[str] = None
    role: UserRole
    
    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse

# Signup schemas
class CaregiverSignup(BaseModel):
    email: EmailStr
    password: str
    accountType: str = "caregiver"
    prefix: str
    firstName: str
    lastName: str
    caregiverRole: str
    childAge: str
    city: str
    country: str
    diagnosis: str
    state: str
    yearsOfDiagnosis: str
    zipCode: str

class ClinicianSignup(BaseModel):
    email: EmailStr
    password: str
    accountType: str = "clinician"
    prefix: str
    firstName: str
    lastName: str
    areaOfExpertise: str
    city: str
    clinicianType: str
    country: str
    licenseNumber: str
    state: str
    zipCode: str

class SignupResponse(BaseModel):
    message: str
    user_id: int

# Post schemas
class PostResponse(BaseModel):
    id: str
    image_url: str
    title: str
    user_id: int
    date: str
    read_time: str
    tags: list[str]
    price: float
    html_content: str
    allow_comments: bool
    tier: str
    collection: str
    attachments: Optional[list[str]] = None
    date_published: datetime
    
    class Config:
        from_attributes = True

# Clinician schemas
class ClinicianResponse(BaseModel):
    user_id: int
    specialty: str
    profile_image: Optional[str] = None
    is_subscribed: bool
    prefix: Optional[str] = None
    first_name: str
    last_name: str
    country: str
    city: str
    state: str
    zip_code: str
    clinician_type: str
    license_number: str
    area_of_expertise: str
    
    class Config:
        from_attributes = True

# Subscription schemas
class SubscriptionRequest(BaseModel):
    caregiver_id: int
    clinician_id: int

class SubscriptionResponse(BaseModel):
    caregiver_id: int
    subscribed_clinician_id: int
    message: str
