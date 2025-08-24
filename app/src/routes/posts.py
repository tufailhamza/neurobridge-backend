# src/routes/posts.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime
from bs4 import BeautifulSoup
import math
import stripe
import logging

from ..models.base import get_db
from ..models.post import Post
from ..models.user import User
from ..models.purchases import Purchase
from ..schemas import PostCreate, PostResponse
from ..auth import get_current_user
from ..config import STRIPE_SECRET_KEY

# Initialize Stripe
stripe.api_key = STRIPE_SECRET_KEY

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/posts", tags=["posts"])

def _calculate_read_time(html_content: str, wpm: int = 200) -> int:
    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    words = text.split()
    word_count = len(words)
    minutes = math.ceil(word_count / wpm)

    return f"{minutes} min read"


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new post with automatic Stripe product and price creation
    """
    try:
        # Generate unique ID for the post
        post_id = str(uuid.uuid4())
        
        stripe_price_id = None
        stripe_product_id = None
        
        # If post has a price and tier is not free, create Stripe product and price
        if post_data.price and post_data.price > 0 and post_data.tier != "free":
            try:
                # 1. Create product in Stripe
                product = stripe.Product.create(
                    name=post_data.title,
                    description=f"Content: {post_data.title}",
                    metadata={
                        "post_id": post_id,
                        "user_id": str(current_user.user_id),
                        "tier": post_data.tier
                    }
                )
                stripe_product_id = product.id
                
                # 2. Create price in Stripe (convert price to cents)
                price_amount = int(post_data.price * 100)  # Convert dollars to cents
                price = stripe.Price.create(
                    unit_amount=price_amount,
                    currency="usd",
                    product=product.id,
                    metadata={
                        "post_id": post_id,
                        "user_id": str(current_user.user_id)
                    }
                )
                stripe_price_id = price.id
                
            except stripe.error.StripeError as e:
                logger.error(f"Stripe error creating product/price: {str(e)}")
                # Continue without Stripe IDs if there's an error
                stripe_price_id = None
                stripe_product_id = None
        
        # Create new post
        new_post = Post(
            id=post_id,
            image_url=post_data.image_url,
            title=post_data.title,
            user_id=current_user.user_id,
            date=datetime.now().strftime("%Y-%m-%d"),
            read_time=_calculate_read_time(post_data.html_content),
            tags=post_data.tags,
            price=post_data.price,
            html_content=post_data.html_content,
            allow_comments=post_data.allow_comments,
            tier=post_data.tier,
            collection=post_data.collection,
            attachments=post_data.attachments,
            date_published=post_data.date_published or datetime.now(),
            user_name=getattr(current_user, 'name', f"User {current_user.user_id}"),
            stripe_price_id=stripe_price_id,
            stripe_product_id=stripe_product_id
        )
        
        db.add(new_post)
        db.commit()
        db.refresh(new_post)
        
        return new_post
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating post: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create post: {str(e)}"
        )

@router.get("/", response_model=List[PostResponse])
def get_posts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    print("Posts endpoint called")
    print(f"Skip: {skip}, Limit: {limit}")
    
    try:
 
        
        posts = db.query(Post).offset(skip).limit(limit).all()
        print(f"Query completed. Found {len(posts)} posts")
        return posts
    except Exception as e:
        print(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@router.get("/test")
def test_posts_endpoint():
    """
    Simple test endpoint to check if the posts router is working
    """
    print("Test posts endpoint called")
    return {"message": "Posts endpoint is working", "status": "ok"}

@router.get("/{post_id}", response_model=PostResponse)
def get_post(post_id: str, db: Session = Depends(get_db)):
    """
    Get a specific post by ID
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    return post

@router.get("/user/{user_id}", response_model=List[PostResponse])
def get_user_posts(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all posts by a specific user
    """
    posts = db.query(Post).filter(Post.user_id == user_id).offset(skip).limit(limit).all()
    return posts

@router.get("/{post_id}/access/{user_id}")
def check_post_access(
    post_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Check if a user has access to a specific post
    """
    try:
        # Get the post
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        
        # If post is free, user has access
        if post.tier == "free" or post.price == 0 or post.price is None:
            return {
                "hasAccess": True,
                "reason": "free_content",
                "post": post
            }
        
        # Check if user has purchased this content
        purchase = db.query(Purchase).filter(
            Purchase.user_id == user_id,
            Purchase.content_id == post_id,
            Purchase.status == 'completed'
        ).first()
        
        if purchase:
            return {
                "hasAccess": True,
                "reason": "purchased",
                "purchaseId": purchase.id,
                "post": post
            }
        else:
            return {
                "hasAccess": False,
                "reason": "not_purchased",
                "post": {
                    "id": post.id,
                    "title": post.title,
                    "image_url": post.image_url,
                    "price": post.price,
                    "tier": post.tier,
                    "stripe_price_id": post.stripe_price_id,
                    "stripe_product_id": post.stripe_product_id
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking post access: {str(e)}"
        )

@router.put("/{post_id}/stripe-price")
def update_post_stripe_price(
    post_id: str,
    stripe_price_id: str,
    stripe_product_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update the Stripe price ID and product ID for a post
    """
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        
        # Check if user owns the post
        if post.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own posts"
            )
        
        post.stripe_price_id = stripe_price_id
        if stripe_product_id:
            post.stripe_product_id = stripe_product_id
        db.commit()
        
        return {
            "message": "Stripe price and product IDs updated successfully",
            "post_id": post_id,
            "stripe_price_id": stripe_price_id,
            "stripe_product_id": stripe_product_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating Stripe IDs: {str(e)}"
        )


