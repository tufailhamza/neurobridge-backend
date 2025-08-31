# src/routes/profile.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session, joinedload
from typing import Dict, Any, Optional
from pydantic import BaseModel
import cloudinary
import cloudinary.uploader
import base64
import os

from ..models.base import get_db
from ..models.user import User
from ..models.caregivers import Caregiver
from ..models.clinician import Clinician

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def upload_image_to_cloudinary(image_data: str, folder: str = "neurobridge") -> str:
    """
    Upload base64 image data to Cloudinary and return the URL
    
    Args:
        image_data: Base64 encoded image string (with or without data:image/... prefix)
        folder: Cloudinary folder to upload to
    
    Returns:
        Cloudinary URL of the uploaded image
    """
    try:
        # Remove data:image/... prefix if present
        if image_data.startswith('data:image/'):
            image_data = image_data.split(',')[1]
        
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            f"data:image/jpeg;base64,{image_data}",
            folder=folder,
            resource_type="image"
        )
        print(f"Result: {result}")
        return result.get('secure_url', result.get('url', ''))
    except Exception as e:
        print(f"Error uploading image to Cloudinary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading image: {str(e)}"
        )

router = APIRouter(prefix="/profile", tags=["profile"])

@router.get("/{user_id}")
async def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get complete user profile information by joining the relevant table based on role
    """
    try:
        # Get user with basic info
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Base user data
        profile_data = {
            "user_id": user.user_id,
            "email": user.email,
            "role": user.role,
            "account_create_date": user.account_create_date,
            "last_active_at": user.last_active_at,
            "last_engagement_at": user.last_engagement_at,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "stripe_customer_id": user.stripe_customer_id
        }
        
        # Get role-specific profile data
        if user.role == "caregiver":
            # Get caregiver profile with joined data
            caregiver = db.query(Caregiver).filter(Caregiver.user_id == user_id).first()
            if not caregiver:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Caregiver profile not found"
                )
            
            # Add caregiver-specific data
            profile_data.update({
                "profile_type": "caregiver",
                "first_name": caregiver.first_name,
                "last_name": caregiver.last_name,
                "username": caregiver.username,
                "country": caregiver.country,
                "city": caregiver.city,
                "state": caregiver.state,
                "zip_code": caregiver.zip_code,
                "caregiver_role": caregiver.caregiver_role,
                "childs_age": caregiver.childs_age,
                "diagnosis": caregiver.diagnosis,
                "years_of_diagnosis": caregiver.years_of_diagnosis,
                "make_name_public": caregiver.make_name_public,
                "make_personal_details_public": caregiver.make_personal_details_public,
                "profile_image": caregiver.profile_image,
                "cover_image": caregiver.cover_image,
                "content_preferences_tags": caregiver.content_preferences_tags or [],
                "bio": caregiver.bio,
                "subscribed_clinicians_ids": caregiver.subscribed_clinicians_ids or [],
                "purchased_feed_content_ids": caregiver.purchased_feed_content_ids or []
            })
            
        elif user.role == "clinician":
            # Get clinician profile with joined data
            clinician = db.query(Clinician).filter(Clinician.user_id == user_id).first()
            if not clinician:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Clinician profile not found"
                )
            
            # Add clinician-specific data
            profile_data.update({
                "profile_type": "clinician",
                "specialty": clinician.specialty,
                "profile_image": clinician.profile_image,
                "cover_image": clinician.cover_image,
                "is_subscribed": clinician.is_subscribed,
                "prefix": clinician.prefix,
                "first_name": clinician.first_name,
                "last_name": clinician.last_name,
                "country": clinician.country,
                "city": clinician.city,
                "state": clinician.state,
                "zip_code": clinician.zip_code,
                "bio": clinician.bio,
                "approach": clinician.approach,
                "clinician_type": clinician.clinician_type,
                "license_number": clinician.license_number,
                "area_of_expertise": clinician.area_of_expertise,
                "content_preferences_tags": clinician.content_preferences_tags or []
            })
            
        else:
            # Handle other roles (like admin)
            profile_data.update({
                "profile_type": "basic",
                "message": "Profile type not fully implemented for this role"
            })
        
        return profile_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user profile: {str(e)}"
        )

@router.put("/{user_id}")
async def update_user_profile(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Update user profile based on their role (caregiver or clinician)
    """
    try:
        # Get user to determine their role
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get the request body
        body = await request.json()
        print(f"Body: {body}")
        # Get the request body based on role
        if user.role == "caregiver":
            
            # Validate and update caregiver profile
            caregiver = db.query(Caregiver).filter(Caregiver.user_id == user_id).first()
            if not caregiver:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Caregiver profile not found"
                )
            
            # Update only the fields that are provided
            if 'first_name' in body and body['first_name'] is not None:
                caregiver.first_name = body['first_name']
            if 'last_name' in body and body['last_name'] is not None:
                caregiver.last_name = body['last_name']
            if 'username' in body and body['username'] is not None:
                caregiver.username = body['username']
            if 'country' in body and body['country'] is not None:
                caregiver.country = body['country']
            if 'city' in body and body['city'] is not None:
                caregiver.city = body['city']
            if 'state' in body and body['state'] is not None:
                caregiver.state = body['state']
            if 'zip_code' in body and body['zip_code'] is not None:
                caregiver.zip_code = body['zip_code']
            if 'caregiver_role' in body and body['caregiver_role'] is not None:
                caregiver.caregiver_role = body['caregiver_role']
            if 'childs_age' in body and body['childs_age'] is not None:
                caregiver.childs_age = body['childs_age']
            if 'diagnosis' in body and body['diagnosis'] is not None:
                caregiver.diagnosis = body['diagnosis']
            if 'years_of_diagnosis' in body and body['years_of_diagnosis'] is not None:
                caregiver.years_of_diagnosis = body['years_of_diagnosis']
            if 'make_name_public' in body and body['make_name_public'] is not None:
                caregiver.make_name_public = body['make_name_public']
            if 'make_personal_details_public' in body and body['make_personal_details_public'] is not None:
                caregiver.make_personal_details_public = body['make_personal_details_public']
            if 'profile_image' in body and body['profile_image']:
                # Upload profile image to Cloudinary
                cloudinary_url = upload_image_to_cloudinary(body['profile_image'], "neurobridge/profile_images")
                caregiver.profile_image = cloudinary_url
            if 'cover_image' in body and body['cover_image']:
                # Upload cover image to Cloudinary
                cloudinary_url = upload_image_to_cloudinary(body['cover_image'], "neurobridge/cover_images")
                caregiver.cover_image = cloudinary_url
            if 'bio' in body:
                caregiver.bio = body['bio']
            if 'content_preferences_tags' in body:
                caregiver.content_preferences_tags = body['content_preferences_tags']
            
            db.commit()
            
            return {
                "message": "Caregiver profile updated successfully",
                "user_id": user_id,
                "role": "caregiver"
            }
            
        elif user.role == "clinician":
            # Validate and update clinician profile
            clinician = db.query(Clinician).filter(Clinician.user_id == user_id).first()
            if not clinician:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Clinician profile not found"
                )
            
            
            # Update only the fields that are provided
            if 'specialty' in body and body['specialty'] is not None:
                clinician.specialty = body['specialty']
            if 'profile_image' in body and body['profile_image']:
                # Upload profile image to Cloudinary
                cloudinary_url = upload_image_to_cloudinary(body['profile_image'], "neurobridge/profile_images")
                clinician.profile_image = cloudinary_url
            if 'cover_image' in body and body['cover_image']:
                print(f"Profile image data type: FFFFFFFFFFFFFFF")
                # Upload cover image to Cloudinary
                cloudinary_url = upload_image_to_cloudinary(body['cover_image'], "neurobridge/cover_images")
                clinician.cover_image = cloudinary_url
            if 'prefix' in body:
                clinician.prefix = body['prefix']
            if 'first_name' in body and body['first_name'] is not None:
                clinician.first_name = body['first_name']
            if 'last_name' in body and body['last_name'] is not None:
                clinician.last_name = body['last_name']
            if 'country' in body and body['country'] is not None:
                clinician.country = body['country']
            if 'city' in body and body['city'] is not None:
                clinician.city = body['city']
            if 'bio' in body and body['bio'] is not None:
                clinician.bio = body['bio']
            if 'approach' in body and body['approach'] is not None:
                clinician.approach = body['approach']
            if 'state' in body and body['state'] is not None:
                clinician.state = body['state']
            if 'zip_code' in body and body['zip_code'] is not None:
                clinician.zip_code = body['zip_code']
            if 'clinician_type' in body and body['clinician_type'] is not None:
                clinician.clinician_type = body['clinician_type']
            if 'license_number' in body and body['license_number'] is not None:
                clinician.license_number = body['license_number']
            if 'area_of_expertise' in body and body['area_of_expertise'] is not None:
                clinician.area_of_expertise = body['area_of_expertise']
            if 'content_preferences_tags' in body and body['content_preferences_tags'] is not None:
                clinician.content_preferences_tags = body['content_preferences_tags']
            
            db.commit()
            
            return {
                "message": "Clinician profile updated successfully",
                "user_id": user_id,
                "role": "clinician"
            }
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Profile updates not supported for role: {user.role}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user profile: {str(e)}"
        )
