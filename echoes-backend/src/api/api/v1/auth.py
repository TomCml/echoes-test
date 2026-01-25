"""
Echoes Backend - Authentication Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_db
from src.infrastructure.database.repositories import (
    PlayerRepository,
    UserRepository,
)
from src.infrastructure.external.twitch_auth import get_twitch_auth_service
from src.application.use_cases.auth.login_twitch import LoginTwitchUseCase, LoginTwitchInput
from src.application.use_cases.auth.get_current_user import GetCurrentUserUseCase
from src.presentation.api.deps import get_current_user
from src.presentation.schemas.schemas import (
    TwitchCallbackRequest,
    TokenResponse,
    UserResponse,
    ErrorResponse,
)

router = APIRouter()


@router.post(
    "/twitch/callback",
    response_model=TokenResponse,
    responses={400: {"model": ErrorResponse}},
)
async def twitch_oauth_callback(
    request: TwitchCallbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Twitch OAuth callback.
    Exchanges authorization code for tokens and creates/updates user.
    """
    # Initialize repositories and services
    user_repo = UserRepository(db)
    player_repo = PlayerRepository(db)
    twitch_service = get_twitch_auth_service()
    
    # Execute use case
    use_case = LoginTwitchUseCase(
        user_repository=user_repo,
        player_repository=player_repo,
        twitch_service=twitch_service,
    )
    
    result, error = await use_case.execute(LoginTwitchInput(
        authorization_code=request.code,
    ))
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    
    return TokenResponse(
        access_token=result.access_token,
        token_type=result.token_type,
        expires_in=result.expires_in,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    responses={401: {"model": ErrorResponse}},
)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the currently authenticated user.
    """
    from uuid import UUID
    
    user_id = UUID(current_user["user_id"])
    
    user_repo = UserRepository(db)
    player_repo = PlayerRepository(db)
    
    use_case = GetCurrentUserUseCase(
        user_repository=user_repo,
        player_repository=player_repo,
    )
    
    result, error = await use_case.execute(user_id)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error,
        )
    
    return UserResponse(
        id=result.user_id,
        twitch_id=result.twitch_id,
        username=result.username,
        is_profile_public=result.is_profile_public,
        created_at=result.created_at,
    )
