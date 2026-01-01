// 매매 스타일
export type TradingStyle = "SCALPING" | "DAYTRADING" | "SWING";

// 신호 타입
export type SignalType = "STRONG_BUY" | "BUY" | "WATCH" | "HOLD" | "SELL";

// 종목 시세
export interface Quote {
  stock_code: string;
  name: string;
  price: number;
  change: number;
  change_rate: number;
  volume: number;
  high: number;
  low: number;
  open: number;
  prev_close: number;
  timestamp: string;
}

// 분석 결과
export interface AnalysisResult {
  stock_code: string;
  stock_name: string;
  current_price: number;
  change: number;
  change_rate: number;
  signal: SignalType;
  total_score: number;
  confidence: number;
  reasons: string[];
  trade_params: TradeParams;
  indicators: Record<string, any>;
  timestamp: string;
}

// 매매 파라미터
export interface TradeParams {
  action: string;
  entry_price?: number;
  stop_loss?: number;
  stop_loss_pct?: number;
  take_profit_1?: number;
  take_profit_1_pct?: number;
  take_profit_2?: number;
  take_profit_2_pct?: number;
  trailing_stop_pct?: number;
  position_size_pct?: number;
}

// 포지션
export interface Position {
  position_id: string;
  stock_code: string;
  stock_name: string;
  quantity: number;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  status: string;
}

// 주문
export interface Order {
  order_id: string;
  stock_code: string;
  stock_name: string;
  order_side: "BUY" | "SELL";
  order_type: "MARKET" | "LIMIT";
  order_price: number;
  order_quantity: number;
  executed_price: number;
  executed_quantity: number;
  status: string;
  created_at: string;
}

// API 응답
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

// WebSocket 메시지
export interface WSMessage {
  type: string;
  [key: string]: any;
}

// 시장 상황
export type MarketCondition =
  | "STRONG_BULLISH"
  | "BULLISH"
  | "NEUTRAL"
  | "BEARISH"
  | "STRONG_BEARISH";

// 통계
export interface Statistics {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  avg_pnl: number;
  max_profit: number;
  max_loss: number;
}
