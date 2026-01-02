"""
인증 의존성
- FastAPI 의존성 주입
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .models import User, UserRole
from .service import auth_service

# Bearer 토큰 스키마
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    현재 인증된 사용자 조회

    Args:
        credentials: Bearer 토큰

    Returns:
        User: 현재 사용자

    Raises:
        HTTPException: 인증 실패시 401
    """
    token = credentials.credentials

    user = await auth_service.get_current_user(token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    현재 활성 사용자 조회

    Args:
        current_user: 현재 사용자

    Returns:
        User: 활성 사용자

    Raises:
        HTTPException: 비활성 사용자 400
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    return current_user


async def get_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    관리자 사용자 조회

    Args:
        current_user: 현재 활성 사용자

    Returns:
        User: 관리자 사용자

    Raises:
        HTTPException: 권한 없음 403
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return current_user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[User]:
    """
    선택적 사용자 조회 (인증 옵션)

    Args:
        credentials: Bearer 토큰 (optional)

    Returns:
        Optional[User]: 사용자 또는 None
    """
    if not credentials:
        return None

    token = credentials.credentials
    # Note: This is synchronous for simplicity
    # In production, consider making this async
    try:
        payload = auth_service.verify_token(token)
        if not payload:
            return None

        user = auth_service.get_user_by_id(int(payload.sub))
        if not user or not user.is_active:
            return None

        return User(
            id=user.id,
            email=user.email,
            username=user.username,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
    except Exception:
        return None
