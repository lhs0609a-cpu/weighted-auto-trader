"""
WeightedAutoTrader FastAPI 애플리케이션
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config.settings import get_settings
from .api.routes import (
    stocks_router,
    signals_router,
    portfolio_router,
    backtest_router,
    settings_router,
    trades_router,
    auto_trader_router
)
from .api.websocket import websocket_router
from .auth.routes import router as auth_router
from .services import get_auto_trader

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 라이프사이클 관리"""
    # Startup
    print("[App] 서버 시작 중...")

    # 자동매매 설정이 활성화되어 있으면 자동 시작
    if settings.auto_trade_enabled:
        try:
            trader = get_auto_trader()
            await trader.start()
            print("[App] 자동매매 시작됨")
        except Exception as e:
            print(f"[App] 자동매매 시작 실패: {e}")

    yield

    # Shutdown
    print("[App] 서버 종료 중...")

    # 자동매매 중지
    try:
        trader = get_auto_trader()
        if trader._running:
            await trader.stop()
            print("[App] 자동매매 중지됨")
    except Exception as e:
        print(f"[App] 자동매매 중지 실패: {e}")


# FastAPI 앱 생성
app = FastAPI(
    title="WeightedAutoTrader API",
    description="가중치 기반 자동매매 시스템 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
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
app.include_router(auth_router, prefix="/api/v1")
app.include_router(stocks_router, prefix="/api/v1")
app.include_router(signals_router, prefix="/api/v1")
app.include_router(portfolio_router, prefix="/api/v1")
app.include_router(backtest_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")
app.include_router(trades_router, prefix="/api/v1")
app.include_router(auto_trader_router, prefix="/api/v1")
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
