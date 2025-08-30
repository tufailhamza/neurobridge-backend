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
async def get_all_clinicians(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get all clinicians from the database (similar to caregivers endpoint)
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

@router.get("/clinicians/{user_id}", response_model=ClinicianResponse)
async def get_clinician_by_user_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific clinician by user_id
    """
    try:
        clinician = db.query(Clinician).filter(Clinician.user_id == user_id).first()
        
        if not clinician:
            # Check if user exists at all
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User {user_id} exists but is not a clinician"
                )
        
        return clinician
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching clinician: {str(e)}"
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

@router.delete("/unsubscribe", response_model=SubscriptionResponse)
async def unsubscribe_from_clinician(
    request: SubscriptionRequest,
    db: Session = Depends(get_db)
):
    """
    Unsubscribe a caregiver from a clinician
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
        
        # Remove clinician from subscribed list if already subscribed
        clinician_id_str = str(request.clinician_id)
        
        # Get current subscribed IDs, handle None case
        current_subscribed = caregiver.subscribed_clinicians_ids or []
        print(f"Current subscribed_clinicians_ids: {current_subscribed}")
        
        if clinician_id_str in current_subscribed:
            # Use direct SQL to remove from the array
            from sqlalchemy import text
            
            # PostgreSQL array_remove function to remove the clinician ID
            db.execute(
                text("""
                    UPDATE ariadne.caregivers 
                    SET subscribed_clinicians_ids = array_remove(subscribed_clinicians_ids, :clinician_id) 
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
                message="Not subscribed to this clinician"
            )
        
        return SubscriptionResponse(
            caregiver_id=request.caregiver_id,
            subscribed_clinician_id=request.clinician_id,
            message="Successfully unsubscribed from clinician"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error unsubscribing from clinician: {str(e)}"
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
        print(f"Looking for caregiver with user_id: {caregiver_id}")
        
        # First check if user exists at all
        user = db.query(User).filter(User.user_id == caregiver_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {caregiver_id} not found"
            )
        
        # Check if user is a caregiver
        if user.role != "caregiver":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User {caregiver_id} is a {user.role}, not a caregiver. This endpoint is for caregivers only."
            )
        
        # Get the caregiver from caregivers table
        caregiver = db.query(Caregiver).filter(Caregiver.user_id == caregiver_id).first()
        if not caregiver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Caregiver profile not found for user {caregiver_id}"
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

@router.get("/debug/caregivers")
async def debug_caregivers(db: Session = Depends(get_db)):
    """
    Debug endpoint to see what caregivers exist
    """
    try:
        caregivers = db.query(Caregiver).all()
        return {
            "total_caregivers": len(caregivers),
            "caregiver_ids": [c.user_id for c in caregivers],
            "caregivers": [
                {
                    "user_id": c.user_id,
                    "first_name": c.first_name,
                    "last_name": c.last_name,
                    "username": c.username
                } for c in caregivers
            ]
        }
    except Exception as e:
        return {"error": str(e)}

# Clinician-specific endpoints similar to caregivers

@router.get("/{user_id}", response_model=ClinicianResponse)
async def get_clinician_by_id_simple(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific clinician by user_id (simple endpoint like caregivers)
    """
    try:
        clinician = db.query(Clinician).filter(Clinician.user_id == user_id).first()
        
        if not clinician:
            # Check if user exists at all
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User {user_id} exists but is not a clinician"
                )
        
        return clinician
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching clinician: {str(e)}"
        )

@router.get("/clinician/{user_id}", response_model=ClinicianResponse)
async def get_clinician_by_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific clinician by user_id (similar to caregiver endpoint)
    """
    try:
        clinician = db.query(Clinician).filter(Clinician.user_id == user_id).first()
        
        if not clinician:
            # Check if user exists at all
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User {user_id} exists but is not a clinician"
                )
        
        return clinician
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching clinician: {str(e)}"
        )

@router.get("/debug/clinicians")
async def debug_clinicians(db: Session = Depends(get_db)):
    """
    Debug endpoint to see what clinicians exist
    """
    try:
        clinicians = db.query(Clinician).all()
        return {
            "total_clinicians": len(clinicians),
            "clinician_ids": [c.user_id for c in clinicians],
            "clinicians": [
                {
                    "user_id": c.user_id,
                    "first_name": c.first_name,
                    "last_name": c.last_name,
                    "specialty": c.specialty
                } for c in clinicians
            ]
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/debug/users")
async def debug_users(db: Session = Depends(get_db)):
    """
    Debug endpoint to see all users and their roles
    """
    try:
        users = db.query(User).all()
        return {
            "total_users": len(users),
            "users": [
                {
                    "user_id": u.user_id,
                    "email": u.email,
                    "role": u.role
                } for u in users
            ]
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/debug/user/{user_id}")
async def debug_user_by_id(user_id: int, db: Session = Depends(get_db)):
    """
    Debug endpoint to see a specific user's details
    """
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return {"error": f"User {user_id} not found"}
        
        result = {
            "user_id": user.user_id,
            "email": user.email,
            "role": user.role
        }
        
        # Check if user has a caregiver profile
        caregiver = db.query(Caregiver).filter(Caregiver.user_id == user_id).first()
        if caregiver:
            result["caregiver_profile"] = {
                "first_name": caregiver.first_name,
                "last_name": caregiver.last_name,
                "username": caregiver.username
            }
        
        # Check if user has a clinician profile
        clinician = db.query(Clinician).filter(Clinician.user_id == user_id).first()
        if clinician:
            result["clinician_profile"] = {
                "first_name": clinician.first_name,
                "last_name": clinician.last_name,
                "specialty": clinician.specialty
            }
        
        return result
    except Exception as e:
        return {"error": str(e)}

@router.get("/except/{exclude_id}", response_model=List[ClinicianResponse])
async def get_all_clinicians_except(
    exclude_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all clinicians except the one with the specified ID
    """
    try:
        # Query all clinicians except the one with exclude_id
        clinicians = db.query(Clinician).filter(
            Clinician.user_id != exclude_id
        ).all()
        
        return clinicians
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching clinicians: {str(e)}"
        )