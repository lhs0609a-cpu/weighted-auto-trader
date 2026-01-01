"""
시장 분석기
- 시장 전체 흐름 분석
- 업종별 분석
- 시장 지표 산출
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ...core.broker.interfaces import IBrokerClient, Quote


class MarketCondition(str, Enum):
    """시장 상황"""
    STRONG_BULLISH = "STRONG_BULLISH"
    BULLISH = "BULLISH"
    NEUTRAL = "NEUTRAL"
    BEARISH = "BEARISH"
    STRONG_BEARISH = "STRONG_BEARISH"


@dataclass
class MarketSummary:
    """시장 요약"""
    condition: MarketCondition
    kospi_change_rate: float
    kosdaq_change_rate: float
    advance_count: int
    decline_count: int
    unchanged_count: int
    total_volume: int
    foreign_net_buy: float
    institution_net_buy: float
    score: float
    analysis: str
    timestamp: datetime


@dataclass
class SectorAnalysis:
    """업종 분석"""
    sector_name: str
    change_rate: float
    volume_ratio: float
    top_gainers: List[Dict]
    top_losers: List[Dict]
    strength: str


class MarketAnalyzer:
    """시장 분석기"""

    def __init__(self, broker: IBrokerClient):
        self.broker = broker

    async def analyze_market(self) -> MarketSummary:
        """시장 전체 분석"""
        # 전 종목 시세 조회
        stocks = await self.broker.get_stock_list()

        # 등락 통계
        advances = 0
        declines = 0
        unchanged = 0
        total_volume = 0

        for stock in stocks:
            change_rate = stock.get('change_rate', 0)
            if change_rate > 0:
                advances += 1
            elif change_rate < 0:
                declines += 1
            else:
                unchanged += 1
            total_volume += stock.get('volume', 0)

        # 등락비율로 시장 상황 판단
        total = advances + declines + unchanged
        if total == 0:
            total = 1

        advance_ratio = advances / total * 100

        # 시장 상황 판단
        if advance_ratio >= 70:
            condition = MarketCondition.STRONG_BULLISH
            score = 90
        elif advance_ratio >= 55:
            condition = MarketCondition.BULLISH
            score = 70
        elif advance_ratio >= 45:
            condition = MarketCondition.NEUTRAL
            score = 50
        elif advance_ratio >= 30:
            condition = MarketCondition.BEARISH
            score = 30
        else:
            condition = MarketCondition.STRONG_BEARISH
            score = 10

        # 분석 코멘트
        analysis = self._generate_market_comment(condition, advance_ratio, advances, declines)

        return MarketSummary(
            condition=condition,
            kospi_change_rate=0,
            kosdaq_change_rate=0,
            advance_count=advances,
            decline_count=declines,
            unchanged_count=unchanged,
            total_volume=total_volume,
            foreign_net_buy=0,
            institution_net_buy=0,
            score=score,
            analysis=analysis,
            timestamp=datetime.now()
        )

    def _generate_market_comment(
        self,
        condition: MarketCondition,
        advance_ratio: float,
        advances: int,
        declines: int
    ) -> str:
        """시장 분석 코멘트 생성"""
        comments = {
            MarketCondition.STRONG_BULLISH: (
                f"강한 상승장입니다. 상승 {advances}종목 vs 하락 {declines}종목으로 "
                f"상승비율 {advance_ratio:.1f}%입니다. 적극적 매수 검토 가능합니다."
            ),
            MarketCondition.BULLISH: (
                f"상승 우위 장세입니다. 상승 {advances}종목 vs 하락 {declines}종목입니다. "
                f"개별 종목 선별 매수가 유리합니다."
            ),
            MarketCondition.NEUTRAL: (
                f"보합 장세입니다. 상승 {advances}종목, 하락 {declines}종목으로 혼조세입니다. "
                f"방향성 확인 후 진입을 권장합니다."
            ),
            MarketCondition.BEARISH: (
                f"하락 우위 장세입니다. 하락 {declines}종목이 상승 {advances}종목보다 많습니다. "
                f"신규 매수는 신중하게 접근하세요."
            ),
            MarketCondition.STRONG_BEARISH: (
                f"강한 하락장입니다. 상승비율 {advance_ratio:.1f}%로 대부분 종목이 하락 중입니다. "
                f"매수 보다는 관망을 권장합니다."
            )
        }
        return comments.get(condition, "시장 분석 중...")

    async def analyze_sectors(self) -> List[SectorAnalysis]:
        """업종별 분석"""
        stocks = await self.broker.get_stock_list()

        # 업종별 그룹화 (간단한 예시)
        sectors = {}
        for stock in stocks:
            sector = stock.get('sector', '기타')
            if sector not in sectors:
                sectors[sector] = []
            sectors[sector].append(stock)

        results = []
        for sector_name, sector_stocks in sectors.items():
            if not sector_stocks:
                continue

            # 평균 등락률
            avg_change = sum(s.get('change_rate', 0) for s in sector_stocks) / len(sector_stocks)

            # 거래량 비율
            avg_volume_ratio = sum(s.get('volume_ratio', 100) for s in sector_stocks) / len(sector_stocks)

            # 상승/하락 상위
            sorted_stocks = sorted(sector_stocks, key=lambda x: x.get('change_rate', 0), reverse=True)
            top_gainers = sorted_stocks[:3]
            top_losers = sorted_stocks[-3:]

            # 업종 강도
            if avg_change >= 2:
                strength = "강세"
            elif avg_change >= 0:
                strength = "보합"
            else:
                strength = "약세"

            results.append(SectorAnalysis(
                sector_name=sector_name,
                change_rate=round(avg_change, 2),
                volume_ratio=round(avg_volume_ratio, 1),
                top_gainers=top_gainers,
                top_losers=top_losers,
                strength=strength
            ))

        # 등락률 기준 정렬
        results.sort(key=lambda x: x.change_rate, reverse=True)

        return results

    async def get_top_stocks(self, count: int = 20) -> Dict[str, List[Dict]]:
        """상위 종목 조회"""
        stocks = await self.broker.get_stock_list()

        # 등락률 상위
        by_change = sorted(stocks, key=lambda x: x.get('change_rate', 0), reverse=True)

        # 거래량 상위
        by_volume = sorted(stocks, key=lambda x: x.get('volume', 0), reverse=True)

        # 거래대금 상위
        by_amount = sorted(stocks, key=lambda x: x.get('trade_amount', 0), reverse=True)

        return {
            "top_gainers": by_change[:count],
            "top_losers": by_change[-count:],
            "top_volume": by_volume[:count],
            "top_amount": by_amount[:count]
        }

    def is_trading_favorable(self, market_summary: MarketSummary) -> bool:
        """매매 유리 여부 판단"""
        return market_summary.condition in [
            MarketCondition.STRONG_BULLISH,
            MarketCondition.BULLISH
        ]
