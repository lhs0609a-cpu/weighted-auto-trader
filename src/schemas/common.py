"""
공통 스키마
"""
from typing import Any, Optional, List
from pydantic import BaseModel


class APIResponse(BaseModel):
    """API 응답 스키마"""
    success: bool
    data: Optional[Any] = None
    error: Optional[dict] = None


class ErrorResponse(BaseModel):
    """에러 응답 스키마"""
    code: str
    message: str
    detail: Optional[str] = None


class PaginatedResponse(BaseModel):
    """페이지네이션 응답"""
    total_count: int
    items: List[Any]
    page: int = 1
    page_size: int = 20
