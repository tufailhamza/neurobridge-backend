from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import stripe
import os
from ..models.base import get_db
from ..models.user import User
from ..schemas import StripeCustomerRequest, StripeCustomerResponse

# Initialize Stripe with API key from environment
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

router = APIRouter(prefix="/stripe", tags=["stripe"])

@router.post("/create-customer", response_model=StripeCustomerResponse)
async def create_stripe_customer(
    request: StripeCustomerRequest,
    db: Session = Depends(get_db)
):
    """
    Create a Stripe customer for a user
    """
    try:
        print(f"aaaaaaaaaaaaaaaaaaaaa {request}")
        # Check if user exis        
        user = db.query(User).filter(User.user_id == request.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user already has a Stripe customer ID
        if user.stripe_customer_id:
            return StripeCustomerResponse(
                user_id=user.user_id,
                stripe_customer_id=user.stripe_customer_id,
                email=user.email
            )
        
        # Create Stripe customer
        stripe_customer = stripe.Customer.create(
            email=request.email,
            metadata={"user_id": request.user_id}
        )
        
        # Store Stripe customer ID in database
        user.stripe_customer_id = stripe_customer.id
        db.commit()
        
        return StripeCustomerResponse(
            user_id=user.user_id,
            stripe_customer_id=stripe_customer.id,
            email=user.email
        )
        
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating Stripe customer: {str(e)}"
        )

@router.get("/customer/{user_id}", response_model=StripeCustomerResponse)
async def get_stripe_customer(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get Stripe customer info for a user
    """
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User has no Stripe customer ID"
            )
        
        return StripeCustomerResponse(
            user_id=user.user_id,
            stripe_customer_id=user.stripe_customer_id,
            email=user.email
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching Stripe customer: {str(e)}"
        )