"""
인증 서비스
- 회원가입, 로그인
- JWT 토큰 발급/검증
- 비밀번호 해싱
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import hashlib
import secrets
import jwt

from .models import (
    User,
    UserCreate,
    UserLogin,
    UserInDB,
    Token,
    TokenPayload,
    UserRole
)


class AuthService:
    """인증 서비스"""

    def __init__(
        self,
        secret_key: str = "your-secret-key-here",
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire = timedelta(minutes=access_token_expire_minutes)
        self.refresh_token_expire = timedelta(days=refresh_token_expire_days)

        # In-memory user store (replace with database in production)
        self._users: Dict[str, UserInDB] = {}
        self._user_id_counter = 0

    def hash_password(self, password: str) -> str:
        """비밀번호 해싱"""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return f"{salt}:{hash_obj.hex()}"

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        try:
            salt, hash_value = hashed_password.split(':')
            hash_obj = hashlib.pbkdf2_hmac(
                'sha256',
                plain_password.encode('utf-8'),
                salt.encode('utf-8'),
                100000
            )
            return hash_obj.hex() == hash_value
        except Exception:
            return False

    def create_token(
        self,
        user: UserInDB,
        token_type: str = "access"
    ) -> str:
        """JWT 토큰 생성"""
        now = datetime.utcnow()

        if token_type == "access":
            expire = now + self.access_token_expire
        else:
            expire = now + self.refresh_token_expire

        payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "exp": int(expire.timestamp()),
            "iat": int(now.timestamp()),
            "type": token_type
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[TokenPayload]:
        """토큰 검증"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return TokenPayload(**payload)
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    async def register(self, user_data: UserCreate) -> Optional[User]:
        """회원가입"""
        # 이메일 중복 체크
        if self.get_user_by_email(user_data.email):
            return None

        self._user_id_counter += 1

        user_in_db = UserInDB(
            id=self._user_id_counter,
            email=user_data.email,
            username=user_data.username,
            hashed_password=self.hash_password(user_data.password),
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.utcnow()
        )

        self._users[user_data.email] = user_in_db

        return User(
            id=user_in_db.id,
            email=user_in_db.email,
            username=user_in_db.username,
            role=user_in_db.role,
            is_active=user_in_db.is_active,
            created_at=user_in_db.created_at
        )

    async def login(self, login_data: UserLogin) -> Optional[Token]:
        """로그인"""
        user = self.get_user_by_email(login_data.email)

        if not user:
            return None

        if not self.verify_password(login_data.password, user.hashed_password):
            return None

        if not user.is_active:
            return None

        # Update last login
        user.last_login = datetime.utcnow()

        # Generate tokens
        access_token = self.create_token(user, "access")
        refresh_token = self.create_token(user, "refresh")

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

    async def refresh_tokens(self, refresh_token: str) -> Optional[Token]:
        """토큰 갱신"""
        payload = self.verify_token(refresh_token)

        if not payload or payload.type != "refresh":
            return None

        user = self.get_user_by_id(int(payload.sub))

        if not user or not user.is_active:
            return None

        new_access_token = self.create_token(user, "access")
        new_refresh_token = self.create_token(user, "refresh")

        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )

    async def get_current_user(self, token: str) -> Optional[User]:
        """현재 사용자 조회"""
        payload = self.verify_token(token)

        if not payload or payload.type != "access":
            return None

        user = self.get_user_by_id(int(payload.sub))

        if not user:
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

    async def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> bool:
        """비밀번호 변경"""
        user = self.get_user_by_id(user_id)

        if not user:
            return False

        if not self.verify_password(current_password, user.hashed_password):
            return False

        user.hashed_password = self.hash_password(new_password)
        user.updated_at = datetime.utcnow()

        return True

    async def deactivate_user(self, user_id: int) -> bool:
        """사용자 비활성화"""
        user = self.get_user_by_id(user_id)

        if not user:
            return False

        user.is_active = False
        user.updated_at = datetime.utcnow()

        return True

    def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """이메일로 사용자 조회"""
        return self._users.get(email)

    def get_user_by_id(self, user_id: int) -> Optional[UserInDB]:
        """ID로 사용자 조회"""
        for user in self._users.values():
            if user.id == user_id:
                return user
        return None

    async def get_all_users(self) -> list[User]:
        """모든 사용자 조회 (admin only)"""
        return [
            User(
                id=u.id,
                email=u.email,
                username=u.username,
                role=u.role,
                is_active=u.is_active,
                created_at=u.created_at,
                last_login=u.last_login
            )
            for u in self._users.values()
        ]


# Global auth service instance
auth_service = AuthService()
