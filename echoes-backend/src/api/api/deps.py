"""
Echoes Backend - API Dependencies
FastAPI dependencies for authentication and common operations.
"""
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.infrastructure.database.connection import get_db
from src.infrastructure.database.repositories import UserRepository, PlayerRepository

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token", auto_error=False)


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the current user if authenticated, otherwise return None.
    """
    if not token:
        return None
    
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            return None
        
        # Fetch user from database
        user_id = UUID(user_id_str)
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)
        
        if not user:
            return None
        
        return {
            "user_id": str(user.id),
            "username": user.username,
            "twitch_id": user.twitch_id,
        }
    except (JWTError, ValueError):
        return None


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the current authenticated user or raise 401.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        
        # Fetch user from database
        user_id = UUID(user_id_str)
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)
        
        if not user:
            raise credentials_exception
        
        return {
            "user_id": str(user.id),
            "username": user.username,
            "twitch_id": user.twitch_id,
        }
    except (JWTError, ValueError):
        raise credentials_exception


async def get_current_player(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the current player for the authenticated user.
    Raises 404 if player doesn't exist.
    """
    user_id = UUID(current_user["user_id"])
    
    player_repo = PlayerRepository(db)
    player = await player_repo.get_by_user_id(user_id)
    
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found. Please create a character first.",
        )
    
    return player
