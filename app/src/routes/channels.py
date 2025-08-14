# # src/routes/channels.py
# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from typing import List
# from pydantic import BaseModel

# from ..models.base import get_db
# # from ..models.channels import Channel

# router = APIRouter(prefix="/channels", tags=["channels"])

# # Response schema for channel list
# class ChannelInfo(BaseModel):
#     user_id: int
#     channel_name: str
    
#     class Config:
#         from_attributes = True

# @router.get("/user/{user_id}", response_model=List[ChannelInfo])
# async def get_user_channels(
#     user_id: int,
#     db: Session = Depends(get_db)
# ):
#     """
#     Get all channels that a specific user should listen to
#     """
#     try:
#         # Query channels for the specific user_id
#         channels = db.query(Channel).filter(Channel.user_id == user_id).all()
        
#         if not channels:
#             return []
        
#         return channels
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Error fetching user channels: {str(e)}"
#         )

# @router.get("/", response_model=List[ChannelInfo])
# async def get_all_channels(
#     db: Session = Depends(get_db)
# ):
#     """
#     Get all channels from the system
#     """
#     try:
#         # Query all channels
#         channels = db.query(Channel).all()
        
#         if not channels:
#             return []
        
#         return channels
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Error fetching all channels: {str(e)}"
#         )

# @router.post("/", response_model=ChannelInfo)
# async def create_user_channel(
#     user_id: int,
#     channel_name: str,
#     db: Session = Depends(get_db)
# ):
#     """
#     Create a new channel for a user
#     """
#     try:
#         # Check if channel already exists for this user
#         existing_channel = db.query(Channel).filter(
#             Channel.user_id == user_id,
#             Channel.channel_name == channel_name
#         ).first()
        
#         if existing_channel:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Channel already exists for this user"
#             )
        
#         # Create new channel
#         new_channel = Channel(
#             user_id=user_id,
#             channel_name=channel_name
#         )
        
#         db.add(new_channel)
#         db.commit()
#         db.refresh(new_channel)
        
#         return new_channel
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Error creating channel: {str(e)}"
#         )
