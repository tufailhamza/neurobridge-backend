from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..models.base import get_db
from ..models.post_purchases import PostPurchase
from ..models.user import User
from ..models.post import Post
from ..models.purchases import Purchase
from ..schemas import (
    PostPurchaseResponse, 
    UserPostPurchaseResponse, 
    PostPurchaseStatsResponse
)
from sqlalchemy.orm import joinedload

router = APIRouter(prefix="/post-purchases", tags=["post-purchases"])

@router.post("/create", response_model=PostPurchaseResponse)
async def create_post_purchase(
    user_id: int,
    post_id: str,
    purchase_id: int = None,
    amount: int = 0,
    currency: str = "usd",
    db: Session = Depends(get_db)
):
    """
    Create a new post purchase record
    """
    try:
        # Check if user exists
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if post exists
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        
        # Check if purchase already exists
        existing_purchase = db.query(PostPurchase).filter(
            PostPurchase.user_id == user_id,
            PostPurchase.post_id == post_id
        ).first()
        
        if existing_purchase:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User has already purchased this post"
            )
        
        # Create new post purchase
        post_purchase = PostPurchase(
            user_id=user_id,
            post_id=post_id,
            purchase_id=purchase_id,
            amount=amount,
            currency=currency
        )
        
        db.add(post_purchase)
        db.commit()
        db.refresh(post_purchase)
        
        return post_purchase
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating post purchase: {str(e)}"
        )

@router.get("/user/{user_id}", response_model=List[UserPostPurchaseResponse])
async def get_user_post_purchases(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all posts purchased by a specific user
    OPTIMIZED VERSION - Uses direct SQL join for better performance
    """
    try:
        # Use raw SQL for better performance
        query = """
        SELECT 
            pp.user_id,
            u.email as user_email,
            SPLIT_PART(u.email, '@', 1) as user_name,
            pp.post_id,
            p.title as post_title,
            pp.amount,
            pp.currency,
            pp.purchased_at
        FROM ariadne.post_purchases pp
        INNER JOIN ariadne.posts p ON pp.post_id = p.id
        INNER JOIN ariadne.users u ON pp.user_id = u.user_id
        WHERE pp.user_id = :user_id
        ORDER BY pp.purchased_at DESC
        """
        
        result = db.execute(query, {"user_id": user_id})
        rows = result.fetchall()
        
        # Check if user exists (only if no purchases found)
        if not rows:
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            return []
        
        # Format response
        result = []
        for row in rows:
            result.append({
                "user_id": row.user_id,
                "user_email": row.user_email,
                "user_name": row.user_name,
                "post_id": row.post_id,
                "post_title": row.post_title,
                "amount": row.amount,
                "currency": row.currency,
                "purchased_at": row.purchased_at
            })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user post purchases: {str(e)}"
        )

@router.get("/post/{post_id}", response_model=List[UserPostPurchaseResponse])
async def get_post_purchasers(
    post_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all users who purchased a specific post
    """
    try:
        # Check if post exists
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        
        # Get all purchases for the post with user details
        purchases = db.query(PostPurchase).options(
            joinedload(PostPurchase.user),
            joinedload(PostPurchase.post)
        ).filter(PostPurchase.post_id == post_id).all()
        
        # Format response
        result = []
        for purchase in purchases:
            result.append({
                "user_id": purchase.user_id,
                "user_email": purchase.user.email,
                "user_name": purchase.user.email.split('@')[0],  # Simple name extraction
                "post_id": purchase.post_id,
                "post_title": purchase.post.title,
                "amount": purchase.amount,
                "currency": purchase.currency,
                "purchased_at": purchase.purchased_at
            })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching post purchasers: {str(e)}"
        )

@router.get("/stats/{post_id}", response_model=PostPurchaseStatsResponse)
async def get_post_purchase_stats(
    post_id: str,
    db: Session = Depends(get_db)
):
    """
    Get purchase statistics for a specific post
    """
    try:
        # Check if post exists
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        
        # Get all purchases for the post
        purchases = db.query(PostPurchase).filter(PostPurchase.post_id == post_id).all()
        
        total_purchases = len(purchases)
        total_revenue = sum(purchase.amount for purchase in purchases)
        currency = purchases[0].currency if purchases else "usd"
        
        return {
            "post_id": post_id,
            "post_title": post.title,
            "total_purchases": total_purchases,
            "total_revenue": total_revenue,
            "currency": currency
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching post purchase stats: {str(e)}"
        )

@router.get("/check/{user_id}/{post_id}")
async def check_user_post_purchase(
    user_id: int,
    post_id: str,
    db: Session = Depends(get_db)
):
    """
    Check if a user has purchased a specific post
    """
    try:
        purchase = db.query(PostPurchase).filter(
            PostPurchase.user_id == user_id,
            PostPurchase.post_id == post_id
        ).first()
        
        return {
            "user_id": user_id,
            "post_id": post_id,
            "has_purchased": purchase is not None,
            "purchase_details": {
                "amount": purchase.amount,
                "currency": purchase.currency,
                "purchased_at": purchase.purchased_at
            } if purchase else None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking post purchase: {str(e)}"
        )

@router.get("/all", response_model=List[UserPostPurchaseResponse])
async def get_all_post_purchases(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get all post purchases with pagination
    """
    try:
        purchases = db.query(PostPurchase).options(
            joinedload(PostPurchase.user),
            joinedload(PostPurchase.post)
        ).offset(offset).limit(limit).all()
        
        # Format response
        result = []
        for purchase in purchases:
            result.append({
                "user_id": purchase.user_id,
                "user_email": purchase.user.email,
                "user_name": purchase.user.email.split('@')[0],  # Simple name extraction
                "post_id": purchase.post_id,
                "post_title": purchase.post.title,
                "amount": purchase.amount,
                "currency": purchase.currency,
                "purchased_at": purchase.purchased_at
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching all post purchases: {str(e)}"
        )

@router.get("/user-posts/{user_id}")
async def get_user_purchased_posts_full(
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get all posts (full post details) purchased by a specific user
    OPTIMIZED VERSION - Uses direct SQL join for better performance
    """
    try:
        # Use raw SQL for better performance - single query instead of multiple joins
        query = """
        SELECT 
            pp.id as purchase_id,
            pp.amount as purchase_amount,
            pp.currency as purchase_currency,
            pp.purchased_at,
            p.id as post_id,
            p.title,
            p.image_url,
            p.html_content,
            p.tags,
            p.price,
            p.tier,
            p.collection,
            p.attachments,
            p.date_published,
            p.read_time,
            p.allow_comments,
            p.stripe_price_id,
            p.stripe_product_id,
            p.updated_at,
            p.user_id as author_id,
            p.user_name as author_name
        FROM ariadne.post_purchases pp
        INNER JOIN ariadne.posts p ON pp.post_id = p.id
        WHERE pp.user_id = :user_id
        ORDER BY pp.purchased_at DESC
        LIMIT :limit OFFSET :offset
        """
        
        result = db.execute(query, {"user_id": user_id, "limit": limit, "offset": offset})
        rows = result.fetchall()
        
        # Check if user exists (only if no purchases found)
        if not rows:
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            return {
                "user_id": user_id,
                "user_email": user.email,
                "total_purchased_posts": 0,
                "purchased_posts": []
            }
        
        # Format response
        purchased_posts = []
        for row in rows:
            purchased_posts.append({
                # Purchase details
                "purchase_id": row.purchase_id,
                "purchase_amount": row.purchase_amount,
                "purchase_currency": row.purchase_currency,
                "purchased_at": row.purchased_at,
                
                # Full post details
                "post_id": row.post_id,
                "title": row.title,
                "image_url": row.image_url,
                "html_content": row.html_content,
                "tags": row.tags,
                "price": row.price,
                "tier": row.tier,
                "collection": row.collection,
                "attachments": row.attachments,
                "date_published": row.date_published,
                "read_time": row.read_time,
                "allow_comments": row.allow_comments,
                "stripe_price_id": row.stripe_price_id,
                "stripe_product_id": row.stripe_product_id,
                "updated_at": row.updated_at,
                
                # Post author details
                "author_id": row.author_id,
                "author_name": row.author_name
            })
        
        # Get user email for response
        user = db.query(User).filter(User.user_id == user_id).first()
        
        return {
            "user_id": user_id,
            "user_email": user.email if user else "Unknown",
            "total_purchased_posts": len(purchased_posts),
            "purchased_posts": purchased_posts
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user purchased posts: {str(e)}"
        )
