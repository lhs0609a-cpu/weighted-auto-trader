"""
백테스팅 API 라우터
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from ...core.backtesting import (
    BacktestEngine,
    BacktestConfig,
    BacktestDataLoader,
    ResultAnalyzer
)
from ...config.constants import TradingStyle

router = APIRouter(prefix="/backtest", tags=["Backtest"])


class BacktestRequest(BaseModel):
    """백테스트 요청"""
    stock_codes: List[str] = Field(..., description="종목 코드 리스트")
    start_date: str = Field(..., description="시작일 (YYYY-MM-DD)")
    end_date: str = Field(..., description="종료일 (YYYY-MM-DD)")
    initial_capital: float = Field(default=10_000_000, description="초기 자본")
    trading_style: str = Field(default="DAYTRADING", description="매매 스타일")
    commission_rate: float = Field(default=0.00015, description="수수료율")
    slippage_rate: float = Field(default=0.001, description="슬리피지")
    max_position_size: float = Field(default=0.2, description="최대 포지션 크기")
    max_positions: int = Field(default=5, description="최대 동시 포지션")
    use_trailing_stop: bool = Field(default=True, description="트레일링 스탑 사용")
    trailing_stop_pct: float = Field(default=0.02, description="트레일링 스탑 비율")


class BacktestStatus(BaseModel):
    """백테스트 상태"""
    backtest_id: str
    status: str
    progress: float
    message: str


# 진행 중인 백테스트 저장소
_backtest_tasks = {}
_backtest_results = {}


@router.post("/run", response_model=dict)
async def run_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    """
    백테스트 실행

    - 백그라운드에서 백테스트 실행
    - backtest_id를 반환하여 상태 조회 가능
    """
    import uuid

    backtest_id = str(uuid.uuid4())[:8]

    # 매매 스타일 변환
    try:
        trading_style = TradingStyle(request.trading_style)
    except ValueError:
        trading_style = TradingStyle.DAYTRADING

    # 설정 생성
    config = BacktestConfig(
        initial_capital=request.initial_capital,
        trading_style=trading_style,
        commission_rate=request.commission_rate,
        slippage_rate=request.slippage_rate,
        max_position_size=request.max_position_size,
        max_positions=request.max_positions,
        use_trailing_stop=request.use_trailing_stop,
        trailing_stop_pct=request.trailing_stop_pct
    )

    # 초기 상태 설정
    _backtest_tasks[backtest_id] = {
        "status": "running",
        "progress": 0,
        "message": "백테스트 시작..."
    }

    # 백그라운드에서 실행
    background_tasks.add_task(
        _run_backtest_task,
        backtest_id,
        request.stock_codes,
        request.start_date,
        request.end_date,
        config
    )

    return {
        "success": True,
        "backtest_id": backtest_id,
        "message": "백테스트가 시작되었습니다"
    }


async def _run_backtest_task(
    backtest_id: str,
    stock_codes: List[str],
    start_date: str,
    end_date: str,
    config: BacktestConfig
):
    """백테스트 실행 태스크"""
    try:
        data_loader = BacktestDataLoader()
        engine = BacktestEngine(config, data_loader)

        # 날짜 파싱
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        # 모의 데이터 생성 (실제로는 외부 데이터 로드)
        for code in stock_codes:
            mock_data = data_loader.generate_mock_data(
                stock_code=code,
                stock_name=code,
                start_date=start_dt,
                end_date=end_dt,
                initial_price=50000,
                volatility=0.02,
                trend=0.0001
            )
            data_loader.save_ohlcv(code, mock_data)

        # 진행률 콜백
        async def progress_callback(data):
            _backtest_tasks[backtest_id] = {
                "status": "running",
                "progress": data['progress'] * 100,
                "message": f"처리 중: {data['date']}"
            }

        # 백테스트 실행
        result = await engine.run(
            stock_codes=stock_codes,
            start_date=start_dt,
            end_date=end_dt,
            progress_callback=progress_callback
        )

        # 결과 분석
        if 'error' not in result:
            analyzer = ResultAnalyzer()
            analysis = analyzer.analyze(result)
            result['analysis'] = {
                'sharpe_ratio': analysis.sharpe_ratio,
                'sortino_ratio': analysis.sortino_ratio,
                'calmar_ratio': analysis.calmar_ratio,
                'annualized_return': analysis.annualized_return,
                'monthly_return': analysis.monthly_return
            }

        # 결과 저장
        _backtest_results[backtest_id] = result
        _backtest_tasks[backtest_id] = {
            "status": "completed",
            "progress": 100,
            "message": "백테스트 완료"
        }

    except Exception as e:
        _backtest_tasks[backtest_id] = {
            "status": "failed",
            "progress": 0,
            "message": f"오류 발생: {str(e)}"
        }


@router.get("/status/{backtest_id}", response_model=BacktestStatus)
async def get_backtest_status(backtest_id: str):
    """백테스트 상태 조회"""
    if backtest_id not in _backtest_tasks:
        raise HTTPException(status_code=404, detail="백테스트를 찾을 수 없습니다")

    task = _backtest_tasks[backtest_id]
    return BacktestStatus(
        backtest_id=backtest_id,
        status=task["status"],
        progress=task["progress"],
        message=task["message"]
    )


@router.get("/result/{backtest_id}")
async def get_backtest_result(backtest_id: str):
    """백테스트 결과 조회"""
    if backtest_id not in _backtest_results:
        if backtest_id in _backtest_tasks:
            task = _backtest_tasks[backtest_id]
            if task["status"] == "running":
                return {
                    "success": False,
                    "message": "백테스트가 아직 진행 중입니다",
                    "progress": task["progress"]
                }
            elif task["status"] == "failed":
                return {
                    "success": False,
                    "message": task["message"]
                }
        raise HTTPException(status_code=404, detail="백테스트 결과를 찾을 수 없습니다")

    return {
        "success": True,
        "data": _backtest_results[backtest_id]
    }


@router.post("/quick-run")
async def quick_backtest(request: BacktestRequest):
    """
    즉시 백테스트 실행 (동기)

    - 결과를 즉시 반환
    - 소규모 테스트에 적합
    """
    try:
        # 매매 스타일 변환
        try:
            trading_style = TradingStyle(request.trading_style)
        except ValueError:
            trading_style = TradingStyle.DAYTRADING

        config = BacktestConfig(
            initial_capital=request.initial_capital,
            trading_style=trading_style,
            commission_rate=request.commission_rate,
            slippage_rate=request.slippage_rate,
            max_position_size=request.max_position_size,
            max_positions=request.max_positions,
            use_trailing_stop=request.use_trailing_stop,
            trailing_stop_pct=request.trailing_stop_pct
        )

        data_loader = BacktestDataLoader()
        engine = BacktestEngine(config, data_loader)

        start_dt = datetime.strptime(request.start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(request.end_date, "%Y-%m-%d")

        # 모의 데이터 생성
        for code in request.stock_codes:
            mock_data = data_loader.generate_mock_data(
                stock_code=code,
                stock_name=code,
                start_date=start_dt,
                end_date=end_dt,
                initial_price=50000,
                volatility=0.02,
                trend=0.0001
            )
            data_loader.save_ohlcv(code, mock_data)

        result = await engine.run(
            stock_codes=request.stock_codes,
            start_date=start_dt,
            end_date=end_dt
        )

        if 'error' in result:
            return {"success": False, "message": result['error']}

        return {"success": True, "data": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_backtests():
    """완료된 백테스트 목록 조회"""
    backtests = []
    for backtest_id, task in _backtest_tasks.items():
        backtests.append({
            "backtest_id": backtest_id,
            "status": task["status"],
            "progress": task["progress"],
            "has_result": backtest_id in _backtest_results
        })

    return {
        "success": True,
        "data": backtests
    }
