# src/routes/caregivers.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from ..models.base import get_db
from ..models.caregivers import Caregiver

router = APIRouter(prefix="/caregivers", tags=["caregivers"])

# Response schema for caregiver list
class CaregiverBasicInfo(BaseModel):
    user_id: int
    username: str
    
    class Config:
        from_attributes = True

@router.get("/caregivers", response_model=List[CaregiverBasicInfo])
async def get_all_caregivers(
    db: Session = Depends(get_db)
):
    """
    Get all caregivers with their user_id and username
    """
    try:
        # Query all caregivers from the caregivers table
        caregivers = db.query(Caregiver).all()
        
        if not caregivers:
            return []
        
        return caregivers
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching caregivers: {str(e)}"
        )

@router.get("/{user_id}", response_model=CaregiverBasicInfo)
async def get_caregiver_by_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific caregiver by user_id
    """
    try:
        caregiver = db.query(Caregiver).filter(Caregiver.user_id == user_id).first()
        
        if not caregiver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Caregiver not found"
            )
        
        return caregiver
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching caregiver: {str(e)}"
        )
