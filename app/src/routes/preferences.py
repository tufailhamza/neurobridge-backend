# src/routes/preferences.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from ..models.base import get_db
from ..models.user import User
from ..models.caregivers import Caregiver
from ..models.clinician import Clinician
from ..auth import get_current_user

# Request body schema for content preferences
class ContentPreferencesUpdate(BaseModel):
    role: str
    content_preferences: List[str]

router = APIRouter(prefix="/preferences", tags=["preferences"])

@router.put("/content/{user_id}")
async def update_content_preferences(
    user_id: int,
    request: ContentPreferencesUpdate,
    db: Session = Depends(get_db)
):
    """
    Update content preferences for a user based on their role
    """
    try:
        # Extract values from request body
        role = request.role
        content_preferences = request.content_preferences
        
        # Validate role
        if role not in ["caregiver", "clinician"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Must be 'caregiver' or 'clinician'"
            )
        
        # Check if user exists
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify user role matches the provided role
        if user.role != role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User role ({user.role}) does not match provided role ({role})"
            )
        
        # Update content preferences based on role
        if role == "caregiver":
            # Update caregiver content preferences
            caregiver = db.query(Caregiver).filter(Caregiver.user_id == user_id).first()
            if not caregiver:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Caregiver profile not found"
                )
            
            caregiver.content_preferences_tags = content_preferences
            db.commit()
            
            return {
                "message": "Caregiver content preferences updated successfully",
                "user_id": user_id,
                "role": role,
                "content_preferences": content_preferences
            }
            
        elif role == "clinician":
            # Update clinician content preferences
            clinician = db.query(Clinician).filter(Clinician.user_id == user_id).first()
            if not clinician:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Clinician profile not found"
                )
            
            clinician.content_preferences_tags = content_preferences
            db.commit()
            
            return {
                "message": "Clinician content preferences updated successfully",
                "user_id": user_id,
                "role": role,
                "content_preferences": content_preferences
            }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating content preferences: {str(e)}"
        )

@router.get("/content/{user_id}")
async def get_content_preferences(
    user_id: int,
    role: str,
    db: Session = Depends(get_db)
):
    """
    Get content preferences for a user based on their role
    """
    try:
        # Validate role
        if role not in ["caregiver", "clinician"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Must be 'caregiver' or 'clinician'"
            )
        
        # Check if user exists
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify user role matches the provided role
        if user.role != role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User role ({user.role}) does not match provided role ({role})"
            )
        
        # Get content preferences based on role
        if role == "caregiver":
            caregiver = db.query(Caregiver).filter(Caregiver.user_id == user_id).first()
            if not caregiver:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Caregiver profile not found"
                )
            
            return {
                "user_id": user_id,
                "role": role,
                "content_preferences": caregiver.content_preferences_tags or []
            }
            
        elif role == "clinician":
            clinician = db.query(Clinician).filter(Clinician.user_id == user_id).first()
            if not clinician:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Clinician profile not found"
                )
            
            return {
                "user_id": user_id,
                "role": role,
                "content_preferences": clinician.content_preferences_tags or []
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching content preferences: {str(e)}"
        )
