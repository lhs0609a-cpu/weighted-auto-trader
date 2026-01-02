"""
API 라우트 패키지
"""
from .stocks import router as stocks_router
from .signals import router as signals_router
from .portfolio import router as portfolio_router
from .backtest import router as backtest_router
from .settings import router as settings_router
from .trades import router as trades_router
from .auto_trader import router as auto_trader_router

__all__ = [
    "stocks_router",
    "signals_router",
    "portfolio_router",
    "backtest_router",
    "settings_router",
    "trades_router",
    "auto_trader_router",
]
