from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from .models.user import User
from .models.caregivers import Caregiver
from .models.clinician import Clinician
from .models.base import get_db
from .config import *

# Password hashing
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password, hashed_password):
    """Verify a password against its hash."""
    try:
        print(f'aaaaaaaaaaaaaaaaaaaaa {get_password_hash(plain_password)}')
        return pwd_context.verify(plain_password, hashed_password)
    except:
        # If hash is invalid, just compare plain text for now
        return plain_password == hashed_password

def get_password_hash(password):
    """Hash a password."""
    return pwd_context.hash(password)

def create_access_token(data, expires_delta):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token):
    """Verify and decode a JWT token."""
    try:
        print(f"🔍 Verifying token: {token[:20]}...")
        print(f"🔑 Using JWT_SECRET_KEY: {JWT_SECRET_KEY[:10]}...")
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        print(f"✅ Token verified successfully. Payload: {payload}")
        return payload
    except JWTError as e:
        print(f"❌ JWT verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def authenticate_user(db, email, password):
    """Authenticate a user with email and password."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user

def check_email_exists(db, email):
    """Check if an email already exists in the database."""
    return db.query(User).filter(User.email == email).first() is not None

def create_user(db, user_data, role):
    """Create a new user in the database."""
    # Check if user already exists
    if check_email_exists(db, user_data.email):
        return None, "An account with this email already exists"
    
    # Hash the password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user object
    user = User(
        email=user_data.email,
        password=hashed_password,
        role=role
    )
    
    # Add user to database
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # If this is a caregiver, also create caregiver record
    if role == "caregiver":
        try:
            # Create caregiver object with all the required fields
            caregiver = Caregiver(
                user_id=user.user_id,
                first_name=user_data.firstName,
                last_name=user_data.lastName,
                username=user_data.firstName.lower() + user_data.lastName.lower(),  # Generate username
                country=user_data.country,
                city=user_data.city,
                state=user_data.state,
                zip_code=user_data.zipCode,
                caregiver_role=user_data.caregiverRole,
                childs_age=int(user_data.childAge) if user_data.childAge.isdigit() else 0,
                diagnosis=user_data.diagnosis,
                years_of_diagnosis=int(user_data.yearsOfDiagnosis) if user_data.yearsOfDiagnosis.isdigit() else 0,
                make_name_public=False,  # Default value
                make_personal_details_public=False,  # Default value
                profile_image=None,  # Default value
                cover_image=None,  # Default value
                content_preferences_tags=[],  # Default empty array
                bio="",  # Default empty bio
                subscribed_clinicians_ids=[],  # Default empty array
                purchased_feed_content_ids=[]  # Default empty array
            )
            
            # Add caregiver to database
            db.add(caregiver)
            db.commit()
            
        except Exception as e:
            # If caregiver creation fails, rollback user creation
            db.rollback()
            return None, f"Failed to create caregiver profile: {str(e)}"
    
    # If this is a clinician, also create clinician record
    elif role == "clinician":
        try:
            # Create clinician object with all the required fields
            clinician = Clinician(
                user_id=user.user_id,
                specialty=user_data.areaOfExpertise,  # Map areaOfExpertise to specialty
                profile_image=None,  # Default value
                is_subscribed=False,  # Default value
                prefix=user_data.prefix,
                first_name=user_data.firstName,
                last_name=user_data.lastName,
                country=user_data.country,
                city=user_data.city,
                state=user_data.state,
                zip_code=user_data.zipCode,
                clinician_type=user_data.clinicianType,
                license_number=user_data.licenseNumber,
                area_of_expertise=user_data.areaOfExpertise,
                content_preferences_tags=[]  # Default empty array
            )
            
            # Add clinician to database
            db.add(clinician)
            db.commit()
            
        except Exception as e:
            # If clinician creation fails, rollback user creation
            db.rollback()
            return None, f"Failed to create clinician profile: {str(e)}"
    
    return user, None

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token."""
    print(f"🔐 Getting current user...")
    token = credentials.credentials
    print(f"📝 Token received: {token[:20]}...")
    
    payload = verify_token(token)
    user_id: int = payload.get("sub")
    print(f"👤 User ID from token: {user_id}")
    
    if user_id is None:
        print("❌ No user ID found in token payload")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        print(f"❌ User with ID {user_id} not found in database")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print(f"✅ User authenticated: {user.email} (ID: {user.user_id})")
    return user
