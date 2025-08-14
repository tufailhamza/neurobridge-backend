from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from ..models.base import get_db
from ..models.user import User
from ..models.caregivers import Caregiver
from ..models.clinician import Clinician
from ..schemas import UserLogin, LoginResponse, CaregiverSignup, ClinicianSignup, SignupResponse
from ..auth import authenticate_user, create_access_token, create_user
from ..config import *

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/signup/caregiver", response_model=SignupResponse)
async def signup_caregiver(user_data: CaregiverSignup, db: Session = Depends(get_db)):
    """
    Create a new caregiver account
    """
    user, error = create_user(db, user_data, "caregiver")
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return SignupResponse(
        message="Caregiver account created successfully",
        user_id=user.user_id
    )

@router.post("/signup/clinician", response_model=SignupResponse)
async def signup_clinician(user_data: ClinicianSignup, db: Session = Depends(get_db)):
    """
    Create a new clinician account
    """
    user, error = create_user(db, user_data, "clinician")
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return SignupResponse(
        message="Clinician account created successfully",
        user_id=user.user_id
    )

@router.post("/login", response_model=LoginResponse)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token
    """
    # Authenticate user
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get username from the appropriate profile table based on role
    username = ""
    if user.role == "caregiver":
        caregiver = db.query(Caregiver).filter(Caregiver.user_id == user.user_id).first()
        if caregiver:
            username = caregiver.username
    elif user.role == "clinician":
        clinician = db.query(Clinician).filter(Clinician.user_id == user.user_id).first()
        if clinician:
            # For clinicians, we can use first_name + last_name as username or create a username field
            username = f"{clinician.first_name}_{clinician.last_name}".lower()
    
    # Create access token
    access_token_expires = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.user_id)}, expires_delta=access_token_expires
    )
    
    # Create UserResponse with username
    from ..schemas import UserResponse
    user_response = UserResponse(
        user_id=user.user_id,
        email=user.email,
        role=user.role,
        name=username
    )
    
    # Return token and user info
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        user=user_response
    )
