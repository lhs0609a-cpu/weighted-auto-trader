"""
한국투자증권 (KIS) API 클라이언트
- OAuth2 인증 및 토큰 관리
- REST API를 통한 시세 조회 및 주문 실행
- WebSocket을 통한 실시간 시세 수신

API 문서: https://apiportal.koreainvestment.com
"""
import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass

from .interfaces import (
    IBrokerClient, Quote, OHLCV, OrderBook, OrderResult,
    Balance, HoldingStock, OrderType, OrderSide
)

logger = logging.getLogger(__name__)


# =============================================================================
# 데이터 클래스
# =============================================================================

@dataclass
class KISToken:
    """KIS API 토큰 정보"""
    access_token: str
    token_type: str
    expires_at: datetime

    @property
    def is_expired(self) -> bool:
        """토큰 만료 여부 (5분 여유)"""
        return datetime.now() >= self.expires_at - timedelta(minutes=5)


@dataclass
class InvestorData:
    """투자자별 매매동향"""
    date: str
    close_price: float
    change: float
    change_sign: str
    prsn_ntby_qty: int      # 개인 순매수수량
    prsn_ntby_tr_pbmn: int  # 개인 순매수대금
    frgn_ntby_qty: int      # 외국인 순매수수량
    frgn_ntby_tr_pbmn: int  # 외국인 순매수대금
    orgn_ntby_qty: int      # 기관 순매수수량
    orgn_ntby_tr_pbmn: int  # 기관 순매수대금


@dataclass
class VolumeRankItem:
    """거래량 순위 종목"""
    rank: int
    stock_code: str
    stock_name: str
    price: float
    change: float
    change_rate: float
    change_sign: str
    volume: int
    prev_volume: int
    volume_rate: float      # 전일대비 거래량 비율
    turnover_rate: float    # 회전율
    trade_amount: int       # 거래대금


@dataclass
class ExecutionData:
    """체결 데이터"""
    time: str
    price: float
    change: float
    change_sign: str
    change_rate: float
    volume: int
    strength: float         # 체결강도


# =============================================================================
# TR ID 상수
# =============================================================================

class TRID:
    """한국투자증권 API TR ID (실전투자)"""

    # ========== 시세 조회 (국내주식 기본시세) ==========
    QUOTE_PRICE = "FHKST01010100"           # 주식현재가 시세
    QUOTE_ASKING = "FHKST01010200"          # 주식현재가 호가/예상체결
    QUOTE_CCNL = "FHKST01010300"            # 주식현재가 체결
    QUOTE_DAILY = "FHKST01010400"           # 주식현재가 일자별
    QUOTE_TIME = "FHPST01060000"            # 주식현재가 당일시간대별체결
    QUOTE_MEMBER = "FHKST01010600"          # 주식현재가 회원사
    QUOTE_INVESTOR = "FHKST01010900"        # 주식현재가 투자자

    # 시간외
    QUOTE_OVERTIME = "FHPST02300000"        # 시간외현재가
    QUOTE_OVERTIME_ASKING = "FHPST02300400" # 시간외호가
    QUOTE_OVERTIME_TIME = "FHPST02310000"   # 시간외시간별체결
    QUOTE_OVERTIME_DAILY = "FHPST02320000"  # 시간외일자별주가

    # 차트 데이터
    OHLCV_DAILY = "FHKST03010100"           # 국내주식기간별시세(일/주/월/년)
    OHLCV_MINUTE = "FHKST03010200"          # 주식당일분봉조회
    OHLCV_MINUTE_DAILY = "FHKST03010230"    # 주식일별분봉조회

    # ETF/ETN
    ETF_PRICE = "FHPST02400000"             # ETF/ETN 현재가
    ETF_COMPONENT = "FHKST121600C0"         # ETF 구성종목시세
    ETF_NAV_TREND = "FHPST02440000"         # NAV 비교추이

    # ========== 순위분석 ==========
    RANK_VOLUME = "FHPST01710000"           # 거래량순위
    RANK_FLUCTUATION = "FHPST01740000"      # 등락률순위
    RANK_MARKET_CAP = "FHPST01770000"       # 시가총액순위
    RANK_TRADE_AMOUNT = "FHPST01780000"     # 거래대금순위
    RANK_CREDIT = "FHKST66410100"           # 신용잔고순위
    RANK_SHORT = "FHKST66420100"            # 공매도순위
    RANK_EXEC_STRENGTH = "FHPST01630000"    # 체결강도순위
    RANK_FOREIGN_HOLD = "FHPST01650000"     # 외국인보유순위

    # ========== 시세분석 ==========
    INVESTOR_TREND_DAILY = "FHKST01011100"  # 종목별 투자자매매동향(일별)
    INVESTOR_TREND_TICK = "FHKST01011200"   # 종목별 투자자매매동향(시세)
    FOREIGN_TREND = "FHKST01011500"         # 외국계 순매수추이
    PROGRAM_TREND = "FHKST01011600"         # 프로그램매매추이
    SHORT_TREND = "FHKST66420000"           # 공매도 일별추이
    CREDIT_TREND = "FHKST66410000"          # 신용잔고 일별추이

    # ========== 업종/기타 ==========
    SECTOR_DAILY = "FHKUP03500100"          # 업종기간별시세
    SECTOR_INDEX = "FHPUP02100000"          # 업종현재지수
    SECTOR_INVESTOR = "FHPTJ04010000"       # 업종별 투자자매매동향
    HOLIDAY = "CTCA0903R"                   # 국내휴장일조회

    # ========== 종목정보 ==========
    STOCK_INFO = "CTPF1002R"                # 주식기본조회
    STOCK_FINANCE = "FHKST67100100"         # 재무비율
    STOCK_CONSENSUS = "FHKST67000100"       # 종목투자의견

    # ========== 주문/계좌 ==========
    ORDER_BUY = "TTTC0012U"                 # 현금 매수
    ORDER_SELL = "TTTC0011U"                # 현금 매도
    ORDER_MODIFY = "TTTC0013U"              # 주문 정정/취소
    ORDER_CREDIT_BUY = "TTTC0052U"          # 신용 매수
    ORDER_CREDIT_SELL = "TTTC0051U"         # 신용 매도
    ORDER_RESV = "CTSC0008U"                # 예약주문
    ORDER_RESV_CANCEL = "CTSC0009U"         # 예약주문 취소

    # 조회
    BALANCE = "TTTC8434R"                   # 주식잔고조회
    BALANCE_REALIZED = "TTTC8494R"          # 주식잔고조회(실현손익)
    PSBL_ORDER = "TTTC8908R"                # 매수가능조회
    PSBL_SELL = "TTTC8408R"                 # 매도가능수량조회
    PSBL_CREDIT = "TTTC8909R"               # 신용매수가능조회
    ORDER_HISTORY = "TTTC0081R"             # 주식일별주문체결조회(3개월이내)
    ORDER_HISTORY_OLD = "CTSC9215R"         # 주식일별주문체결조회(3개월이전)
    PSBL_RVSECNCL = "TTTC0084R"             # 정정취소가능주문조회
    PERIOD_PROFIT = "TTTC8715R"             # 기간별매매손익현황

    # ========== 실시간 (WebSocket) ==========
    WS_STOCK_EXEC = "H0STCNT0"              # 실시간 체결가 (KRX)
    WS_STOCK_ASKING = "H0STASP0"            # 실시간 호가 (KRX)
    WS_STOCK_NOTICE = "H0STCNI0"            # 실시간 체결통보
    WS_STOCK_EXEC_NXT = "H0STCNT1"          # 실시간 체결가 (NXT)
    WS_STOCK_ASKING_NXT = "H0STASP1"        # 실시간 호가 (NXT)
    WS_INDEX_EXEC = "H0UPCNT0"              # 업종지수 실시간체결
    WS_PROGRAM = "H0UPPGMT"                 # 실시간 프로그램매매
    WS_FUTURES_EXEC = "H0IFCNT0"            # 지수선물 실시간체결
    WS_FUTURES_ASKING = "H0IFASP0"          # 지수선물 실시간호가
    WS_OPTIONS_EXEC = "H0IOCNT0"            # 지수옵션 실시간체결


# =============================================================================
# KIS 클라이언트
# =============================================================================

class KISClient(IBrokerClient):
    """한국투자증권 API 클라이언트 (실전투자)"""

    BASE_URL = "https://openapi.koreainvestment.com:9443"
    WS_URL = "ws://ops.koreainvestment.com:21000"

    def __init__(
        self,
        app_key: str,
        app_secret: str,
        account_no: str
    ):
        """
        KIS 클라이언트 초기화

        Args:
            app_key: 앱 키
            app_secret: 앱 시크릿
            account_no: 계좌번호 (8자리-2자리 형식)
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.account_no = account_no

        # 계좌번호 파싱
        if "-" in account_no:
            self.cano, self.acnt_prdt_cd = account_no.split("-")
        else:
            self.cano = account_no[:8]
            self.acnt_prdt_cd = account_no[8:10] if len(account_no) >= 10 else "01"

        # 토큰 관리
        self._token: Optional[KISToken] = None
        self._ws_approval_key: Optional[str] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._connected = False

        # WebSocket 콜백
        self._ws_callbacks: Dict[str, List[Callable]] = {}
        self._ws_subscriptions: Dict[str, set] = {}
        self._ws_task: Optional[asyncio.Task] = None

        # 캐시
        self._stock_info_cache: Dict[str, Dict] = {}
        self._hashkey_cache: Dict[str, str] = {}

    # =========================================================================
    # 연결 관리
    # =========================================================================

    async def connect(self) -> bool:
        """API 연결 및 토큰 발급"""
        try:
            if self._session is None or self._session.closed:
                timeout = aiohttp.ClientTimeout(total=30)
                self._session = aiohttp.ClientSession(timeout=timeout)

            await self._get_access_token()

            self._connected = True
            logger.info("KIS API 연결 성공")
            return True

        except Exception as e:
            logger.error(f"KIS API 연결 실패: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """연결 해제"""
        if self._ws_task:
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass

        if self._ws and not self._ws.closed:
            await self._ws.close()

        if self._session and not self._session.closed:
            await self._session.close()

        self._connected = False
        self._ws_subscriptions.clear()
        logger.info("KIS API 연결 해제")

    @property
    def is_connected(self) -> bool:
        """연결 상태"""
        return self._connected and self._token is not None and not self._token.is_expired

    # =========================================================================
    # OAuth 인증
    # =========================================================================

    async def _get_access_token(self) -> str:
        """OAuth 토큰 발급/갱신"""
        if self._token and not self._token.is_expired:
            return self._token.access_token

        url = f"{self.BASE_URL}/oauth2/tokenP"
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }

        async with self._session.post(url, headers=headers, json=body) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"토큰 발급 실패: {resp.status} - {text}")

            data = await resp.json()

            if "access_token" not in data:
                raise Exception(f"토큰 응답 오류: {data}")

            expires_in = int(data.get("expires_in", 86400))
            self._token = KISToken(
                access_token=data["access_token"],
                token_type=data.get("token_type", "Bearer"),
                expires_at=datetime.now() + timedelta(seconds=expires_in)
            )

            logger.info(f"KIS 토큰 발급 완료 (만료: {self._token.expires_at})")
            return self._token.access_token

    async def revoke_token(self) -> bool:
        """토큰 폐기"""
        if not self._token:
            return True

        url = f"{self.BASE_URL}/oauth2/revokeP"
        headers = {"content-type": "application/json"}
        body = {
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "token": self._token.access_token
        }

        try:
            async with self._session.post(url, headers=headers, json=body) as resp:
                self._token = None
                return resp.status == 200
        except Exception as e:
            logger.error(f"토큰 폐기 실패: {e}")
            return False

    async def _get_ws_approval_key(self) -> str:
        """WebSocket 접속키 발급"""
        if self._ws_approval_key:
            return self._ws_approval_key

        url = f"{self.BASE_URL}/oauth2/Approval"
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "secretkey": self.app_secret
        }

        async with self._session.post(url, headers=headers, json=body) as resp:
            data = await resp.json()
            self._ws_approval_key = data.get("approval_key", "")
            return self._ws_approval_key

    async def _get_hashkey(self, body: Dict) -> str:
        """해시키 생성 (POST 요청용)"""
        cache_key = json.dumps(body, sort_keys=True)
        if cache_key in self._hashkey_cache:
            return self._hashkey_cache[cache_key]

        url = f"{self.BASE_URL}/uapi/hashkey"
        headers = {
            "content-type": "application/json",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }

        async with self._session.post(url, headers=headers, json=body) as resp:
            data = await resp.json()
            hashkey = data.get("HASH", "")
            self._hashkey_cache[cache_key] = hashkey
            return hashkey

    # =========================================================================
    # HTTP 요청 유틸리티
    # =========================================================================

    def _get_headers(self, tr_id: str) -> Dict[str, str]:
        """API 요청 헤더 생성"""
        return {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self._token.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
            "custtype": "P",
        }

    async def _request(
        self,
        method: str,
        path: str,
        tr_id: str,
        params: Dict = None,
        body: Dict = None
    ) -> Dict:
        """API 요청 실행"""
        await self._get_access_token()

        url = f"{self.BASE_URL}{path}"
        headers = self._get_headers(tr_id)

        if method == "POST" and body:
            headers["hashkey"] = await self._get_hashkey(body)

        try:
            if method == "GET":
                async with self._session.get(url, headers=headers, params=params) as resp:
                    return await self._handle_response(resp, tr_id)
            else:
                async with self._session.post(url, headers=headers, json=body) as resp:
                    return await self._handle_response(resp, tr_id)

        except aiohttp.ClientError as e:
            logger.error(f"API 요청 실패 [{tr_id}]: {e}")
            raise

    async def _handle_response(self, resp: aiohttp.ClientResponse, tr_id: str = "") -> Dict:
        """응답 처리"""
        data = await resp.json()

        rt_cd = data.get("rt_cd")
        if rt_cd and rt_cd != "0":
            msg = data.get("msg1", "알 수 없는 오류")
            msg_cd = data.get("msg_cd", "")
            logger.warning(f"API 오류 [{tr_id}][{msg_cd}]: {msg}")
            raise Exception(f"API 오류 [{msg_cd}]: {msg}")

        return data

    # =========================================================================
    # 시세 조회 - 현재가
    # =========================================================================

    async def get_quote(self, stock_code: str, market: str = "J") -> Quote:
        """
        현재가 조회

        Args:
            stock_code: 종목코드
            market: J(KRX), NX(NXT), UN(통합)
        """
        path = "/uapi/domestic-stock/v1/quotations/inquire-price"
        params = {
            "FID_COND_MRKT_DIV_CODE": market,
            "FID_INPUT_ISCD": stock_code
        }

        data = await self._request("GET", path, TRID.QUOTE_PRICE, params=params)
        output = data.get("output", {})

        return Quote(
            stock_code=stock_code,
            name=output.get("rprs_mrkt_kor_name", output.get("stck_shrn_iscd", stock_code)),
            price=float(output.get("stck_prpr", 0)),
            change=float(output.get("prdy_vrss", 0)),
            change_rate=float(output.get("prdy_ctrt", 0)),
            volume=int(output.get("acml_vol", 0)),
            trade_amount=int(output.get("acml_tr_pbmn", 0)),
            open=float(output.get("stck_oprc", 0)),
            high=float(output.get("stck_hgpr", 0)),
            low=float(output.get("stck_lwpr", 0)),
            prev_close=float(output.get("stck_sdpr", 0)),
            timestamp=datetime.now(),
            extra={
                "per": float(output.get("per", 0)),
                "pbr": float(output.get("pbr", 0)),
                "eps": float(output.get("eps", 0)),
                "bps": float(output.get("bps", 0)),
                "market_cap": int(output.get("hts_avls", 0)) * 100000000,
                "foreign_ratio": float(output.get("hts_frgn_ehrt", 0)),
                "d250_high": float(output.get("d250_hgpr", 0)),
                "d250_low": float(output.get("d250_lwpr", 0)),
                "w52_high": float(output.get("w52_hgpr", 0)),
                "w52_low": float(output.get("w52_lwpr", 0)),
            }
        )

    async def get_quotes(self, stock_codes: List[str]) -> List[Quote]:
        """복수 종목 현재가 조회"""
        tasks = [self.get_quote(code) for code in stock_codes]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        quotes = []
        for result in results:
            if isinstance(result, Quote):
                quotes.append(result)
            else:
                logger.warning(f"시세 조회 실패: {result}")

        return quotes

    # =========================================================================
    # 시세 조회 - 호가
    # =========================================================================

    async def get_orderbook(self, stock_code: str, market: str = "J") -> OrderBook:
        """호가 조회 (10단계)"""
        path = "/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn"
        params = {
            "FID_COND_MRKT_DIV_CODE": market,
            "FID_INPUT_ISCD": stock_code
        }

        data = await self._request("GET", path, TRID.QUOTE_ASKING, params=params)
        output1 = data.get("output1", {})
        output2 = data.get("output2", {})

        ask_prices = [float(output1.get(f"askp{i}", 0)) for i in range(1, 11)]
        ask_volumes = [int(output1.get(f"askp_rsqn{i}", 0)) for i in range(1, 11)]
        bid_prices = [float(output1.get(f"bidp{i}", 0)) for i in range(1, 11)]
        bid_volumes = [int(output1.get(f"bidp_rsqn{i}", 0)) for i in range(1, 11)]

        return OrderBook(
            stock_code=stock_code,
            ask_prices=ask_prices,
            ask_volumes=ask_volumes,
            bid_prices=bid_prices,
            bid_volumes=bid_volumes,
            total_ask_volume=int(output1.get("total_askp_rsqn", 0)),
            total_bid_volume=int(output1.get("total_bidp_rsqn", 0)),
            timestamp=datetime.now(),
            extra={
                "antc_cnpr": float(output2.get("antc_cnpr", 0)),
                "antc_cntg_vrss": float(output2.get("antc_cntg_vrss", 0)),
                "antc_cntg_prdy_ctrt": float(output2.get("antc_cntg_prdy_ctrt", 0)),
                "antc_vol": int(output2.get("antc_vol", 0)),
            }
        )

    # =========================================================================
    # 시세 조회 - 체결
    # =========================================================================

    async def get_execution_data(self, stock_code: str, market: str = "J") -> List[ExecutionData]:
        """체결 데이터 조회"""
        path = "/uapi/domestic-stock/v1/quotations/inquire-ccnl"
        params = {
            "FID_COND_MRKT_DIV_CODE": market,
            "FID_INPUT_ISCD": stock_code
        }

        data = await self._request("GET", path, TRID.QUOTE_CCNL, params=params)

        executions = []
        for item in data.get("output", []):
            executions.append(ExecutionData(
                time=item.get("stck_cntg_hour", ""),
                price=float(item.get("stck_prpr", 0)),
                change=float(item.get("prdy_vrss", 0)),
                change_sign=item.get("prdy_vrss_sign", "3"),
                change_rate=float(item.get("prdy_ctrt", 0)),
                volume=int(item.get("cntg_vol", 0)),
                strength=float(item.get("tday_rltv", 100))
            ))

        return executions

    async def get_execution_strength(self, stock_code: str) -> Dict:
        """체결강도 조회"""
        executions = await self.get_execution_data(stock_code)

        if not executions:
            return {
                "stock_code": stock_code,
                "strength": 100.0,
                "buy_volume": 0,
                "sell_volume": 0,
                "timestamp": datetime.now()
            }

        latest = executions[0]
        return {
            "stock_code": stock_code,
            "strength": latest.strength,
            "price": latest.price,
            "change_rate": latest.change_rate,
            "timestamp": datetime.now()
        }

    # =========================================================================
    # 시세 조회 - 투자자
    # =========================================================================

    async def get_investor_trend(self, stock_code: str, market: str = "J") -> List[InvestorData]:
        """투자자별 매매동향 조회"""
        path = "/uapi/domestic-stock/v1/quotations/inquire-investor"
        params = {
            "FID_COND_MRKT_DIV_CODE": market,
            "FID_INPUT_ISCD": stock_code
        }

        data = await self._request("GET", path, TRID.QUOTE_INVESTOR, params=params)

        trends = []
        for item in data.get("output", []):
            trends.append(InvestorData(
                date=item.get("stck_bsop_date", ""),
                close_price=float(item.get("stck_clpr", 0)),
                change=float(item.get("prdy_vrss", 0)),
                change_sign=item.get("prdy_vrss_sign", "3"),
                prsn_ntby_qty=int(item.get("prsn_ntby_qty", 0)),
                prsn_ntby_tr_pbmn=int(item.get("prsn_ntby_tr_pbmn", 0)),
                frgn_ntby_qty=int(item.get("frgn_ntby_qty", 0)),
                frgn_ntby_tr_pbmn=int(item.get("frgn_ntby_tr_pbmn", 0)),
                orgn_ntby_qty=int(item.get("orgn_ntby_qty", 0)),
                orgn_ntby_tr_pbmn=int(item.get("orgn_ntby_tr_pbmn", 0))
            ))

        return trends

    # =========================================================================
    # 시세 조회 - OHLCV
    # =========================================================================

    async def get_ohlcv(
        self,
        stock_code: str,
        period: str = "D",
        count: int = 100,
        adj_price: bool = True
    ) -> List[OHLCV]:
        """
        OHLCV 데이터 조회

        Args:
            stock_code: 종목코드
            period: D(일), W(주), M(월), Y(년)
            count: 조회 개수
            adj_price: 수정주가 적용 여부
        """
        ohlcv_list = []

        if period in ["D", "W", "M", "Y"]:
            path = "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
            params = {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": stock_code,
                "FID_INPUT_DATE_1": (datetime.now() - timedelta(days=365*3)).strftime("%Y%m%d"),
                "FID_INPUT_DATE_2": datetime.now().strftime("%Y%m%d"),
                "FID_PERIOD_DIV_CODE": period,
                "FID_ORG_ADJ_PRC": "0" if adj_price else "1",
            }

            data = await self._request("GET", path, TRID.OHLCV_DAILY, params=params)

            for item in data.get("output2", [])[:count]:
                try:
                    ohlcv_list.append(OHLCV(
                        timestamp=datetime.strptime(item["stck_bsop_date"], "%Y%m%d"),
                        open=float(item.get("stck_oprc", 0)),
                        high=float(item.get("stck_hgpr", 0)),
                        low=float(item.get("stck_lwpr", 0)),
                        close=float(item.get("stck_clpr", 0)),
                        volume=int(item.get("acml_vol", 0))
                    ))
                except (KeyError, ValueError) as e:
                    logger.warning(f"OHLCV 파싱 오류: {e}")
        else:
            path = "/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice"
            params = {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": stock_code,
                "FID_INPUT_HOUR_1": datetime.now().strftime("%H%M%S"),
                "FID_PW_DATA_INCU_YN": "Y",
            }

            data = await self._request("GET", path, TRID.OHLCV_MINUTE, params=params)

            for item in data.get("output2", [])[:count]:
                try:
                    date_str = item.get("stck_bsop_date", "")
                    time_str = item.get("stck_cntg_hour", "")
                    if date_str and time_str:
                        timestamp = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
                    else:
                        continue

                    ohlcv_list.append(OHLCV(
                        timestamp=timestamp,
                        open=float(item.get("stck_oprc", 0)),
                        high=float(item.get("stck_hgpr", 0)),
                        low=float(item.get("stck_lwpr", 0)),
                        close=float(item.get("stck_prpr", 0)),
                        volume=int(item.get("cntg_vol", 0))
                    ))
                except (KeyError, ValueError) as e:
                    logger.warning(f"분봉 파싱 오류: {e}")

        return ohlcv_list

    async def get_minute_ohlcv(
        self,
        stock_code: str,
        date: str = None,
        count: int = 100
    ) -> List[OHLCV]:
        """분봉 데이터 조회 (특정 일자)"""
        if date is None:
            return await self.get_ohlcv(stock_code, period="1", count=count)

        path = "/uapi/domestic-stock/v1/quotations/inquire-time-dailychartprice"
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": stock_code,
            "FID_INPUT_DATE_1": date,
            "FID_INPUT_HOUR_1": "090000",
            "FID_PW_DATA_INCU_YN": "Y",
        }

        data = await self._request("GET", path, TRID.OHLCV_MINUTE_DAILY, params=params)

        ohlcv_list = []
        for item in data.get("output2", [])[:count]:
            try:
                date_str = item.get("stck_bsop_date", "")
                time_str = item.get("stck_cntg_hour", "")
                if date_str and time_str:
                    timestamp = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
                else:
                    continue

                ohlcv_list.append(OHLCV(
                    timestamp=timestamp,
                    open=float(item.get("stck_oprc", 0)),
                    high=float(item.get("stck_hgpr", 0)),
                    low=float(item.get("stck_lwpr", 0)),
                    close=float(item.get("stck_prpr", 0)),
                    volume=int(item.get("cntg_vol", 0))
                ))
            except (KeyError, ValueError) as e:
                logger.warning(f"분봉 파싱 오류: {e}")

        return ohlcv_list

    # =========================================================================
    # 순위 조회
    # =========================================================================

    async def get_volume_rank(
        self,
        market: str = "J",
        target_cls: str = "111111111",
        exclude_cls: str = "000000",
        min_price: int = 0,
        max_price: int = 0,
        min_volume: int = 0
    ) -> List[VolumeRankItem]:
        """거래량 순위 조회"""
        path = "/uapi/domestic-stock/v1/quotations/volume-rank"
        params = {
            "FID_COND_MRKT_DIV_CODE": market,
            "FID_COND_SCR_DIV_CODE": "20171",
            "FID_INPUT_ISCD": "0000",
            "FID_DIV_CLS_CODE": "0",
            "FID_BLNG_CLS_CODE": "0",
            "FID_TRGT_CLS_CODE": target_cls,
            "FID_TRGT_EXLS_CLS_CODE": exclude_cls,
            "FID_INPUT_PRICE_1": str(min_price),
            "FID_INPUT_PRICE_2": str(max_price),
            "FID_VOL_CNT": str(min_volume),
            "FID_INPUT_DATE_1": "0",
        }

        data = await self._request("GET", path, TRID.RANK_VOLUME, params=params)

        ranks = []
        for item in data.get("output", []):
            ranks.append(VolumeRankItem(
                rank=int(item.get("data_rank", 0)),
                stock_code=item.get("mksc_shrn_iscd", ""),
                stock_name=item.get("hts_kor_isnm", ""),
                price=float(item.get("stck_prpr", 0)),
                change=float(item.get("prdy_vrss", 0)),
                change_rate=float(item.get("prdy_ctrt", 0)),
                change_sign=item.get("prdy_vrss_sign", "3"),
                volume=int(item.get("acml_vol", 0)),
                prev_volume=int(item.get("prdy_vol", 0)),
                volume_rate=float(item.get("vol_inrt", 0)),
                turnover_rate=float(item.get("vol_tnrt", 0)),
                trade_amount=int(item.get("acml_tr_pbmn", 0))
            ))

        return ranks

    async def get_fluctuation_rank(
        self,
        market: str = "J",
        direction: str = "up",
        period: str = "0"
    ) -> List[Dict]:
        """등락률 순위 조회"""
        path = "/uapi/domestic-stock/v1/quotations/fluctuation-rank"
        params = {
            "FID_COND_MRKT_DIV_CODE": market,
            "FID_COND_SCR_DIV_CODE": "20174",
            "FID_INPUT_ISCD": "0000",
            "FID_RANK_SORT_CLS_CODE": "0" if direction == "up" else "1",
            "FID_INPUT_CNT_1": "0",
            "FID_PRC_CLS_CODE": "0",
            "FID_INPUT_PRICE_1": "0",
            "FID_INPUT_PRICE_2": "0",
            "FID_VOL_CNT": "0",
            "FID_TRGT_CLS_CODE": "0",
            "FID_TRGT_EXLS_CLS_CODE": "0",
            "FID_DIV_CLS_CODE": period,
            "FID_RSFL_RATE1": "0",
            "FID_RSFL_RATE2": "0",
        }

        data = await self._request("GET", path, TRID.RANK_FLUCTUATION, params=params)
        return data.get("output", [])

    # =========================================================================
    # 계좌 조회
    # =========================================================================

    async def get_balance(self) -> Balance:
        """잔고 조회"""
        path = "/uapi/domestic-stock/v1/trading/inquire-balance"
        params = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "00",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }

        data = await self._request("GET", path, TRID.BALANCE, params=params)
        output2 = data.get("output2", [{}])[0] if data.get("output2") else {}

        return Balance(
            total_asset=float(output2.get("tot_evlu_amt", 0)),
            available_cash=float(output2.get("dnca_tot_amt", 0)),
            total_purchase=float(output2.get("pchs_amt_smtl_amt", 0)),
            total_evaluation=float(output2.get("evlu_amt_smtl_amt", 0)),
            total_pnl=float(output2.get("evlu_pfls_smtl_amt", 0)),
            total_pnl_rate=float(output2.get("tot_evlu_pfls_rt", 0)) if output2.get("tot_evlu_pfls_rt") else 0
        )

    async def get_positions(self) -> List[HoldingStock]:
        """보유 종목 조회"""
        path = "/uapi/domestic-stock/v1/trading/inquire-balance"
        params = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "00",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }

        data = await self._request("GET", path, TRID.BALANCE, params=params)

        positions = []
        for item in data.get("output1", []):
            quantity = int(item.get("hldg_qty", 0))
            if quantity <= 0:
                continue

            positions.append(HoldingStock(
                stock_code=item.get("pdno", ""),
                stock_name=item.get("prdt_name", ""),
                quantity=quantity,
                avg_price=float(item.get("pchs_avg_pric", 0)),
                current_price=float(item.get("prpr", 0)),
                evaluation=float(item.get("evlu_amt", 0)),
                pnl=float(item.get("evlu_pfls_amt", 0)),
                pnl_rate=float(item.get("evlu_pfls_rt", 0))
            ))

        return positions

    async def get_buyable_amount(
        self,
        stock_code: str,
        order_type: str = "01",
        price: int = 0
    ) -> Dict:
        """매수가능 조회"""
        path = "/uapi/domestic-stock/v1/trading/inquire-psbl-order"
        params = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "PDNO": stock_code,
            "ORD_UNPR": str(price),
            "ORD_DVSN": order_type,
            "CMA_EVLU_AMT_ICLD_YN": "N",
            "OVRS_ICLD_YN": "N"
        }

        data = await self._request("GET", path, TRID.PSBL_ORDER, params=params)
        output = data.get("output", {})

        return {
            "ord_psbl_cash": int(output.get("ord_psbl_cash", 0)),
            "nrcvb_buy_amt": int(output.get("nrcvb_buy_amt", 0)),
            "nrcvb_buy_qty": int(output.get("nrcvb_buy_qty", 0)),
            "max_buy_amt": int(output.get("max_buy_amt", 0)),
            "max_buy_qty": int(output.get("max_buy_qty", 0)),
            "psbl_qty_calc_unpr": int(output.get("psbl_qty_calc_unpr", 0)),
        }

    # =========================================================================
    # 주문
    # =========================================================================

    async def place_order(
        self,
        stock_code: str,
        order_side: OrderSide,
        order_type: OrderType,
        quantity: int,
        price: Optional[float] = None
    ) -> OrderResult:
        """주문 실행"""
        path = "/uapi/domestic-stock/v1/trading/order-cash"

        tr_id = TRID.ORDER_BUY if order_side == OrderSide.BUY else TRID.ORDER_SELL

        if order_type == OrderType.MARKET:
            ord_dvsn = "01"
            order_price = 0
        else:
            ord_dvsn = "00"
            order_price = int(price) if price else 0

        body = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "PDNO": stock_code,
            "ORD_DVSN": ord_dvsn,
            "ORD_QTY": str(quantity),
            "ORD_UNPR": str(order_price),
        }

        try:
            data = await self._request("POST", path, tr_id, body=body)
            output = data.get("output", {})

            return OrderResult(
                order_id=output.get("ODNO", ""),
                stock_code=stock_code,
                order_side=order_side,
                order_type=order_type,
                order_price=price or 0,
                order_qty=quantity,
                executed_price=None,
                executed_qty=0,
                status="SUBMITTED",
                message=data.get("msg1", "주문 접수")
            )

        except Exception as e:
            return OrderResult(
                order_id="",
                stock_code=stock_code,
                order_side=order_side,
                order_type=order_type,
                order_price=price or 0,
                order_qty=quantity,
                executed_price=None,
                executed_qty=0,
                status="REJECTED",
                message=str(e)
            )

    async def cancel_order(
        self,
        order_id: str,
        quantity: int = 0,
        price: int = 0,
        cancel_all: bool = True
    ) -> bool:
        """주문 취소"""
        path = "/uapi/domestic-stock/v1/trading/order-rvsecncl"
        body = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "KRX_FWDG_ORD_ORGNO": "",
            "ORGN_ODNO": order_id,
            "ORD_DVSN": "00",
            "RVSE_CNCL_DVSN_CD": "02",
            "ORD_QTY": "0" if cancel_all else str(quantity),
            "ORD_UNPR": str(price),
            "QTY_ALL_ORD_YN": "Y" if cancel_all else "N",
        }

        try:
            await self._request("POST", path, TRID.ORDER_MODIFY, body=body)
            return True
        except Exception as e:
            logger.error(f"주문 취소 실패: {e}")
            return False

    async def modify_order(
        self,
        order_id: str,
        quantity: int,
        price: int
    ) -> bool:
        """주문 정정"""
        path = "/uapi/domestic-stock/v1/trading/order-rvsecncl"
        body = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "KRX_FWDG_ORD_ORGNO": "",
            "ORGN_ODNO": order_id,
            "ORD_DVSN": "00",
            "RVSE_CNCL_DVSN_CD": "01",
            "ORD_QTY": str(quantity),
            "ORD_UNPR": str(price),
            "QTY_ALL_ORD_YN": "N",
        }

        try:
            await self._request("POST", path, TRID.ORDER_MODIFY, body=body)
            return True
        except Exception as e:
            logger.error(f"주문 정정 실패: {e}")
            return False

    async def get_order_history(
        self,
        start_date: str = None,
        end_date: str = None,
        order_type: str = "00"
    ) -> List[Dict]:
        """주문 체결 내역 조회"""
        path = "/uapi/domestic-stock/v1/trading/inquire-daily-ccld"

        if start_date is None:
            start_date = datetime.now().strftime("%Y%m%d")
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")

        params = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "INQR_STRT_DT": start_date,
            "INQR_END_DT": end_date,
            "SLL_BUY_DVSN_CD": order_type,
            "INQR_DVSN": "00",
            "PDNO": "",
            "CCLD_DVSN": "00",
            "ORD_GNO_BRNO": "",
            "ODNO": "",
            "INQR_DVSN_3": "00",
            "INQR_DVSN_1": "",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }

        data = await self._request("GET", path, TRID.ORDER_HISTORY, params=params)
        return data.get("output1", [])

    # =========================================================================
    # 종목 정보
    # =========================================================================

    async def get_stock_info(self, stock_code: str) -> Dict:
        """종목 기본 정보 조회"""
        quote = await self.get_quote(stock_code)
        return {
            "stock_code": stock_code,
            "stock_name": quote.name,
            "market_cap": quote.extra.get("market_cap", 0),
            "per": quote.extra.get("per", 0),
            "pbr": quote.extra.get("pbr", 0),
            "eps": quote.extra.get("eps", 0),
            "bps": quote.extra.get("bps", 0),
        }

    async def get_stock_list(self, market: str = None) -> List[Dict]:
        """종목 리스트 조회"""
        stocks = [
            {"code": "005930", "name": "삼성전자", "market": "KOSPI"},
            {"code": "000660", "name": "SK하이닉스", "market": "KOSPI"},
            {"code": "035420", "name": "NAVER", "market": "KOSPI"},
            {"code": "035720", "name": "카카오", "market": "KOSPI"},
            {"code": "005380", "name": "현대차", "market": "KOSPI"},
            {"code": "051910", "name": "LG화학", "market": "KOSPI"},
            {"code": "006400", "name": "삼성SDI", "market": "KOSPI"},
            {"code": "068270", "name": "셀트리온", "market": "KOSPI"},
            {"code": "373220", "name": "LG에너지솔루션", "market": "KOSPI"},
            {"code": "207940", "name": "삼성바이오로직스", "market": "KOSPI"},
            {"code": "005490", "name": "POSCO홀딩스", "market": "KOSPI"},
            {"code": "055550", "name": "신한지주", "market": "KOSPI"},
            {"code": "105560", "name": "KB금융", "market": "KOSPI"},
            {"code": "012330", "name": "현대모비스", "market": "KOSPI"},
            {"code": "066570", "name": "LG전자", "market": "KOSPI"},
            {"code": "003550", "name": "LG", "market": "KOSPI"},
            {"code": "034730", "name": "SK", "market": "KOSPI"},
            {"code": "018260", "name": "삼성에스디에스", "market": "KOSPI"},
            {"code": "017670", "name": "SK텔레콤", "market": "KOSPI"},
            {"code": "028260", "name": "삼성물산", "market": "KOSPI"},
        ]

        if market:
            stocks = [s for s in stocks if s["market"] == market]

        return stocks

    # =========================================================================
    # WebSocket 실시간
    # =========================================================================

    async def connect_websocket(self) -> bool:
        """WebSocket 연결"""
        try:
            if self._session is None:
                self._session = aiohttp.ClientSession()

            self._ws = await self._session.ws_connect(self.WS_URL)
            self._ws_task = asyncio.create_task(self._ws_receiver())

            logger.info("KIS WebSocket 연결 성공")
            return True

        except Exception as e:
            logger.error(f"WebSocket 연결 실패: {e}")
            return False

    async def disconnect_websocket(self) -> None:
        """WebSocket 연결 해제"""
        if self._ws_task:
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass

        if self._ws and not self._ws.closed:
            await self._ws.close()

        self._ws_subscriptions.clear()
        logger.info("KIS WebSocket 연결 해제")

    async def _ws_receiver(self):
        """WebSocket 메시지 수신"""
        try:
            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self._handle_ws_message(msg.data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket 오류: {msg.data}")
                    break
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"WebSocket 수신 오류: {e}")

    async def _handle_ws_message(self, data: str):
        """WebSocket 메시지 처리"""
        try:
            if data[0] in ('0', '1'):
                parts = data.split("|")
                if len(parts) < 4:
                    return

                tr_id = parts[1]
                body = parts[3]

                if tr_id in self._ws_callbacks:
                    parsed = self._parse_realtime_data(tr_id, body)
                    if parsed:
                        for callback in self._ws_callbacks[tr_id]:
                            try:
                                await callback(parsed)
                            except Exception as e:
                                logger.error(f"콜백 처리 오류: {e}")
            else:
                response = json.loads(data)
                if response.get("header", {}).get("tr_id"):
                    tr_id = response["header"]["tr_id"]
                    logger.debug(f"WebSocket 응답 [{tr_id}]: {response}")

        except Exception as e:
            logger.error(f"메시지 파싱 오류: {e}")

    def _parse_realtime_data(self, tr_id: str, data: str) -> Optional[Dict]:
        """실시간 데이터 파싱"""
        try:
            fields = data.split("^")

            if tr_id == TRID.WS_STOCK_EXEC:
                if len(fields) < 20:
                    return None
                return {
                    "type": "execution",
                    "stock_code": fields[0],
                    "time": fields[1],
                    "price": float(fields[2]),
                    "change_sign": fields[3],
                    "change": float(fields[4]),
                    "change_rate": float(fields[5]),
                    "weighted_avg_price": float(fields[6]),
                    "open": float(fields[7]),
                    "high": float(fields[8]),
                    "low": float(fields[9]),
                    "ask_price": float(fields[10]),
                    "bid_price": float(fields[11]),
                    "exec_volume": int(fields[12]),
                    "total_volume": int(fields[13]),
                    "total_amount": int(fields[14]),
                    "exec_count": int(fields[16]),
                    "strength": float(fields[17]) if len(fields) > 17 else 100.0,
                }

            elif tr_id == TRID.WS_STOCK_ASKING:
                if len(fields) < 43:
                    return None

                return {
                    "type": "orderbook",
                    "stock_code": fields[0],
                    "time": fields[1],
                    "ask_prices": [float(fields[i]) for i in range(3, 13)],
                    "ask_volumes": [int(fields[i]) for i in range(23, 33)],
                    "bid_prices": [float(fields[i]) for i in range(13, 23)],
                    "bid_volumes": [int(fields[i]) for i in range(33, 43)],
                    "total_ask_volume": sum(int(fields[i]) for i in range(23, 33)),
                    "total_bid_volume": sum(int(fields[i]) for i in range(33, 43)),
                }

            elif tr_id == TRID.WS_STOCK_NOTICE:
                return {
                    "type": "notice",
                    "raw": fields,
                }

            return None

        except Exception as e:
            logger.error(f"실시간 데이터 파싱 오류 [{tr_id}]: {e}")
            return None

    async def subscribe_execution(
        self,
        stock_codes: List[str],
        callback: Callable[[Dict], Any]
    ):
        """실시간 체결가 구독"""
        tr_id = TRID.WS_STOCK_EXEC

        if not self._ws:
            await self.connect_websocket()

        if tr_id not in self._ws_callbacks:
            self._ws_callbacks[tr_id] = []
        self._ws_callbacks[tr_id].append(callback)

        approval_key = await self._get_ws_approval_key()

        for code in stock_codes:
            if tr_id not in self._ws_subscriptions:
                self._ws_subscriptions[tr_id] = set()

            if code in self._ws_subscriptions[tr_id]:
                continue

            request = {
                "header": {
                    "approval_key": approval_key,
                    "custtype": "P",
                    "tr_type": "1",
                    "content-type": "utf-8"
                },
                "body": {
                    "input": {
                        "tr_id": tr_id,
                        "tr_key": code
                    }
                }
            }

            await self._ws.send_json(request)
            self._ws_subscriptions[tr_id].add(code)
            logger.debug(f"실시간 체결가 구독: {code}")

    async def subscribe_orderbook(
        self,
        stock_codes: List[str],
        callback: Callable[[Dict], Any]
    ):
        """실시간 호가 구독"""
        tr_id = TRID.WS_STOCK_ASKING

        if not self._ws:
            await self.connect_websocket()

        if tr_id not in self._ws_callbacks:
            self._ws_callbacks[tr_id] = []
        self._ws_callbacks[tr_id].append(callback)

        approval_key = await self._get_ws_approval_key()

        for code in stock_codes:
            if tr_id not in self._ws_subscriptions:
                self._ws_subscriptions[tr_id] = set()

            if code in self._ws_subscriptions[tr_id]:
                continue

            request = {
                "header": {
                    "approval_key": approval_key,
                    "custtype": "P",
                    "tr_type": "1",
                    "content-type": "utf-8"
                },
                "body": {
                    "input": {
                        "tr_id": tr_id,
                        "tr_key": code
                    }
                }
            }

            await self._ws.send_json(request)
            self._ws_subscriptions[tr_id].add(code)
            logger.debug(f"실시간 호가 구독: {code}")

    async def subscribe_notice(self, callback: Callable[[Dict], Any]):
        """실시간 체결통보 구독 (내 주문 체결 알림)"""
        tr_id = TRID.WS_STOCK_NOTICE

        if not self._ws:
            await self.connect_websocket()

        if tr_id not in self._ws_callbacks:
            self._ws_callbacks[tr_id] = []
        self._ws_callbacks[tr_id].append(callback)

        approval_key = await self._get_ws_approval_key()

        request = {
            "header": {
                "approval_key": approval_key,
                "custtype": "P",
                "tr_type": "1",
                "content-type": "utf-8"
            },
            "body": {
                "input": {
                    "tr_id": tr_id,
                    "tr_key": self.account_no
                }
            }
        }

        await self._ws.send_json(request)
        logger.info("실시간 체결통보 구독 완료")

    async def unsubscribe(self, tr_id: str, stock_codes: List[str] = None):
        """실시간 구독 해제"""
        if not self._ws:
            return

        approval_key = await self._get_ws_approval_key()
        codes_to_unsub = stock_codes or list(self._ws_subscriptions.get(tr_id, set()))

        for code in codes_to_unsub:
            request = {
                "header": {
                    "approval_key": approval_key,
                    "custtype": "P",
                    "tr_type": "2",
                    "content-type": "utf-8"
                },
                "body": {
                    "input": {
                        "tr_id": tr_id,
                        "tr_key": code
                    }
                }
            }

            await self._ws.send_json(request)

            if tr_id in self._ws_subscriptions:
                self._ws_subscriptions[tr_id].discard(code)

        logger.debug(f"실시간 구독 해제 [{tr_id}]: {codes_to_unsub}")

    async def subscribe_realtime(
        self,
        stock_codes: List[str],
        callback: Callable[[str, Dict], Any]
    ):
        """실시간 시세 구독 (레거시 호환)"""
        async def wrapped_callback(data: Dict):
            stock_code = data.get("stock_code", "")
            await callback(stock_code, data)

        await self.subscribe_execution(stock_codes, wrapped_callback)
