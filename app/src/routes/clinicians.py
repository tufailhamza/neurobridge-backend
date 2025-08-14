from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..models.base import get_db
from ..models.clinician import Clinician
from ..models.user import User
from ..models.caregivers import Caregiver
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
        
        # Check if caregiver exists in caregivers table
        caregiver = db.query(Caregiver).filter(Caregiver.user_id == request.caregiver_id).first()
        if not caregiver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Caregiver not found"
            )
        
        # Add clinician to subscribed list if not already subscribed
        clinician_id_str = str(request.clinician_id)
        
        # Get current subscribed IDs, handle None case
        current_subscribed = caregiver.subscribed_clinicians_ids or []
        print(f"Current subscribed_clinicians_ids: {current_subscribed}")
        
        if clinician_id_str not in current_subscribed:
            # Use direct SQL to append to the array - this will definitely work
            from sqlalchemy import text
            
            # PostgreSQL array_append function to add the new clinician ID
            db.execute(
                text("""
                    UPDATE ariadne.caregivers 
                    SET subscribed_clinicians_ids = array_append(subscribed_clinicians_ids, :clinician_id) 
                    WHERE user_id = :caregiver_id
                """),
                {"clinician_id": clinician_id_str, "caregiver_id": request.caregiver_id}
            )
            
            # Refresh the caregiver object to get updated data
            db.refresh(caregiver)
            print(f"Updated subscribed_clinicians_ids: {caregiver.subscribed_clinicians_ids}")
            
            db.commit()
        else:
            return SubscriptionResponse(
                caregiver_id=request.caregiver_id,
                subscribed_clinician_id=request.clinician_id,
                message="Already subscribed to this clinician"
            )
        
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

@router.get("/subscribed/{client_id}", response_model=List[ClinicianResponse])
async def get_clinicians_subscribed_by_client(
    client_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all clinicians that a specific client (caregiver) is subscribed to
    """
    print(f"client_id: {client_id}")
    try:
        # Get the caregiver from caregivers table
        caregiver = db.query(Caregiver).filter(Caregiver.user_id == client_id).first()
        if not caregiver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Caregiver not found"
            )
        
        # If caregiver is not subscribed to any clinicians, return empty list
        if not caregiver.subscribed_clinicians_ids or len(caregiver.subscribed_clinicians_ids) == 0:
            return []
        
        # Get all clinicians that the caregiver is subscribed to
        clinicians = db.query(Clinician).filter(
            Clinician.user_id.in_(caregiver.subscribed_clinicians_ids)
        ).all()
        
        return clinicians
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching subscribed clinicians: {str(e)}"
        )

@router.get("/unsubscribed/{caregiver_id}", response_model=List[ClinicianResponse])
async def get_unsubscribed_clinicians(
    caregiver_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all clinicians that a specific caregiver is NOT subscribed to
    """
    try:
        # Get the caregiver from caregivers table
        caregiver = db.query(Caregiver).filter(Caregiver.user_id == caregiver_id).first()
        if not caregiver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Caregiver not found"
            )
        
        # Get all clinicians
        all_clinicians = db.query(Clinician).all()
        
        # If caregiver is not subscribed to any clinicians, return all clinicians
        if not caregiver.subscribed_clinicians_ids or len(caregiver.subscribed_clinicians_ids) == 0:
            return all_clinicians
        
        # Get clinicians that the caregiver is NOT subscribed to
        # Convert subscribed_clinicians_ids to integers for comparison
        subscribed_ids = [int(cid) for cid in caregiver.subscribed_clinicians_ids if cid]
        
        unsubscribed_clinicians = db.query(Clinician).filter(
            ~Clinician.user_id.in_(subscribed_ids)
        ).all()
        
        return unsubscribed_clinicians
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching unsubscribed clinicians: {str(e)}"
        )