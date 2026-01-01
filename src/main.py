"""
WeightedAutoTrader FastAPI 애플리케이션
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config.settings import get_settings
from .api.routes import stocks_router, signals_router, portfolio_router
from .api.websocket import websocket_router

settings = get_settings()

# FastAPI 앱 생성
app = FastAPI(
    title="WeightedAutoTrader API",
    description="가중치 기반 자동매매 시스템 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경에서는 모든 origin 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(stocks_router, prefix="/api/v1")
app.include_router(signals_router, prefix="/api/v1")
app.include_router(portfolio_router, prefix="/api/v1")
app.include_router(websocket_router, prefix="/api/v1")


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "name": "WeightedAutoTrader API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "env": settings.app_env
    }


@app.get("/api/v1/trading-styles")
async def get_trading_styles():
    """매매 스타일 목록"""
    return {
        "success": True,
        "data": [
            {
                "value": "SCALPING",
                "label": "스캘핑",
                "description": "1분봉 기반 초단타 매매"
            },
            {
                "value": "DAYTRADING",
                "label": "단타",
                "description": "5분봉 기반 당일 매매"
            },
            {
                "value": "SWING",
                "label": "스윙",
                "description": "일봉 기반 며칠간 보유"
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
