# src/routes/tracking.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from pydantic import BaseModel

from ..models.base import get_db
from ..models.user_tracking import UserTracking
from ..models.user import User

router = APIRouter(prefix="/tracking", tags=["user_tracking"])

# Response schema for tracking data
class TrackingInfo(BaseModel):
    user_id: int
    login_count: int
    viewed_posts_count: int
    bought_posts_count: int
    profile_view_count: int
    updated_at: str
    
    class Config:
        from_attributes = True

# Request schema for updating tracking
class TrackingUpdate(BaseModel):
    login_count: int = None
    viewed_posts_count: int = None
    bought_posts_count: int = None
    profile_view_count: int = None

@router.get("/user/{user_id}", response_model=TrackingInfo)
async def get_user_tracking(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get tracking information for a specific user
    """
    try:
        tracking = db.query(UserTracking).filter(UserTracking.user_id == user_id).first()
        
        if not tracking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tracking record not found for this user"
            )
        
        return tracking
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user tracking: {str(e)}"
        )

@router.get("/", response_model=List[TrackingInfo])
async def get_all_tracking(
    db: Session = Depends(get_db)
):
    """
    Get all user tracking records
    """
    try:
        tracking_records = db.query(UserTracking).all()
        return tracking_records
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching all tracking records: {str(e)}"
        )

@router.post("/user/{user_id}/login")
async def increment_login_count(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Increment login count for a user
    """
    try:
        # Check if user exists
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get or create tracking record
        tracking = db.query(UserTracking).filter(UserTracking.user_id == user_id).first()
        if not tracking:
            tracking = UserTracking(
                user_id=user_id,
                login_count=1,
                viewed_posts_count=0,
                bought_posts_count=0,
                profile_view_count=0
            )
            db.add(tracking)
        else:
            tracking.login_count += 1
        
        db.commit()
        
        return {
            "message": "Login count incremented successfully",
            "user_id": user_id,
            "new_login_count": tracking.login_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error incrementing login count: {str(e)}"
        )

@router.post("/user/{user_id}/view-post")
async def increment_viewed_posts(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Increment viewed posts count for a user
    """
    try:
        tracking = db.query(UserTracking).filter(UserTracking.user_id == user_id).first()
        if not tracking:
            # Create tracking record if it doesn't exist
            tracking = UserTracking(
                user_id=user_id,
                login_count=0,
                viewed_posts_count=1,
                bought_posts_count=0,
                profile_view_count=0
            )
            db.add(tracking)
        else:
            tracking.viewed_posts_count += 1
        
        db.commit()
        
        return {
            "message": "Viewed posts count incremented successfully",
            "user_id": user_id,
            "new_viewed_posts_count": tracking.viewed_posts_count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error incrementing viewed posts count: {str(e)}"
        )

@router.post("/user/{user_id}/buy-post")
async def increment_bought_posts(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Increment bought posts count for a user
    """
    try:
        tracking = db.query(UserTracking).filter(UserTracking.user_id == user_id).first()
        if not tracking:
            # Create tracking record if it doesn't exist
            tracking = UserTracking(
                user_id=user_id,
                login_count=0,
                viewed_posts_count=0,
                bought_posts_count=1,
                profile_view_count=0
            )
            db.add(tracking)
        else:
            tracking.bought_posts_count += 1
        
        db.commit()
        
        return {
            "message": "Bought posts count incremented successfully",
            "user_id": user_id,
            "new_bought_posts_count": tracking.bought_posts_count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error incrementing bought posts count: {str(e)}"
        )

@router.post("/user/{user_id}/view-profile")
async def increment_profile_views(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Increment profile view count for a user
    """
    try:
        tracking = db.query(UserTracking).filter(UserTracking.user_id == user_id).first()
        if not tracking:
            # Create tracking record if it doesn't exist
            tracking = UserTracking(
                user_id=user_id,
                login_count=0,
                viewed_posts_count=0,
                bought_posts_count=0,
                profile_view_count=1
            )
            db.add(tracking)
        else:
            tracking.profile_view_count += 1
        
        db.commit()
        
        return {
            "message": "Profile view count incremented successfully",
            "user_id": user_id,
            "new_profile_view_count": tracking.profile_view_count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error incrementing profile view count: {str(e)}"
        )

@router.put("/user/{user_id}", response_model=TrackingInfo)
async def update_user_tracking(
    user_id: int,
    tracking_update: TrackingUpdate,
    db: Session = Depends(get_db)
):
    """
    Update tracking information for a user
    """
    try:
        tracking = db.query(UserTracking).filter(UserTracking.user_id == user_id).first()
        if not tracking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tracking record not found for this user"
            )
        
        # Update only the fields that are provided
        if tracking_update.login_count is not None:
            tracking.login_count = tracking_update.login_count
        if tracking_update.viewed_posts_count is not None:
            tracking.viewed_posts_count = tracking_update.viewed_posts_count
        if tracking_update.bought_posts_count is not None:
            tracking.bought_posts_count = tracking_update.bought_posts_count
        if tracking_update.profile_view_count is not None:
            tracking.profile_view_count = tracking_update.profile_view_count
        
        db.commit()
        db.refresh(tracking)
        
        return tracking
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user tracking: {str(e)}"
        )

@router.delete("/user/{user_id}")
async def delete_user_tracking(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete tracking record for a user
    """
    try:
        tracking = db.query(UserTracking).filter(UserTracking.user_id == user_id).first()
        if not tracking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tracking record not found for this user"
            )
        
        db.delete(tracking)
        db.commit()
        
        return {
            "message": "Tracking record deleted successfully",
            "user_id": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting user tracking: {str(e)}"
        )
