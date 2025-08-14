# src/routes/posts.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from ..models.base import get_db
from ..models.post import Post
from ..models.user import User
from ..schemas import PostCreate, PostResponse
from ..auth import get_current_user

router = APIRouter(prefix="/posts", tags=["posts"])

@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    post_data: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new post
    """
    try:
        # Generate unique ID for the post
        post_id = str(uuid.uuid4())
        
        # Create new post
        new_post = Post(
            id=post_id,
            image_url=post_data.image_url,
            title=post_data.title,
            user_id=current_user.user_id,
            date=datetime.now().strftime("%Y-%m-%d"),
            read_time=post_data.read_time,
            tags=post_data.tags,
            price=post_data.price,
            html_content=post_data.html_content,
            allow_comments=post_data.allow_comments,
            tier=post_data.tier,
            collection=post_data.collection,
            attachments=post_data.attachments,
            date_published=post_data.date_published or datetime.now(),
            user_name=current_user.name
        )
        
        db.add(new_post)
        db.commit()
        db.refresh(new_post)
        
        return new_post
        
    except Exception as e:
        db.rollback()
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
    """
    Get all posts with pagination
    """
    posts = db.query(Post).offset(skip).limit(limit).all()
    return posts

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


