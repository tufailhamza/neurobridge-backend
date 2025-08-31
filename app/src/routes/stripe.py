from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
import stripe
import os
import logging
from typing import Optional
from ..models.base import get_db
from ..models.user import User
from ..models.post import Post
from ..models.purchases import Purchase
from ..schemas import (
    PostResponse,
    StripeCustomerRequest, 
    StripeCustomerResponse,
    StripeCheckoutRequest,
    StripeCheckoutResponse,
    StripeVerifyRequest,
    StripeVerifyResponse,
    PurchaseResponse,
    PurchaseWithPostResponse
)
from ..config import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET

# Initialize Stripe with API key from environment
stripe.api_key = STRIPE_SECRET_KEY

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        # Check if user exists
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
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating Stripe customer: {str(e)}")
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
        logger.error(f"Error fetching Stripe customer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching Stripe customer: {str(e)}"
        )

@router.post("/create-checkout-session", response_model=StripeCheckoutResponse)
async def create_checkout_session(
    request: StripeCheckoutRequest,
    db: Session = Depends(get_db)
):
    """
    Create a Stripe checkout session for content purchase
    """
    try:
        # Get the price details from Stripe
        price = stripe.Price.retrieve(request.priceId)
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': request.priceId,
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.successUrl,
            cancel_url=request.cancelUrl,
            metadata=request.metadata,
            customer_email=request.metadata.get('userEmail'),  # Optional: pre-fill email
        )
        
        # Create purchase record in database
        purchase = Purchase(
            user_id=str(request.metadata.get('userId')),
            content_id=str(request.metadata.get('contentId')),
            stripe_session_id=checkout_session.id,
            amount=price.unit_amount,
            currency=price.currency,
            status='pending'
        )
        db.add(purchase)
        db.commit()
        
        return StripeCheckoutResponse(sessionId=checkout_session.id)
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating checkout session: {str(e)}"
        )

@router.post("/verify-payment", response_model=StripeVerifyResponse)
async def verify_payment(
    request: StripeVerifyRequest,
    db: Session = Depends(get_db)
):
    """
    Verify a payment using session ID
    """
    try:
        # Retrieve the checkout session from Stripe
        session = stripe.checkout.Session.retrieve(request.sessionId)
        
        # Find the purchase record
        purchase = db.query(Purchase).filter(
            Purchase.stripe_session_id == request.sessionId
        ).first()
        
        if not purchase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase record not found"
            )
        
        # Update purchase record with payment intent ID if available
        if session.payment_intent and not purchase.stripe_payment_intent_id:
            purchase.stripe_payment_intent_id = session.payment_intent
        
        # Update status based on payment status
        if session.payment_status == 'paid':
            purchase.status = 'completed'
        elif session.payment_status == 'unpaid':
            purchase.status = 'failed'
        
        db.commit()
        
        return StripeVerifyResponse(
            success=session.payment_status == 'paid',
            paymentStatus=session.payment_status,
            amount=session.amount_total,
            currency=session.currency
        )
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error verifying payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe error: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error verifying payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verifying payment: {str(e)}"
        )

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle Stripe webhooks for payment events
    """
    try:
        # Get the raw body
        body = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        if not sig_header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing stripe-signature header"
            )
        
        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                body, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            logger.error(f"Invalid payload: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payload"
            )
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature"
            )
        
        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            await handle_checkout_session_completed(session, db)
        elif event['type'] == 'checkout.session.expired':
            session = event['data']['object']
            await handle_checkout_session_expired(session, db)
        elif event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            await handle_payment_intent_succeeded(payment_intent, db)
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            await handle_payment_intent_failed(payment_intent, db)
        else:
            logger.info(f"Unhandled event type: {event['type']}")
        
        return {"status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing webhook"
        )

async def handle_checkout_session_completed(session, db: Session):
    """Handle successful checkout session completion"""
    try:
        purchase = db.query(Purchase).filter(
            Purchase.stripe_session_id == session.id
        ).first()
        
        if purchase:
            purchase.status = 'completed'
            if session.payment_intent:
                purchase.stripe_payment_intent_id = session.payment_intent
            db.commit()
            logger.info(f"Purchase {purchase.id} marked as completed")
            
            # Create post purchase record
            try:
                from ..models.post_purchases import PostPurchase
                
                # Check if post purchase already exists
                existing_post_purchase = db.query(PostPurchase).filter(
                    PostPurchase.user_id == int(purchase.user_id),
                    PostPurchase.post_id == purchase.content_id
                ).first()
                
                if not existing_post_purchase:
                    post_purchase = PostPurchase(
                        user_id=int(purchase.user_id),
                        post_id=purchase.content_id,
                        purchase_id=purchase.id,
                        amount=purchase.amount,
                        currency=purchase.currency
                    )
                    db.add(post_purchase)
                    db.commit()
                    logger.info(f"Post purchase record created for user {purchase.user_id} and post {purchase.content_id}")
                else:
                    logger.info(f"Post purchase record already exists for user {purchase.user_id} and post {purchase.content_id}")
                    
            except Exception as e:
                logger.error(f"Error creating post purchase record: {str(e)}")
                # Don't rollback the main purchase update
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error handling checkout session completed: {str(e)}")

async def handle_checkout_session_expired(session, db: Session):
    """Handle expired checkout session"""
    try:
        purchase = db.query(Purchase).filter(
            Purchase.stripe_session_id == session.id
        ).first()
        
        if purchase:
            purchase.status = 'expired'
            db.commit()
            logger.info(f"Purchase {purchase.id} marked as expired")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error handling checkout session expired: {str(e)}")

async def handle_payment_intent_succeeded(payment_intent, db: Session):
    """Handle successful payment intent"""
    try:
        purchase = db.query(Purchase).filter(
            Purchase.stripe_payment_intent_id == payment_intent.id
        ).first()
        
        if purchase:
            purchase.status = 'completed'
            db.commit()
            logger.info(f"Purchase {purchase.id} marked as completed via payment intent")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error handling payment intent succeeded: {str(e)}")

async def handle_payment_intent_failed(payment_intent, db: Session):
    """Handle failed payment intent"""
    try:
        purchase = db.query(Purchase).filter(
            Purchase.stripe_payment_intent_id == payment_intent.id
        ).first()
        
        if purchase:
            purchase.status = 'failed'
            db.commit()
            logger.info(f"Purchase {purchase.id} marked as failed")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error handling payment intent failed: {str(e)}")

@router.get("/purchases/{user_id}", response_model=list[PostResponse])
async def get_user_purchases(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all purchases for a user with associated post information
    """
    try:
        # Join Purchase with Post table on content_id = post.id
        purchases_with_posts = db.query(Purchase, Post).join(
            Post, Purchase.content_id == Post.id
        ).filter(
            Purchase.user_id == user_id
        ).all()
        
        logger.info(f"Found {len(purchases_with_posts)} purchases with posts for user {user_id}")
        
        # Convert to response format
        result = []
        for purchase, post in purchases_with_posts:
            try:
                # Create PostResponse object directly since we're returning list[PostResponse]
                post_response = PostResponse(
                    id=post.id,
                    image_url=post.image_url,
                    title=post.title,
                    user_id=post.user_id,
                    date=post.date,
                    read_time=post.read_time,
                    tags=post.tags,
                    price=post.price,
                    html_content=post.html_content,
                    allow_comments=post.allow_comments,
                    tier=post.tier,
                    collection=post.collection,
                    attachments=post.attachments,
                    date_published=post.date_published,
                    user_name=post.user_name,
                    updated_at=post.updated_at,
                    stripe_price_id=post.stripe_price_id,
                    stripe_product_id=post.stripe_product_id,
                    scheduled_time=post.scheduled_time
                )
                result.append(post_response)
            except Exception as e:
                logger.error(f"Error creating PostResponse for post {post.id}: {str(e)}")
                logger.error(f"Post data: {post.__dict__}")
                # Skip this post if there's an error
                continue
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching user purchases: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user purchases: {str(e)}"
        )

@router.get("/purchases/check/{user_id}/{content_id}")
async def check_purchase_access(
    user_id: str,
    content_id: str,
    db: Session = Depends(get_db)
):
    """
    Check if user has access to content (has purchased it)
    """
    try:
        purchase = db.query(Purchase).filter(
            Purchase.user_id == user_id,
            Purchase.content_id == content_id,
            Purchase.status == 'completed'
        ).first()
        
        return {
            "hasAccess": purchase is not None,
            "purchaseId": purchase.id if purchase else None
        }
        
    except Exception as e:
        logger.error(f"Error checking purchase access: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking purchase access: {str(e)}"
        )

@router.put("/posts/{post_id}/price")
async def update_post_price_id(
    post_id: str,
    price_id: str,
    db: Session = Depends(get_db)
):
    """
    Manually update the Stripe price ID for a post
    """
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        
        # Update the price ID
        post.stripe_price_id = price_id
        db.commit()
        
        return {
            "message": "Price ID updated successfully",
            "post_id": post_id,
            "stripe_price_id": price_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating post price ID: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating post price ID: {str(e)}"
        )


@router.post("/create-payment-intent")
async def create_payment_intent(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Create payment intent using saved payment method
    """
    try:
        # Get request body
        body = await request.json()
        amount = body.get("amount")
        currency = body.get("currency", "usd")
        payment_method_id = body.get("paymentMethodId")
        metadata = body.get("metadata", {})
        
        if not amount or not payment_method_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amount and payment method ID required"
            )
        
        user_id = metadata.get('userId')
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID required"
            )
        
        # Get user from database
        user = db.query(User).filter(User.user_id == int(user_id)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Create Stripe customer if doesn't exist
        if not user.stripe_customer_id:
            stripe_customer = stripe.Customer.create(
                email=user.email,
                metadata={"user_id": str(user.user_id)}
            )
            user.stripe_customer_id = stripe_customer.id
            db.commit()
        
        # Create payment intent
        payment_intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            payment_method=payment_method_id,
            customer=user.stripe_customer_id,
            confirm=True,  # Auto-confirm the payment
            metadata=metadata,
            return_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/caregiver/payment/success"
        )
        
        # Create purchase record in database
        purchase = Purchase(
            user_id=str(user_id),
            content_id=str(metadata.get('contentId')),
            stripe_payment_intent_id=payment_intent.id,
            amount=amount,
            currency=currency,
            status='pending'
        )
        db.add(purchase)
        db.commit()
        
        return {"clientSecret": payment_intent.client_secret}
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating payment intent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe error: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating payment intent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating payment intent: {str(e)}"
        )


@router.post("/create-price")
async def create_stripe_price(
    product_name: str,
    amount: int,  # Amount in cents (e.g., 2000 for $20.00)
    currency: str = "usd",
    db: Session = Depends(get_db)
):
    """
    Create a new Stripe price for testing
    """
    try:
        # Create a product first
        product = stripe.Product.create(
            name=product_name,
            description=f"Content: {product_name}"
        )
        
        # Create a price for the product
        price = stripe.Price.create(
            product=product.id,
            unit_amount=amount,
            currency=currency,
            recurring=None  # One-time payment
        )
        
        return {
            "message": "Price created successfully",
            "product_id": product.id,
            "price_id": price.id,
            "amount": amount,
            "currency": currency
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating price: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error creating price: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating price: {str(e)}"
        )

@router.post("/create-product")
async def create_stripe_product(
    name: str,
    description: Optional[str] = None,
    images: Optional[list[str]] = None,
    db: Session = Depends(get_db)
):
    """
    Create a new Stripe product
    """
    try:
        product_data = {
            "name": name,
            "description": description or f"Content: {name}"
        }
        
        if images:
            product_data["images"] = images
        
        product = stripe.Product.create(**product_data)
        
        return {
            "message": "Product created successfully",
            "product_id": product.id,
            "name": product.name,
            "description": product.description
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating product: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating product: {str(e)}"
        )

@router.get("/payment-methods")
async def get_payment_methods(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get payment methods for a user
    """
    try:
        # Get user's Stripe customer ID
        user = db.query(User).filter(User.user_id == int(user_id)).first()
        if not user or not user.stripe_customer_id:
            return {"payment_methods": []}
        
        # Get payment methods from Stripe
        payment_methods = stripe.PaymentMethod.list(
            customer=user.stripe_customer_id,
            type='card'
        )
        
        return {
            "payment_methods": [
                {
                    "id": pm.id,
                    "type": pm.type,
                    "card": {
                        "brand": pm.card.brand,
                        "last4": pm.card.last4,
                        "exp_month": pm.card.exp_month,
                        "exp_year": pm.card.exp_year
                    } if pm.card else None
                } for pm in payment_methods.data
            ]
        }
        
    except Exception as e:
        logger.error(f"Error fetching payment methods: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching payment methods: {str(e)}"
        )

@router.post("/save-payment-method")
async def save_payment_method(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Save a payment method for a user
    """
    try:
        # Get request body
        body = await request.json()
        logger.info(f"Save payment method request body: {body}")
        
        # Try different possible field names
        payment_method_id = body.get("paymentMethodId") or body.get("payment_method_id") or body.get("paymentMethod")
        user_id = body.get("userId") or body.get("user_id") or body.get("user")
        
        logger.info(f"Extracted payment_method_id: {payment_method_id}, user_id: {user_id}")
        
        if not payment_method_id or not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment method ID and user ID required. Received: payment_method_id={payment_method_id}, user_id={user_id}"
            )
        
        # Get or create Stripe customer
        user = db.query(User).filter(User.user_id == int(user_id)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Create Stripe customer if doesn't exist
        if not user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                metadata={"user_id": str(user.user_id)}
            )
            user.stripe_customer_id = customer.id
            db.commit()
        
        # Attach payment method to customer
        stripe.PaymentMethod.attach(
            payment_method_id,
            customer=user.stripe_customer_id
        )
        
        return {
            "message": "Payment method saved successfully",
            "payment_method_id": payment_method_id,
            "customer_id": user.stripe_customer_id
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error saving payment method: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe error: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving payment method: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving payment method: {str(e)}"
        )