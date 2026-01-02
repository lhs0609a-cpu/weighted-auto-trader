"""
인증 API 라우트
"""
from fastapi import APIRouter, Depends, HTTPException, status

from .models import (
    User,
    UserCreate,
    UserLogin,
    Token,
    PasswordChange
)
from .service import auth_service
from .dependencies import get_current_user, get_current_active_user, get_admin_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    회원가입

    - **email**: 이메일 주소
    - **username**: 사용자 이름 (3-50자)
    - **password**: 비밀번호 (8자 이상)
    """
    user = await auth_service.register(user_data)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    return user


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    """
    로그인

    - **email**: 이메일 주소
    - **password**: 비밀번호
    """
    token = await auth_service.login(login_data)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return token


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """
    토큰 갱신

    - **refresh_token**: 리프레시 토큰
    """
    token = await auth_service.refresh_tokens(refresh_token)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return token


@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """
    현재 사용자 정보 조회
    """
    return current_user


@router.put("/me/password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user)
):
    """
    비밀번호 변경

    - **current_password**: 현재 비밀번호
    - **new_password**: 새 비밀번호 (8자 이상)
    """
    success = await auth_service.change_password(
        current_user.id,
        password_data.current_password,
        password_data.new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid current password"
        )

    return {"message": "Password changed successfully"}


@router.delete("/me")
async def deactivate_account(
    current_user: User = Depends(get_current_active_user)
):
    """
    계정 비활성화
    """
    await auth_service.deactivate_user(current_user.id)
    return {"message": "Account deactivated"}


@router.get("/users", response_model=list[User])
async def get_all_users(admin_user: User = Depends(get_admin_user)):
    """
    모든 사용자 조회 (관리자 전용)
    """
    return await auth_service.get_all_users()


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    로그아웃

    클라이언트 측에서 토큰 삭제 필요
    서버 측에서는 토큰 블랙리스트 관리 가능 (선택사항)
    """
    # In production, you might want to:
    # - Add the token to a blacklist
    # - Clear any server-side session data
    return {"message": "Logged out successfully"}
