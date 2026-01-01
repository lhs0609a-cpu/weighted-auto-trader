"""
스크리닝 서비스
- 조건별 종목 필터링
- 실시간 스크리닝
"""
from typing import Dict, List, Optional
from datetime import datetime
import asyncio

from ..config.constants import TradingStyle, DEFAULT_SCREENING_FILTERS
from ..core.broker import IBrokerClient
from .analysis_service import AnalysisService


class ScreeningService:
    """스크리닝 서비스"""

    def __init__(self, broker: IBrokerClient):
        self.broker = broker
        self.analysis_service = AnalysisService(broker)

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
