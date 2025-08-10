from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..models.base import get_db
from ..models.clinician import Clinician
from ..models.user import User
from ..schemas import ClinicianResponse, SubscriptionRequest, SubscriptionResponse
from sqlalchemy.orm import joinedload

router = APIRouter(prefix="/clinicians", tags=["clinicians"])

@router.get("/clinicians", response_model=List[ClinicianResponse])
async def get_clinicians(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get all clinicians from the database
    Default: returns up to 50 clinicians
    """
    try:
        # Query clinicians table directly
        clinicians = db.query(Clinician).limit(limit).all()
        
        if not clinicians:
            return []
        
        return clinicians
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching clinicians: {str(e)}"
        )
    

@router.post("/subscribe", response_model=SubscriptionResponse)
async def subscribe_to_clinician(
    request: SubscriptionRequest,
    db: Session = Depends(get_db)
):
    """
    Subscribe a caregiver to a clinician
    """
    try:
        # Check if clinician exists
        clinician = db.query(Clinician).filter(Clinician.user_id == request.clinician_id).first()
        if not clinician:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Clinician not found"
            )
        
        # Check if caregiver exists
        caregiver = db.query(User).filter(User.user_id == request.caregiver_id).first()
        if not caregiver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Caregiver not found"
            )
        
        # Update caregiver's subscribed_clinician_id
        caregiver.subscribed_clinician_id = request.clinician_id
        db.commit()
        
        return SubscriptionResponse(
            caregiver_id=request.caregiver_id,
            subscribed_clinician_id=request.clinician_id,
            message="Successfully subscribed to clinician"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error subscribing to clinician: {str(e)}"
        )
    
