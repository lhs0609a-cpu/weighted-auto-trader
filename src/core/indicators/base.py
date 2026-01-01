"""
지표 계산기 베이스
"""
from abc import ABC, abstractmethod
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class OHLCV:
    """OHLCV 데이터"""
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class IIndicator(ABC):
    """지표 계산기 인터페이스"""

    @property
    @abstractmethod
    def name(self) -> str:
        """지표명"""
        pass

    @abstractmethod
    def calculate(self, data: List[OHLCV]) -> Dict:
        """지표 계산"""
        pass
