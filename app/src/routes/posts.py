from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..models.base import get_db
from ..models.post import Post
from ..schemas import PostResponse

router = APIRouter(prefix="/posts", tags=["posts"])

@router.get("/", response_model=List[PostResponse])
async def get_posts(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get the latest posts from the database
    Default: returns latest 20 posts
    """
    try:
        # Query posts ordered by date_published (newest first) with limit
        posts = db.query(Post).order_by(Post.date_published.desc()).limit(limit).all()
        
        if not posts:
            return []
        
        return posts
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching posts: {str(e)}"
        )
