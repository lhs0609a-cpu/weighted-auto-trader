"""
인증 모델
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class UserRole(str, Enum):
    """사용자 역할"""
    USER = "user"
    ADMIN = "admin"


class UserBase(BaseModel):
    """사용자 기본 정보"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    """사용자 생성"""
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """사용자 로그인"""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """사용자 정보 수정"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    """데이터베이스 사용자"""
    id: int
    hashed_password: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class User(UserBase):
    """사용자 응답 모델"""
    id: int
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT 토큰"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """토큰 페이로드"""
    sub: str  # user id
    email: str
    role: str
    exp: int
    iat: int
    type: str  # access or refresh


class PasswordChange(BaseModel):
    """비밀번호 변경"""
    current_password: str
    new_password: str = Field(..., min_length=8)


class PasswordReset(BaseModel):
    """비밀번호 재설정"""
    token: str
    new_password: str = Field(..., min_length=8)


class EmailVerification(BaseModel):
    """이메일 인증"""
    token: str
