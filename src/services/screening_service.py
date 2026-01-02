"""
스크리닝 서비스
- 조건별 종목 필터링
- 실시간 스크리닝
- 자동 종목 발굴
- 섹터별 분석
"""
from typing import Dict, List, Optional, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import asyncio

from ..config.constants import TradingStyle, DEFAULT_SCREENING_FILTERS, SignalType
from ..core.broker import IBrokerClient
from .analysis_service import AnalysisService


@dataclass
class WatchlistItem:
    """관심종목 항목"""
    stock_code: str
    stock_name: str
    added_at: datetime
    signal: SignalType
    score: float
    priority: int = 0  # 높을수록 우선순위


@dataclass
class SectorInfo:
    """섹터 정보"""
    sector_name: str
    stock_count: int
    avg_change_rate: float
    avg_score: float
    top_stocks: List[Dict] = field(default_factory=list)
    momentum: str = "neutral"  # bullish, bearish, neutral


class ScreeningService:
    """스크리닝 서비스"""

    def __init__(self, broker: IBrokerClient):
        self.broker = broker
        self.analysis_service = AnalysisService(broker)
        self._watchlist: Dict[str, WatchlistItem] = {}
        self._sector_cache: Dict[str, SectorInfo] = {}
        self._running = False
        self._callbacks: List[Callable] = []
        self._last_screen_time: Optional[datetime] = None
        self._discovered_stocks: Set[str] = set()

    async def screen_stocks(
        self,
        trading_style: TradingStyle,
        filters: Optional[Dict] = None,
        sort_by: str = "total_score",
        sort_order: str = "desc",
        limit: int = 20
    ) -> Dict:
        """
        종목 스크리닝

        Args:
            trading_style: 매매 스타일
            filters: 필터 조건
            sort_by: 정렬 기준
            sort_order: 정렬 순서 (asc/desc)
            limit: 최대 결과 수

        Returns:
            스크리닝 결과
        """
        # 필터 기본값 적용
        active_filters = {**DEFAULT_SCREENING_FILTERS}
        if filters:
            active_filters.update(filters)

        # 1. 종목 리스트 조회
        stock_list = await self.broker.get_stock_list()

        # 2. 기본 필터 적용 (시가총액 등)
        filtered_stocks = self._apply_basic_filters(stock_list, active_filters)

        # 3. 각 종목 분석 (병렬 처리)
        analysis_results = await self._analyze_stocks_parallel(
            filtered_stocks,
            trading_style,
            active_filters
        )

        # 4. 점수 필터 적용
        if 'score_min' in active_filters:
            analysis_results = [
                r for r in analysis_results
                if r['total_score'] >= active_filters['score_min']
            ]

        # 5. 정렬
        reverse = sort_order == "desc"
        analysis_results.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)

        # 6. 제한
        analysis_results = analysis_results[:limit]

        return {
            'total_count': len(analysis_results),
            'items': analysis_results,
            'filters': active_filters,
            'trading_style': trading_style.value,
            'screening_time': datetime.now().isoformat()
        }

    def _apply_basic_filters(self, stock_list: List[Dict], filters: Dict) -> List[Dict]:
        """기본 필터 적용"""
        filtered = []

        for stock in stock_list:
            market_cap = stock.get('market_cap', 0)

            # 시가총액 필터
            if 'market_cap_min' in filters and market_cap < filters['market_cap_min']:
                continue
            if 'market_cap_max' in filters and market_cap > filters['market_cap_max']:
                continue

            # 시장 필터
            if 'market' in filters and stock.get('market') != filters['market']:
                continue

            filtered.append(stock)

        return filtered

    async def _analyze_stocks_parallel(
        self,
        stocks: List[Dict],
        trading_style: TradingStyle,
        filters: Dict
    ) -> List[Dict]:
        """종목 병렬 분석"""
        async def analyze_single(stock: Dict) -> Optional[Dict]:
            try:
                result = await self.analysis_service.analyze_stock(
                    stock['code'],
                    trading_style
                )

                # 거래량/체결강도 필터
                indicators = result.get('indicators', {})
                volume_data = indicators.get('volume', {})
                order_book_data = indicators.get('order_book', {})

                volume_ratio = volume_data.get('volume_ratio', 0)
                strength = order_book_data.get('strength', 0)

                if 'volume_ratio_min' in filters and volume_ratio < filters['volume_ratio_min']:
                    return None
                if 'strength_min' in filters and strength < filters['strength_min']:
                    return None

                return {
                    'stock_code': result['stock_code'],
                    'stock_name': result['stock_name'],
                    'current_price': result['current_price'],
                    'change_rate': result['change_rate'],
                    'total_score': result['total_score'],
                    'signal': result['signal'],
                    'volume_ratio': volume_ratio,
                    'strength': strength,
                    'mandatory_passed': result['mandatory_check']['all_passed'],
                    'confidence': result['confidence']
                }
            except Exception as e:
                print(f"분석 오류 ({stock['code']}): {e}")
                return None

        # 병렬 실행
        tasks = [analyze_single(stock) for stock in stocks]
        results = await asyncio.gather(*tasks)

        # None 필터링
        return [r for r in results if r is not None]

    async def get_top_signals(
        self,
        trading_style: TradingStyle,
        signal_types: List[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """상위 신호 종목 조회"""
        if signal_types is None:
            signal_types = ['STRONG_BUY', 'BUY']

        result = await self.screen_stocks(
            trading_style=trading_style,
            filters={'volume_ratio_min': 150, 'strength_min': 100},
            sort_by='total_score',
            limit=50
        )

        # 신호 필터
        filtered = [
            item for item in result['items']
            if item['signal'] in signal_types
        ]

        return filtered[:limit]

    # === 자동 종목 발굴 ===

    async def auto_discover(
        self,
        trading_style: TradingStyle,
        max_stocks: int = 20
    ) -> List[Dict]:
        """
        자동 종목 발굴
        - 거래량 급증 종목
        - 신호 발생 종목
        - 섹터 모멘텀 종목
        """
        discovered = []

        # 1. 거래량 급증 종목
        volume_surge = await self._find_volume_surge_stocks(trading_style)
        discovered.extend(volume_surge[:max_stocks // 3])

        # 2. 강력 신호 종목
        strong_signals = await self.get_top_signals(
            trading_style,
            signal_types=['STRONG_BUY'],
            limit=max_stocks // 3
        )
        discovered.extend(strong_signals)

        # 3. 섹터 리더 종목
        sector_leaders = await self._find_sector_leaders(trading_style)
        discovered.extend(sector_leaders[:max_stocks // 3])

        # 중복 제거 및 점수순 정렬
        seen = set()
        unique = []
        for stock in discovered:
            if stock['stock_code'] not in seen:
                seen.add(stock['stock_code'])
                unique.append(stock)

        unique.sort(key=lambda x: x.get('total_score', 0), reverse=True)
        self._discovered_stocks = set(s['stock_code'] for s in unique)

        return unique[:max_stocks]

    async def _find_volume_surge_stocks(
        self,
        trading_style: TradingStyle,
        min_volume_ratio: float = 300,
        limit: int = 10
    ) -> List[Dict]:
        """거래량 급증 종목 발굴"""
        result = await self.screen_stocks(
            trading_style=trading_style,
            filters={
                'volume_ratio_min': min_volume_ratio,
                'strength_min': 100
            },
            sort_by='volume_ratio',
            sort_order='desc',
            limit=limit
        )
        return result['items']

    async def _find_sector_leaders(
        self,
        trading_style: TradingStyle,
        limit: int = 10
    ) -> List[Dict]:
        """섹터 리더 종목 발굴"""
        # 섹터 분석 후 각 섹터 상위 종목 추출
        sectors = await self.analyze_sectors(trading_style)
        leaders = []

        for sector in sectors:
            if sector.momentum == "bullish" and sector.top_stocks:
                leaders.extend(sector.top_stocks[:2])

        return leaders[:limit]

    # === 섹터 분석 ===

    async def analyze_sectors(
        self,
        trading_style: TradingStyle
    ) -> List[SectorInfo]:
        """섹터별 분석"""
        stock_list = await self.broker.get_stock_list()

        # 섹터별 그룹화
        sector_groups: Dict[str, List[Dict]] = {}
        for stock in stock_list:
            sector = stock.get('sector', '기타')
            if sector not in sector_groups:
                sector_groups[sector] = []
            sector_groups[sector].append(stock)

        # 섹터별 분석
        sector_infos = []
        for sector_name, stocks in sector_groups.items():
            if len(stocks) < 3:
                continue

            # 샘플링 분석 (성능 최적화)
            sample_stocks = stocks[:min(10, len(stocks))]
            analysis_results = await self._analyze_stocks_parallel(
                sample_stocks, trading_style, {}
            )

            if not analysis_results:
                continue

            avg_change = sum(s.get('change_rate', 0) for s in analysis_results) / len(analysis_results)
            avg_score = sum(s.get('total_score', 0) for s in analysis_results) / len(analysis_results)

            # 모멘텀 판단
            momentum = "neutral"
            if avg_change > 1 and avg_score > 70:
                momentum = "bullish"
            elif avg_change < -1 and avg_score < 40:
                momentum = "bearish"

            # 상위 종목
            top_stocks = sorted(
                analysis_results,
                key=lambda x: x.get('total_score', 0),
                reverse=True
            )[:3]

            sector_info = SectorInfo(
                sector_name=sector_name,
                stock_count=len(stocks),
                avg_change_rate=avg_change,
                avg_score=avg_score,
                top_stocks=top_stocks,
                momentum=momentum
            )
            sector_infos.append(sector_info)

        # 평균 점수순 정렬
        sector_infos.sort(key=lambda x: x.avg_score, reverse=True)
        self._sector_cache = {s.sector_name: s for s in sector_infos}

        return sector_infos

    def get_cached_sectors(self) -> List[SectorInfo]:
        """캐시된 섹터 정보 조회"""
        return list(self._sector_cache.values())

    # === 관심종목 관리 ===

    def add_to_watchlist(
        self,
        stock_code: str,
        stock_name: str,
        signal: SignalType,
        score: float,
        priority: int = 0
    ):
        """관심종목 추가"""
        self._watchlist[stock_code] = WatchlistItem(
            stock_code=stock_code,
            stock_name=stock_name,
            added_at=datetime.now(),
            signal=signal,
            score=score,
            priority=priority
        )

    def remove_from_watchlist(self, stock_code: str):
        """관심종목 제거"""
        if stock_code in self._watchlist:
            del self._watchlist[stock_code]

    def get_watchlist(self) -> List[WatchlistItem]:
        """관심종목 조회"""
        items = list(self._watchlist.values())
        items.sort(key=lambda x: (-x.priority, -x.score))
        return items

    def clear_watchlist(self):
        """관심종목 초기화"""
        self._watchlist.clear()

    # === 실시간 스크리닝 ===

    async def start_realtime_screening(
        self,
        trading_style: TradingStyle,
        interval_seconds: int = 60,
        callback: Optional[Callable] = None
    ):
        """실시간 스크리닝 시작"""
        self._running = True
        if callback:
            self._callbacks.append(callback)

        while self._running:
            try:
                # 스크리닝 실행
                result = await self.screen_stocks(
                    trading_style=trading_style,
                    filters={'volume_ratio_min': 200, 'strength_min': 105},
                    limit=30
                )

                self._last_screen_time = datetime.now()

                # 새로운 신호 감지
                new_signals = []
                for item in result['items']:
                    if item['signal'] in ['STRONG_BUY', 'BUY']:
                        if item['stock_code'] not in self._watchlist:
                            new_signals.append(item)
                            self.add_to_watchlist(
                                item['stock_code'],
                                item['stock_name'],
                                SignalType(item['signal']),
                                item['total_score']
                            )

                # 콜백 호출
                for cb in self._callbacks:
                    try:
                        await cb({
                            'type': 'screening_update',
                            'total_count': result['total_count'],
                            'new_signals': new_signals,
                            'timestamp': self._last_screen_time.isoformat()
                        })
                    except Exception as e:
                        print(f"콜백 오류: {e}")

                await asyncio.sleep(interval_seconds)

            except Exception as e:
                print(f"실시간 스크리닝 오류: {e}")
                await asyncio.sleep(5)

    def stop_realtime_screening(self):
        """실시간 스크리닝 중지"""
        self._running = False
        self._callbacks.clear()

    def register_callback(self, callback: Callable):
        """콜백 등록"""
        self._callbacks.append(callback)

    # === 스크리닝 프리셋 ===

    def get_preset_filters(self, preset_name: str) -> Dict:
        """프리셋 필터 조회"""
        presets = {
            'volume_surge': {
                'volume_ratio_min': 300,
                'strength_min': 110,
                'score_min': 60
            },
            'strong_buy': {
                'volume_ratio_min': 150,
                'strength_min': 120,
                'score_min': 80
            },
            'scalping': {
                'volume_ratio_min': 200,
                'strength_min': 130,
                'score_min': 75,
                'market_cap_max': 5000000000000  # 5조 이하
            },
            'swing': {
                'volume_ratio_min': 100,
                'strength_min': 100,
                'score_min': 65,
                'market_cap_min': 1000000000000  # 1조 이상
            },
            'recovery': {
                'change_rate_min': -3,
                'change_rate_max': 0,
                'volume_ratio_min': 150,
                'score_min': 60
            }
        }
        return presets.get(preset_name, {})

    async def screen_with_preset(
        self,
        trading_style: TradingStyle,
        preset_name: str,
        limit: int = 20
    ) -> Dict:
        """프리셋으로 스크리닝"""
        filters = self.get_preset_filters(preset_name)
        return await self.screen_stocks(
            trading_style=trading_style,
            filters=filters,
            limit=limit
        )

    # === 히스토리 & 통계 ===

    def get_screening_stats(self) -> Dict:
        """스크리닝 통계"""
        watchlist = self.get_watchlist()
        signal_counts = {}
        for item in watchlist:
            signal = item.signal.value
            signal_counts[signal] = signal_counts.get(signal, 0) + 1

        return {
            'watchlist_count': len(watchlist),
            'signal_counts': signal_counts,
            'discovered_count': len(self._discovered_stocks),
            'sector_count': len(self._sector_cache),
            'last_screen_time': self._last_screen_time.isoformat() if self._last_screen_time else None,
            'is_running': self._running
        }
