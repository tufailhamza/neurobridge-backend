from pydantic import BaseModel, EmailStr
from typing import Optional
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
    role: str
    name: str
    
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

class EmailCheckResponse(BaseModel):
    email: str
    exists: bool
    message: str

# Post Purchase schemas
class PostPurchaseResponse(BaseModel):
    id: int
    user_id: int
    post_id: str
    amount: int
    currency: str
    purchased_at: datetime
    
    class Config:
        from_attributes = True

class UserPostPurchaseResponse(BaseModel):
    user_id: int
    user_email: str
    user_name: str
    post_id: str
    post_title: str
    amount: int
    currency: str
    purchased_at: datetime
    
    class Config:
        from_attributes = True

class PostPurchaseStatsResponse(BaseModel):
    post_id: str
    post_title: str
    total_purchases: int
    total_revenue: int
    currency: str
    
    class Config:
        from_attributes = True

# Post schemas
class PostCreate(BaseModel):
    image_url: str
    title: str
    tags: list[str]
    price: Optional[float] = None
    html_content: str
    allow_comments: Optional[bool] = True
    tier: str
    collection: Optional[str] = None
    attachments: Optional[list[str]] = None
    date_published: Optional[datetime] = None
    scheduled_time: Optional[datetime] = None
    # Note: stripe_price_id and stripe_product_id are generated automatically
    # and should not be provided in the request

class PostResponse(BaseModel):
    id: str
    image_url: str
    title: str
    user_id: int
    date: str
    read_time: str
    tags: list[str]
    price: Optional[float] = None
    html_content: str
    allow_comments: bool
    tier: str
    collection: Optional[str] = None
    attachments: Optional[list[str]] = None
    date_published: Optional[datetime] = None
    user_name: Optional[str] = None
    updated_at: Optional[datetime] = None
    stripe_price_id: Optional[str] = None
    stripe_product_id: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    
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
    content_preferences_tags: Optional[list[str]] = None
    
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

# Stripe schemas
class StripeCustomerRequest(BaseModel):
    user_id: int
    email: str

class StripeCustomerResponse(BaseModel):
    user_id: int
    stripe_customer_id: str
    email: str

class StripeCheckoutRequest(BaseModel):
    priceId: str
    successUrl: str
    cancelUrl: str
    metadata: dict

class StripeCheckoutResponse(BaseModel):
    sessionId: str

class StripeVerifyRequest(BaseModel):
    sessionId: str

class StripeVerifyResponse(BaseModel):
    success: bool
    paymentStatus: str
    amount: int
    currency: str

class PurchaseResponse(BaseModel):
    id: int
    user_id: str
    content_id: str
    stripe_session_id: Optional[str] = None
    stripe_payment_intent_id: Optional[str] = None
    amount: int
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Collection schemas
class CollectionResponse(BaseModel):
    collection_id: int
    user_id: int
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class CollectionCreate(BaseModel):
    name: str
