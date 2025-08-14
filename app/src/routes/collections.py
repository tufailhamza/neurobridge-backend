# src/routes/collections.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..models.base import get_db
from ..models.collections import Collection
from ..models.user import User
from ..schemas import CollectionResponse, CollectionCreate
from ..auth import get_current_user

router = APIRouter(prefix="/collections", tags=["collections"])

@router.get("/user/{user_id}", response_model=List[CollectionResponse])
def get_user_collections(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all collections for a specific user
    """
    collections = db.query(Collection).filter(Collection.user_id == user_id).all()
    return collections

@router.post("/", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
def create_collection(
    collection_data: CollectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new collection for the current user
    """
    try:
        new_collection = Collection(
            user_id=current_user.user_id,
            name=collection_data.name
        )
        
        db.add(new_collection)
        db.commit()
        db.refresh(new_collection)
        
        return new_collection
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create collection: {str(e)}"
        )

@router.get("/", response_model=List[CollectionResponse])
def get_all_collections(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all collections with pagination
    """
    collections = db.query(Collection).offset(skip).limit(limit).all()
    return collections

@router.get("/{collection_id}", response_model=CollectionResponse)
def get_collection(
    collection_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific collection by ID
    """
    collection = db.query(Collection).filter(Collection.collection_id == collection_id).first()
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    return collection
