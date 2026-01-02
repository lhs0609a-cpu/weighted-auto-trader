"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { Quote, AnalysisResult, IndicatorData, SignalType, ChartData } from "@/types";
import { stocksApi, signalsApi } from "@/lib/api";
import { useWebSocket } from "@/hooks/useWebSocket";
import { CandlestickChart } from "@/components/Chart";

interface PageProps {
  params: Promise<{ code: string }>;
}

const signalConfig: Record<
  SignalType,
  { gradient: string; label: string; icon: string }
> = {
  STRONG_BUY: {
    gradient: "from-rose-500 to-orange-500",
    label: "Strong Buy",
    icon: "fire",
  },
  BUY: { gradient: "from-orange-500 to-amber-500", label: "Buy", icon: "up" },
  WATCH: {
    gradient: "from-amber-500 to-yellow-500",
    label: "Watch",
    icon: "eye",
  },
  HOLD: { gradient: "from-slate-400 to-slate-500", label: "Hold", icon: "pause" },
  SELL: { gradient: "from-blue-500 to-cyan-500", label: "Sell", icon: "down" },
};

interface NewsItem {
  id: string;
  title: string;
  source: string;
  time: string;
  sentiment: "positive" | "negative" | "neutral";
  url?: string;
}

// Generate mock news for demo
const generateMockNews = (stockName: string): NewsItem[] => [
  {
    id: "1",
    title: `${stockName}, 4분기 실적 시장 예상치 상회...영업이익 증가`,
    source: "한국경제",
    time: "10분 전",
    sentiment: "positive",
  },
  {
    id: "2",
    title: `외국인 투자자 ${stockName} 대규모 순매수...3거래일 연속`,
    source: "매일경제",
    time: "32분 전",
    sentiment: "positive",
  },
  {
    id: "3",
    title: `증권가 "${stockName} 목표가 상향"...신규 사업 기대감`,
    source: "서울경제",
    time: "1시간 전",
    sentiment: "positive",
  },
  {
    id: "4",
    title: `${stockName} 글로벌 경쟁 심화 우려...원자재 비용 상승`,
    source: "조선비즈",
    time: "2시간 전",
    sentiment: "negative",
  },
  {
    id: "5",
    title: `${stockName} 신규 투자 계획 발표...연내 생산시설 확대`,
    source: "연합뉴스",
    time: "3시간 전",
    sentiment: "neutral",
  },
];

// Generate mock chart data
const generateMockChartData = (basePrice: number, days: number = 60): ChartData[] => {
  const data: ChartData[] = [];
  let price = basePrice * 0.9;

  for (let i = days; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);

    const change = (Math.random() - 0.48) * price * 0.03;
    const open = price;
    price = Math.max(price * 0.9, price + change);
    const close = price;
    const high = Math.max(open, close) * (1 + Math.random() * 0.015);
    const low = Math.min(open, close) * (1 - Math.random() * 0.015);
    const volume = Math.floor(Math.random() * 10000000) + 1000000;

    data.push({
      timestamp: date.toISOString(),
      open: Math.round(open),
      high: Math.round(high),
      low: Math.round(low),
      close: Math.round(close),
      volume,
    });
  }

  return data;
};

export default function StockDetailPage({ params }: PageProps) {
  const { code } = use(params);
  const [quote, setQuote] = useState<Quote | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [indicators, setIndicators] = useState<IndicatorData[]>([]);
  const [chartData, setChartData] = useState<ChartData[]>([]);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"analysis" | "chart" | "news">("analysis");
  const [chartPeriod, setChartPeriod] = useState<"D" | "W" | "M">("D");

  // WebSocket for real-time updates
  const { isConnected, subscribe } = useWebSocket({
    onMessage: (message) => {
      if (message.type === "stock_update" && message.data?.stock_code === code) {
        setQuote((prev) => (prev ? { ...prev, ...message.data } : null));
      }
    },
  });

  const getStockName = (code: string) => {
    const names: Record<string, string> = {
      "005930": "삼성전자",
      "000660": "SK하이닉스",
      "035720": "카카오",
      "035420": "NAVER",
      "051910": "LG화학",
      "006400": "삼성SDI",
      "003670": "포스코퓨처엠",
      "373220": "LG에너지솔루션",
    };
    return names[code] || code;
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        // Load stock detail
        const stockResponse = await stocksApi.getDetail(code);
        if (stockResponse.success && stockResponse.data) {
          setQuote(stockResponse.data);
        } else {
          // Fallback mock data
          setQuote({
            stock_code: code,
            name: getStockName(code),
            price: 72500,
            change: 1500,
            change_rate: 2.11,
            volume: 15234567,
            high: 73000,
            low: 71500,
            open: 71800,
            prev_close: 71000,
            timestamp: new Date().toISOString(),
          });
        }

        // Load analysis
        const analysisResponse = await signalsApi.analyze(code, "DAYTRADING");
        if (analysisResponse.success && analysisResponse.data) {
          setAnalysis(analysisResponse.data);
          // Map indicators
          if (analysisResponse.data.indicators) {
            const mappedIndicators = Object.entries(analysisResponse.data.indicators).map(
              ([key, value]: [string, any]) => ({
                name: key.charAt(0).toUpperCase() + key.slice(1),
                value: value.value || 0,
                signal: value.signal || "neutral",
                score: value.score || 50,
                weight: value.weight || 10,
                description: value.description || "",
              })
            );
            setIndicators(mappedIndicators);
          }
        } else {
          // Fallback mock analysis
          setAnalysis({
            stock_code: code,
            stock_name: getStockName(code),
            current_price: 72500,
            change: 1500,
            change_rate: 2.11,
            signal: "STRONG_BUY",
            total_score: 87.5,
            confidence: 0.85,
            reasons: [
              "총점 87.5점 - 강력 매수 신호",
              "[거래량] 전일 대비 350% 폭발적 증가",
              "[호가창] 145% 강한 매수세",
              "[VWAP] 상단 돌파",
              "[MACD] 골든크로스 발생",
            ],
            trade_params: {
              action: "BUY",
              entry_price: 72500,
              stop_loss: 71412,
              stop_loss_pct: -1.5,
              take_profit_1: 73950,
              take_profit_1_pct: 2.0,
              take_profit_2: 74675,
              take_profit_2_pct: 3.0,
              trailing_stop_pct: 1.0,
              position_size_pct: 10,
            },
            indicators: {},
            timestamp: new Date().toISOString(),
          });
          // Fallback mock indicators
          setIndicators([
            { name: "Volume", value: 285, signal: "bullish", score: 85, weight: 25, description: "거래량 285% 증가" },
            { name: "Order Book", value: 135, signal: "bullish", score: 78, weight: 20, description: "체결강도 135%, 매수세 우위" },
            { name: "VWAP", value: 1.5, signal: "bullish", score: 72, weight: 18, description: "VWAP 상단 1.5% 위치" },
            { name: "RSI", value: 58, signal: "neutral", score: 55, weight: 12, description: "RSI 58, 중립권" },
            { name: "MACD", value: 0.8, signal: "bullish", score: 68, weight: 10, description: "MACD 골든크로스" },
            { name: "MA", value: 2.1, signal: "bullish", score: 70, weight: 8, description: "20일선 2.1% 상회" },
            { name: "Bollinger", value: 0.65, signal: "neutral", score: 50, weight: 5, description: "중간밴드 위치 65%" },
            { name: "OBV", value: 12, signal: "bullish", score: 75, weight: 2, description: "OBV 상승 추세" },
          ]);
        }

        // Load chart data
        try {
          const ohlcvResponse = await stocksApi.getOhlcv(code, chartPeriod, 60);
          if (ohlcvResponse.success && ohlcvResponse.data) {
            setChartData(ohlcvResponse.data);
          } else {
            setChartData(generateMockChartData(72500));
          }
        } catch {
          setChartData(generateMockChartData(72500));
        }

        // Generate news
        setNews(generateMockNews(getStockName(code)));

        // Subscribe to real-time updates
        subscribe(code);
      } catch (error) {
        console.error("Failed to load stock data:", error);
        // Set fallback data
        setQuote({
          stock_code: code,
          name: getStockName(code),
          price: 72500,
          change: 1500,
          change_rate: 2.11,
          volume: 15234567,
          high: 73000,
          low: 71500,
          open: 71800,
          prev_close: 71000,
          timestamp: new Date().toISOString(),
        });
        setChartData(generateMockChartData(72500));
        setNews(generateMockNews(getStockName(code)));
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [code, chartPeriod]);

  if (loading) {
    return (
      <div className="min-h-screen gradient-mesh flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 animate-pulse" />
          <p className="mt-6 text-[var(--muted)] font-medium">Loading...</p>
        </div>
      </div>
    );
  }

  if (!quote || !analysis) {
    return (
      <div className="min-h-screen gradient-mesh flex items-center justify-center">
        <p className="text-[var(--muted)]">Stock not found</p>
      </div>
    );
  }

  const config = signalConfig[analysis.signal];
  const isPositive = quote.change_rate >= 0;

  return (
    <div className="min-h-screen gradient-mesh">
      {/* Header */}
      <header className="sticky top-0 z-50 glass-effect border-b border-[var(--border)]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Link
                href="/"
                className="p-2 rounded-xl hover:bg-[var(--secondary)] transition-colors"
              >
                <svg
                  className="w-5 h-5 text-[var(--muted)]"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 19l-7-7 7-7"
                  />
                </svg>
              </Link>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-xl font-bold text-[var(--foreground)]">
                    {quote.name}
                  </h1>
                  {isConnected && (
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" title="실시간 연결됨" />
                  )}
                </div>
                <p className="text-sm text-[var(--muted)] font-mono">
                  {quote.stock_code}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span
                className={`px-3 py-1.5 rounded-lg text-sm font-semibold text-white bg-gradient-to-r ${config.gradient}`}
              >
                {config.label}
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Price Card */}
        <div className="bg-[var(--card)] rounded-2xl p-6 border border-[var(--border)] mb-6">
          <div className="flex items-end justify-between">
            <div>
              <p className="text-4xl font-bold text-[var(--foreground)]">
                {quote.price.toLocaleString()}
                <span className="text-lg font-normal text-[var(--muted)] ml-2">
                  KRW
                </span>
              </p>
              <div className="flex items-center gap-3 mt-2">
                <span
                  className={`inline-flex items-center px-3 py-1 rounded-lg text-sm font-semibold ${
                    isPositive
                      ? "bg-rose-500/10 text-rose-500"
                      : "bg-blue-500/10 text-blue-500"
                  }`}
                >
                  {isPositive ? "+" : ""}
                  {quote.change.toLocaleString()}
                </span>
                <span
                  className={`text-lg font-bold ${
                    isPositive ? "text-rose-500" : "text-blue-500"
                  }`}
                >
                  {isPositive ? "+" : ""}
                  {quote.change_rate.toFixed(2)}%
                </span>
              </div>
            </div>

            <div className="text-right">
              <div
                className={`w-20 h-20 rounded-2xl bg-gradient-to-br ${config.gradient} flex items-center justify-center shadow-lg`}
              >
                <span className="text-3xl font-bold text-white">
                  {analysis.total_score.toFixed(0)}
                </span>
              </div>
              <p className="text-xs text-[var(--muted)] mt-2">Total Score</p>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-4 gap-4 mt-6 pt-6 border-t border-[var(--border)]">
            <div>
              <p className="text-xs text-[var(--muted)]">시가</p>
              <p className="font-semibold text-[var(--foreground)]">
                {quote.open.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-xs text-[var(--muted)]">고가</p>
              <p className="font-semibold text-rose-500">
                {quote.high.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-xs text-[var(--muted)]">저가</p>
              <p className="font-semibold text-blue-500">
                {quote.low.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-xs text-[var(--muted)]">거래량</p>
              <p className="font-semibold text-[var(--foreground)]">
                {(quote.volume / 1000000).toFixed(1)}M
              </p>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          {(["analysis", "chart", "news"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                activeTab === tab
                  ? "bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-lg"
                  : "bg-[var(--secondary)] text-[var(--muted)] hover:text-[var(--foreground)]"
              }`}
            >
              {tab === "analysis" ? "분석" : tab === "chart" ? "차트" : "뉴스"}
            </button>
          ))}
        </div>

        {activeTab === "analysis" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Indicators */}
            <div className="lg:col-span-2 space-y-4">
              <h2 className="text-lg font-bold text-[var(--foreground)]">
                지표 분석
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {indicators.map((ind) => (
                  <div
                    key={ind.name}
                    className="bg-[var(--card)] rounded-xl p-4 border border-[var(--border)]"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <span
                          className={`w-2 h-2 rounded-full ${
                            ind.signal === "bullish"
                              ? "bg-emerald-500"
                              : ind.signal === "bearish"
                              ? "bg-rose-500"
                              : "bg-amber-500"
                          }`}
                        />
                        <span className="font-semibold text-[var(--foreground)]">
                          {ind.name}
                        </span>
                      </div>
                      <span className="text-xs text-[var(--muted)]">
                        Weight: {ind.weight}%
                      </span>
                    </div>

                    <div className="flex items-end justify-between">
                      <div>
                        <p className="text-2xl font-bold text-[var(--foreground)]">
                          {ind.score}
                        </p>
                        <p className="text-xs text-[var(--muted)]">
                          {ind.description}
                        </p>
                      </div>
                      <div
                        className={`px-2 py-1 rounded-lg text-xs font-semibold ${
                          ind.signal === "bullish"
                            ? "bg-emerald-500/10 text-emerald-500"
                            : ind.signal === "bearish"
                            ? "bg-rose-500/10 text-rose-500"
                            : "bg-amber-500/10 text-amber-500"
                        }`}
                      >
                        {ind.signal === "bullish" ? "강세" : ind.signal === "bearish" ? "약세" : "중립"}
                      </div>
                    </div>

                    {/* Score bar */}
                    <div className="mt-3 h-1.5 bg-[var(--secondary)] rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          ind.signal === "bullish"
                            ? "bg-gradient-to-r from-emerald-500 to-teal-500"
                            : ind.signal === "bearish"
                            ? "bg-gradient-to-r from-rose-500 to-pink-500"
                            : "bg-gradient-to-r from-amber-500 to-yellow-500"
                        }`}
                        style={{ width: `${ind.score}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Trade Params */}
            <div className="space-y-4">
              <h2 className="text-lg font-bold text-[var(--foreground)]">
                매매 파라미터
              </h2>
              <div className="bg-[var(--card)] rounded-xl p-5 border border-[var(--border)] space-y-4">
                <div className="flex items-center justify-between py-2 border-b border-[var(--border)]">
                  <span className="text-[var(--muted)]">진입가</span>
                  <span className="font-semibold text-[var(--foreground)]">
                    {analysis.trade_params.entry_price?.toLocaleString()} KRW
                  </span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-[var(--border)]">
                  <span className="text-[var(--muted)]">손절가</span>
                  <div className="text-right">
                    <span className="font-semibold text-rose-500">
                      {analysis.trade_params.stop_loss?.toLocaleString()} KRW
                    </span>
                    <span className="text-xs text-rose-500 ml-2">
                      ({analysis.trade_params.stop_loss_pct}%)
                    </span>
                  </div>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-[var(--border)]">
                  <span className="text-[var(--muted)]">목표가 1</span>
                  <div className="text-right">
                    <span className="font-semibold text-emerald-500">
                      {analysis.trade_params.take_profit_1?.toLocaleString()} KRW
                    </span>
                    <span className="text-xs text-emerald-500 ml-2">
                      (+{analysis.trade_params.take_profit_1_pct}%)
                    </span>
                  </div>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-[var(--border)]">
                  <span className="text-[var(--muted)]">목표가 2</span>
                  <div className="text-right">
                    <span className="font-semibold text-emerald-500">
                      {analysis.trade_params.take_profit_2?.toLocaleString()} KRW
                    </span>
                    <span className="text-xs text-emerald-500 ml-2">
                      (+{analysis.trade_params.take_profit_2_pct}%)
                    </span>
                  </div>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="text-[var(--muted)]">트레일링 스탑</span>
                  <span className="font-semibold text-[var(--foreground)]">
                    {analysis.trade_params.trailing_stop_pct}%
                  </span>
                </div>

                <button className="w-full mt-4 py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 transition-all shadow-lg shadow-indigo-500/25">
                  관심종목 추가
                </button>
              </div>

              {/* Analysis Reasons */}
              <div className="bg-[var(--card)] rounded-xl p-5 border border-[var(--border)]">
                <h3 className="font-semibold text-[var(--foreground)] mb-3">
                  분석 요약
                </h3>
                <div className="space-y-2">
                  {analysis.reasons.map((reason, i) => (
                    <p key={i} className="text-sm text-[var(--muted)]">
                      {reason}
                    </p>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "chart" && (
          <div className="bg-[var(--card)] rounded-xl p-6 border border-[var(--border)]">
            {/* Chart Period Selector */}
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-[var(--foreground)]">가격 차트</h3>
              <div className="flex gap-2">
                {(["D", "W", "M"] as const).map((period) => (
                  <button
                    key={period}
                    onClick={() => setChartPeriod(period)}
                    className={`px-3 py-1 rounded-lg text-sm font-medium transition-all ${
                      chartPeriod === period
                        ? "bg-indigo-500 text-white"
                        : "bg-[var(--secondary)] text-[var(--muted)] hover:text-[var(--foreground)]"
                    }`}
                  >
                    {period === "D" ? "일" : period === "W" ? "주" : "월"}
                  </button>
                ))}
              </div>
            </div>

            {chartData.length > 0 ? (
              <CandlestickChart data={chartData} height={450} showVolume={true} />
            ) : (
              <div className="h-[450px] flex items-center justify-center">
                <p className="text-[var(--muted)]">차트 데이터를 불러오는 중...</p>
              </div>
            )}

            {/* Chart Legend */}
            <div className="flex items-center justify-center gap-6 mt-4 text-xs text-[var(--muted)]">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded bg-emerald-500" />
                <span>상승</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded bg-rose-500" />
                <span>하락</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-8 h-2 rounded bg-gradient-to-r from-emerald-500/50 to-emerald-500/30" />
                <span>거래량</span>
              </div>
            </div>
          </div>
        )}

        {activeTab === "news" && (
          <div className="space-y-4">
            <h3 className="font-semibold text-[var(--foreground)]">관련 뉴스</h3>
            <div className="space-y-3">
              {news.map((item) => (
                <div
                  key={item.id}
                  className="bg-[var(--card)] rounded-xl p-4 border border-[var(--border)] hover:border-indigo-500/50 transition-colors cursor-pointer"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <h4 className="font-medium text-[var(--foreground)] mb-2 line-clamp-2">
                        {item.title}
                      </h4>
                      <div className="flex items-center gap-3 text-xs text-[var(--muted)]">
                        <span>{item.source}</span>
                        <span>{item.time}</span>
                      </div>
                    </div>
                    <div
                      className={`px-2 py-1 rounded-lg text-xs font-semibold shrink-0 ${
                        item.sentiment === "positive"
                          ? "bg-emerald-500/10 text-emerald-500"
                          : item.sentiment === "negative"
                          ? "bg-rose-500/10 text-rose-500"
                          : "bg-slate-500/10 text-slate-500"
                      }`}
                    >
                      {item.sentiment === "positive" ? "긍정" : item.sentiment === "negative" ? "부정" : "중립"}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* News Summary */}
            <div className="bg-[var(--card)] rounded-xl p-5 border border-[var(--border)]">
              <h4 className="font-semibold text-[var(--foreground)] mb-3">뉴스 감성 분석</h4>
              <div className="flex items-center gap-4">
                <div className="flex-1 h-3 bg-[var(--secondary)] rounded-full overflow-hidden flex">
                  <div
                    className="bg-emerald-500"
                    style={{ width: `${(news.filter((n) => n.sentiment === "positive").length / news.length) * 100}%` }}
                  />
                  <div
                    className="bg-slate-400"
                    style={{ width: `${(news.filter((n) => n.sentiment === "neutral").length / news.length) * 100}%` }}
                  />
                  <div
                    className="bg-rose-500"
                    style={{ width: `${(news.filter((n) => n.sentiment === "negative").length / news.length) * 100}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-emerald-500">
                  {Math.round((news.filter((n) => n.sentiment === "positive").length / news.length) * 100)}% 긍정
                </span>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
