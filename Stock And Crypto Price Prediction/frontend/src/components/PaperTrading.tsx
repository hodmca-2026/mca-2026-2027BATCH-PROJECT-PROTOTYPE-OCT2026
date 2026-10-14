import React, { useState, useEffect } from "react";
import { PaperPortfolio, TickerData } from "../types";
import { api } from "../services/api";
import { 
  Wallet, 
  ArrowUpRight, 
  ArrowDownRight, 
  DollarSign, 
  Layers, 
  CheckCircle2, 
  Search, 
  ChevronDown, 
  Sparkles, 
  TrendingUp, 
  TrendingDown, 
  RefreshCw, 
  SlidersHorizontal, 
  X,
  ExternalLink,
  Percent
} from "lucide-react";

interface PaperTradingProps {
  currentTicker: TickerData | null;
  activeSymbol: string;
  onSelectSymbol?: (symbol: string) => void;
}

export interface InstrumentOption {
  symbol: string;
  name: string;
  market: "crypto" | "us_equity" | "in_equity" | "index";
  marketLabel: string;
  category: string;
  defaultQty: number;
}

const INSTRUMENT_CATALOG: InstrumentOption[] = [
  // Crypto
  { symbol: "BTCUSDT", name: "Bitcoin / Tether", market: "crypto", marketLabel: "Crypto", category: "crypto", defaultQty: 0.1 },
  { symbol: "ETHUSDT", name: "Ethereum / Tether", market: "crypto", marketLabel: "Crypto", category: "crypto", defaultQty: 1.0 },
  { symbol: "SOLUSDT", name: "Solana / Tether", market: "crypto", marketLabel: "Crypto", category: "crypto", defaultQty: 5.0 },
  { symbol: "BNBUSDT", name: "BNB / Tether", market: "crypto", marketLabel: "Crypto", category: "crypto", defaultQty: 2.0 },
  { symbol: "XRPUSDT", name: "Ripple / Tether", market: "crypto", marketLabel: "Crypto", category: "crypto", defaultQty: 500 },
  { symbol: "DOGEUSDT", name: "Dogecoin / Tether", market: "crypto", marketLabel: "Crypto", category: "crypto", defaultQty: 2000 },
  { symbol: "ADAUSDT", name: "Cardano / Tether", market: "crypto", marketLabel: "Crypto", category: "crypto", defaultQty: 1000 },

  // US Equities
  { symbol: "AAPL", name: "Apple Inc.", market: "us_equity", marketLabel: "US Equities", category: "us_equity", defaultQty: 10 },
  { symbol: "NVDA", name: "NVIDIA Corporation", market: "us_equity", marketLabel: "US Equities", category: "us_equity", defaultQty: 5 },
  { symbol: "TSLA", name: "Tesla Inc.", market: "us_equity", marketLabel: "US Equities", category: "us_equity", defaultQty: 10 },
  { symbol: "MSFT", name: "Microsoft Corporation", market: "us_equity", marketLabel: "US Equities", category: "us_equity", defaultQty: 5 },
  { symbol: "AMZN", name: "Amazon.com Inc.", market: "us_equity", marketLabel: "US Equities", category: "us_equity", defaultQty: 10 },
  { symbol: "GOOGL", name: "Alphabet Inc.", market: "us_equity", marketLabel: "US Equities", category: "us_equity", defaultQty: 10 },
  { symbol: "META", name: "Meta Platforms Inc.", market: "us_equity", marketLabel: "US Equities", category: "us_equity", defaultQty: 5 },

  // Indian Stocks
  { symbol: "RELIANCE", name: "Reliance Industries", market: "in_equity", marketLabel: "NSE India", category: "in_equity", defaultQty: 25 },
  { symbol: "TCS", name: "Tata Consultancy Services", market: "in_equity", marketLabel: "NSE India", category: "in_equity", defaultQty: 15 },
  { symbol: "INFY", name: "Infosys Limited", market: "in_equity", marketLabel: "NSE India", category: "in_equity", defaultQty: 30 },
  { symbol: "HDFCBANK", name: "HDFC Bank Ltd.", market: "in_equity", marketLabel: "NSE India", category: "in_equity", defaultQty: 40 },
  { symbol: "TATAMOTORS", name: "Tata Motors Limited", market: "in_equity", marketLabel: "NSE India", category: "in_equity", defaultQty: 50 },
  { symbol: "ICICIBANK", name: "ICICI Bank Ltd.", market: "in_equity", marketLabel: "NSE India", category: "in_equity", defaultQty: 35 },

  // Indices
  { symbol: "NIFTY50", name: "Nifty 50 Index", market: "index", marketLabel: "Index", category: "index", defaultQty: 1 },
  { symbol: "BANKNIFTY", name: "Nifty Bank Index", market: "index", marketLabel: "Index", category: "index", defaultQty: 1 },
  { symbol: "NAS100", name: "Nasdaq 100 Index", market: "index", marketLabel: "Index", category: "index", defaultQty: 1 },
  { symbol: "US30", name: "Dow Jones 30 Index", market: "index", marketLabel: "Index", category: "index", defaultQty: 1 },
  { symbol: "SPX", name: "S&P 500 Index", market: "index", marketLabel: "Index", category: "index", defaultQty: 1 },
];

export const PaperTrading: React.FC<PaperTradingProps> = ({ 
  currentTicker, 
  activeSymbol,
  onSelectSymbol 
}) => {
  const [portfolio, setPortfolio] = useState<PaperPortfolio | null>(null);
  const [tradeSymbol, setTradeSymbol] = useState(activeSymbol || "BTCUSDT");
  const [symbolTicker, setSymbolTicker] = useState<TickerData | null>(currentTicker);
  const [quantity, setQuantity] = useState(0.1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [orderMsg, setOrderMsg] = useState<{ text: string; isError: boolean } | null>(null);

  // Instrument Selection Modal / Dropdown State
  const [isSelectorOpen, setIsSelectorOpen] = useState(false);
  const [marketFilter, setMarketFilter] = useState<"all" | "crypto" | "us_equity" | "in_equity" | "index">("all");
  const [searchQuery, setSearchQuery] = useState("");

  const fetchPortfolio = async () => {
    try {
      const data = await api.getPortfolio();
      setPortfolio(data);
    } catch (e) {
      console.error(e);
    }
  };

  // Fetch live price for the actively selected trading symbol
  const fetchSymbolPrice = async (sym: string) => {
    try {
      const tick = await api.getTicker(sym);
      if (tick && tick.price > 0) {
        setSymbolTicker(tick);
      }
    } catch (e) {
      console.warn("Could not fetch ticker for", sym, e);
    }
  };

  useEffect(() => {
    fetchPortfolio();
    const interval = setInterval(fetchPortfolio, 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (activeSymbol) {
      setTradeSymbol(activeSymbol);
      fetchSymbolPrice(activeSymbol);
    }
  }, [activeSymbol]);

  useEffect(() => {
    fetchSymbolPrice(tradeSymbol);
    const interval = setInterval(() => {
      fetchSymbolPrice(tradeSymbol);
    }, 4000);
    return () => clearInterval(interval);
  }, [tradeSymbol]);

  const handleSelectInstrument = (inst: InstrumentOption) => {
    setTradeSymbol(inst.symbol);
    setQuantity(inst.defaultQty);
    fetchSymbolPrice(inst.symbol);
    if (onSelectSymbol) {
      onSelectSymbol(inst.symbol);
    }
    setIsSelectorOpen(false);
    setOrderMsg(null);
  };

  const handleCustomSymbolSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      const sym = searchQuery.trim().toUpperCase().replace(/[\/-]/g, "");
      setTradeSymbol(sym);
      fetchSymbolPrice(sym);
      if (onSelectSymbol) {
        onSelectSymbol(sym);
      }
      setIsSelectorOpen(false);
      setSearchQuery("");
      setOrderMsg(null);
    }
  };

  const handleOrder = async (side: "BUY" | "SELL") => {
    if (quantity <= 0) {
      setOrderMsg({ text: "Please enter a valid quantity greater than 0", isError: true });
      return;
    }

    setIsSubmitting(true);
    setOrderMsg(null);
    try {
      const res = await api.submitPaperOrder({
        symbol: tradeSymbol,
        side,
        quantity,
      });
      setOrderMsg({
        text: `Executed ${side} ${quantity} ${tradeSymbol} @ $${Number(res.price || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })}`,
        isError: false,
      });
      await fetchPortfolio();
    } catch (err: any) {
      setOrderMsg({ text: err.message || "Order execution failed", isError: true });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Quick sizing calculator based on available cash
  const handlePercentSizing = (pct: number) => {
    const livePrice = symbolTicker?.price || 1;
    const cash = portfolio?.cash || 100000;
    if (livePrice <= 0) return;
    const targetValue = cash * (pct / 100);
    const calculatedQty = targetValue / livePrice;
    
    // Format quantity cleanly based on magnitude
    if (calculatedQty >= 100) {
      setQuantity(Math.floor(calculatedQty));
    } else if (calculatedQty >= 1) {
      setQuantity(Number(calculatedQty.toFixed(2)));
    } else {
      setQuantity(Number(calculatedQty.toFixed(4)));
    }
  };

  // Filtered instrument catalog
  const filteredInstruments = INSTRUMENT_CATALOG.filter((inst) => {
    const matchesMarket = marketFilter === "all" || inst.category === marketFilter;
    const q = searchQuery.trim().toLowerCase();
    const matchesSearch = !q || inst.symbol.toLowerCase().includes(q) || inst.name.toLowerCase().includes(q);
    return matchesMarket && matchesSearch;
  });

  const selectedInstMeta = INSTRUMENT_CATALOG.find((i) => i.symbol === tradeSymbol);
  const livePrice = symbolTicker?.price || (activeSymbol === tradeSymbol ? currentTicker?.price : 0) || 0;
  const priceChange = symbolTicker?.change_24h_pct ?? 0;
  const isPriceUp = priceChange >= 0;
  const orderValue = livePrice * quantity;
  const commission = orderValue * 0.0005;

  return (
    <div className="space-y-6 font-mono">
      {/* Balance Summary Header */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-[#0D1117] border border-[#232936] p-4 rounded-xl shadow-lg">
          <div className="text-[10px] text-[#8B949E] uppercase mb-1">Virtual Cash Balance</div>
          <div className="text-xl font-bold text-white">
            ${portfolio?.cash.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) ?? "100,000.00"}
          </div>
        </div>

        <div className="bg-[#0D1117] border border-[#232936] p-4 rounded-xl shadow-lg">
          <div className="text-[10px] text-[#8B949E] uppercase mb-1">Total Portfolio Equity</div>
          <div className="text-xl font-bold text-blue-400">
            ${portfolio?.total_equity.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) ?? "100,000.00"}
          </div>
        </div>

        <div className="bg-[#0D1117] border border-[#232936] p-4 rounded-xl shadow-lg">
          <div className="text-[10px] text-[#8B949E] uppercase mb-1">Unrealized P&L</div>
          <div
            className={`text-xl font-bold ${
              (portfolio?.total_pnl ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"
            }`}
          >
            {(portfolio?.total_pnl ?? 0) >= 0 ? "+" : ""}
            ${portfolio?.total_pnl.toFixed(2) ?? "0.00"} ({portfolio?.total_pnl_pct.toFixed(2) ?? "0.00"}%)
          </div>
        </div>

        <div className="bg-[#0D1117] border border-[#232936] p-4 rounded-xl shadow-lg flex items-center justify-between">
          <div>
            <div className="text-[10px] text-[#8B949E] uppercase mb-1">Execution Mode</div>
            <div className="text-sm font-bold text-amber-400">PAPER TRADING</div>
          </div>
          <span className="px-2 py-1 bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[10px] rounded font-bold">
            ZERO RISK
          </span>
        </div>
      </div>

      {/* Main Trading Execution Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Order Ticket with Rich Instrument Selector */}
        <div className="bg-[#0D1117] border border-[#232936] rounded-xl p-5 shadow-lg flex flex-col justify-between relative">
          <div>
            <div className="flex items-center justify-between pb-3.5 border-b border-[#232936] mb-4">
              <div className="flex items-center space-x-2">
                <Wallet className="h-5 w-5 text-blue-400" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Instant Order Execution</h3>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                LIVE MARKET
              </span>
            </div>

            <div className="space-y-4 text-xs">
              {/* Instrument Selection Trigger */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-[#8B949E] font-semibold text-[11px] uppercase tracking-wider">
                    Select Trading Instrument
                  </label>
                  <span className="text-[10px] text-blue-400">Click to switch</span>
                </div>

                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setIsSelectorOpen(!isSelectorOpen)}
                    className="w-full bg-[#151A22] hover:bg-[#1C2330] border border-[#30363D] hover:border-blue-500/50 rounded-lg p-2.5 text-left transition-all flex items-center justify-between group shadow-sm"
                  >
                    <div className="flex items-center space-x-2.5 truncate">
                      <div className="p-1.5 bg-[#0B0E14] rounded border border-[#232936]">
                        <SlidersHorizontal className="h-4 w-4 text-blue-400 group-hover:rotate-90 transition-transform" />
                      </div>
                      <div className="truncate">
                        <div className="flex items-center space-x-1.5">
                          <span className="text-sm font-bold text-white tracking-wide">{tradeSymbol}</span>
                          <span className="text-[9px] px-1.5 py-0.2 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30 font-semibold uppercase">
                            {selectedInstMeta?.marketLabel || "ASSET"}
                          </span>
                        </div>
                        <div className="text-[10px] text-[#8B949E] truncate">
                          {selectedInstMeta?.name || "Market Instrument"}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2 shrink-0">
                      <div className="text-right">
                        <div className="text-xs font-bold text-white">
                          ${livePrice > 0 ? livePrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 }) : "---"}
                        </div>
                        <div className={`text-[9px] font-bold ${isPriceUp ? "text-emerald-400" : "text-rose-400"}`}>
                          {isPriceUp ? "+" : ""}{priceChange.toFixed(2)}%
                        </div>
                      </div>
                      <ChevronDown className={`h-4 w-4 text-[#8B949E] group-hover:text-white transition-transform ${isSelectorOpen ? "rotate-180" : ""}`} />
                    </div>
                  </button>

                  {/* Instrument Selector Dropdown Modal */}
                  {isSelectorOpen && (
                    <div className="absolute top-full left-0 right-0 mt-2 z-30 bg-[#0E131B] border-2 border-blue-500/50 rounded-xl shadow-2xl p-3 space-y-2.5 animate-in fade-in zoom-in-95 duration-150 backdrop-blur-md">
                      {/* Search Bar inside Selector */}
                      <form onSubmit={handleCustomSymbolSubmit} className="relative">
                        <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-[#8B949E]" />
                        <input
                          type="text"
                          placeholder="Search instrument (e.g. BTC, AAPL, RELIANCE)..."
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          className="w-full bg-[#151A22] border border-[#232936] rounded-lg pl-8 pr-8 py-1.5 text-xs text-white placeholder-[#6E7681] focus:outline-none focus:border-blue-500"
                          autoFocus
                        />
                        {searchQuery && (
                          <button
                            type="button"
                            onClick={() => setSearchQuery("")}
                            className="absolute right-2.5 top-2 text-[#8B949E] hover:text-white"
                          >
                            <X className="h-3.5 w-3.5" />
                          </button>
                        )}
                      </form>

                      {/* Category Filter Pills */}
                      <div className="flex items-center space-x-1 overflow-x-auto pb-1 text-[10px]">
                        {(["all", "crypto", "us_equity", "in_equity", "index"] as const).map((cat) => (
                          <button
                            key={cat}
                            type="button"
                            onClick={() => setMarketFilter(cat)}
                            className={`px-2 py-0.5 rounded transition-all whitespace-nowrap border ${
                              marketFilter === cat
                                ? "bg-blue-600 text-white font-bold border-blue-500"
                                : "bg-[#151A22] text-[#8B949E] hover:text-white border-[#232936]"
                            }`}
                          >
                            {cat === "all" ? "All Markets" : cat === "crypto" ? "Crypto" : cat === "us_equity" ? "US Stocks" : cat === "in_equity" ? "NSE India" : "Indices"}
                          </button>
                        ))}
                      </div>

                      {/* Scrollable Instruments List */}
                      <div className="max-h-56 overflow-y-auto space-y-1 pr-1 divide-y divide-[#1F2633]/50">
                        {filteredInstruments.length === 0 ? (
                          <div className="py-6 text-center text-[11px] text-[#8B949E]">
                            No matching preset instrument. Press Enter to search custom: <span className="text-blue-400 font-bold">{searchQuery.toUpperCase()}</span>
                          </div>
                        ) : (
                          filteredInstruments.map((item) => {
                            const isSelected = item.symbol === tradeSymbol;
                            return (
                              <button
                                key={item.symbol}
                                type="button"
                                onClick={() => handleSelectInstrument(item)}
                                className={`w-full p-2 rounded-lg text-left transition-all flex items-center justify-between ${
                                  isSelected
                                    ? "bg-blue-600/20 border border-blue-500/50 text-white"
                                    : "hover:bg-[#161C26] text-[#C9D1D9]"
                                }`}
                              >
                                <div className="truncate">
                                  <div className="flex items-center space-x-1.5">
                                    <span className="font-bold text-xs text-white">{item.symbol}</span>
                                    <span className="text-[9px] px-1.5 py-0.2 rounded bg-black/40 text-blue-300 font-mono">
                                      {item.marketLabel}
                                    </span>
                                  </div>
                                  <div className="text-[10px] text-[#8B949E] truncate">{item.name}</div>
                                </div>
                                <div className="text-[10px] text-right font-mono text-blue-400 flex items-center space-x-1">
                                  <span>Default: {item.defaultQty}</span>
                                  {isSelected && <CheckCircle2 className="h-3 w-3 text-emerald-400 ml-1" />}
                                </div>
                              </button>
                            );
                          })
                        )}
                      </div>

                      <div className="pt-1.5 border-t border-[#1F2633] flex items-center justify-between text-[10px] text-[#8B949E]">
                        <span>Click outside or Esc to close</span>
                        <button
                          type="button"
                          onClick={() => setIsSelectorOpen(false)}
                          className="text-blue-400 hover:underline font-bold"
                        >
                          Close Menu
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Order Quantity & Sizing */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-[#8B949E] font-semibold text-[11px] uppercase tracking-wider">
                    Order Quantity
                  </label>
                  <span className="text-[10px] text-[#8B949E]">
                    Step: {tradeSymbol.includes("BTC") ? "0.01" : "1.0"}
                  </span>
                </div>
                <div className="relative">
                  <input
                    type="number"
                    step={tradeSymbol.includes("BTC") ? "0.01" : "1"}
                    min="0.0001"
                    value={quantity}
                    onChange={(e) => setQuantity(Number(e.target.value))}
                    className="w-full bg-[#151A22] border border-[#232936] focus:border-blue-500 rounded-lg px-3 py-2 text-white font-mono text-sm font-bold focus:outline-none"
                  />
                  <span className="absolute right-3 top-2.5 text-[10px] text-[#8B949E] font-bold uppercase">
                    {tradeSymbol.replace("USDT", "")}
                  </span>
                </div>

                {/* Percentage Cash Allocations */}
                <div className="grid grid-cols-4 gap-1.5 mt-2">
                  {[25, 50, 75, 100].map((pct) => (
                    <button
                      key={pct}
                      type="button"
                      onClick={() => handlePercentSizing(pct)}
                      className="py-1 bg-[#151A22] hover:bg-blue-600/20 hover:border-blue-500/50 border border-[#232936] text-[10px] font-bold rounded text-[#8B949E] hover:text-blue-300 transition-all"
                    >
                      {pct}% Cash
                    </button>
                  ))}
                </div>
              </div>

              {/* Execution Value Calculator */}
              <div className="bg-[#151A22] p-3 rounded-lg border border-[#232936] space-y-1.5 text-[11px]">
                <div className="flex justify-between text-[#8B949E]">
                  <span>Live Execution Price:</span>
                  <span className="text-white font-bold">
                    ${livePrice > 0 ? livePrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 }) : "---"}
                  </span>
                </div>
                <div className="flex justify-between text-[#8B949E]">
                  <span>Estimated Order Value:</span>
                  <span className="text-white font-bold">
                    ${orderValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="flex justify-between text-[#8B949E]">
                  <span>Estimated Commission (0.05%):</span>
                  <span className="text-amber-400 font-bold">
                    ${commission.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons & Order Status Messages */}
          <div className="pt-5 space-y-2.5">
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => handleOrder("BUY")}
                disabled={isSubmitting}
                className="py-3 bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white rounded-lg font-bold text-xs flex items-center justify-center space-x-1.5 transition-all shadow-md shadow-emerald-600/20 disabled:opacity-50"
              >
                <ArrowUpRight className="h-4 w-4" />
                <span>BUY / LONG</span>
              </button>
              <button
                onClick={() => handleOrder("SELL")}
                disabled={isSubmitting}
                className="py-3 bg-rose-600 hover:bg-rose-500 active:scale-95 text-white rounded-lg font-bold text-xs flex items-center justify-center space-x-1.5 transition-all shadow-md shadow-rose-600/20 disabled:opacity-50"
              >
                <ArrowDownRight className="h-4 w-4" />
                <span>SELL / CLOSE</span>
              </button>
            </div>

            {orderMsg && (
              <div
                className={`p-2.5 rounded text-[11px] font-mono border ${
                  orderMsg.isError
                    ? "bg-rose-950/60 border-rose-500 text-rose-300"
                    : "bg-emerald-950/60 border-emerald-500 text-emerald-300"
                }`}
              >
                {orderMsg.text}
              </div>
            )}
          </div>
        </div>

        {/* Positions Table with Instant Trade Action */}
        <div className="lg:col-span-2 bg-[#0D1117] border border-[#232936] rounded-xl p-5 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3.5 border-b border-[#232936] mb-4">
              <div className="flex items-center space-x-2">
                <Layers className="h-5 w-5 text-blue-400" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Open Positions</h3>
              </div>
              <span className="text-[10px] text-[#8B949E]">
                {portfolio?.positions?.length || 0} Active Position{(portfolio?.positions?.length || 0) !== 1 ? "s" : ""}
              </span>
            </div>

            {!portfolio?.positions || portfolio.positions.length === 0 ? (
              <div className="py-16 text-center text-xs text-[#8B949E] space-y-2">
                <p>No active paper positions.</p>
                <p className="text-[11px] text-[#6E7681]">Select any instrument above and submit a BUY order to test your trading strategies.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#151A22] text-[#8B949E] border-b border-[#232936]">
                    <tr>
                      <th className="py-2.5 px-3">Symbol</th>
                      <th className="py-2.5 px-3">Quantity</th>
                      <th className="py-2.5 px-3">Avg Entry</th>
                      <th className="py-2.5 px-3">Current Price</th>
                      <th className="py-2.5 px-3">Market Value</th>
                      <th className="py-2.5 px-3">Unrealized P&L</th>
                      <th className="py-2.5 px-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#232936]/60">
                    {portfolio.positions.map((p) => {
                      const isRowSelected = p.symbol === tradeSymbol;
                      return (
                        <tr 
                          key={p.symbol} 
                          className={`hover:bg-[#151A22]/70 transition-colors ${isRowSelected ? "bg-blue-600/10" : ""}`}
                        >
                          <td className="py-3 px-3 font-bold text-blue-400 flex items-center space-x-1.5">
                            <span>{p.symbol}</span>
                            {isRowSelected && (
                              <span className="text-[8px] bg-blue-500/20 text-blue-300 px-1 py-0.2 rounded font-bold">
                                ACTIVE
                              </span>
                            )}
                          </td>
                          <td className="py-3 px-3 text-white font-mono">{p.quantity}</td>
                          <td className="py-3 px-3 text-[#8B949E] font-mono">${p.avg_entry_price.toLocaleString()}</td>
                          <td className="py-3 px-3 text-white font-bold font-mono">${p.current_price.toLocaleString()}</td>
                          <td className="py-3 px-3 text-white font-mono">${p.position_value.toLocaleString()}</td>
                          <td
                            className={`py-3 px-3 font-bold font-mono ${
                              p.unrealized_pnl >= 0 ? "text-emerald-400" : "text-rose-400"
                            }`}
                          >
                            {p.unrealized_pnl >= 0 ? "+" : ""}${p.unrealized_pnl.toFixed(2)} ({p.unrealized_pnl_pct.toFixed(2)}%)
                          </td>
                          <td className="py-3 px-3 text-right">
                            <button
                              type="button"
                              onClick={() => {
                                setTradeSymbol(p.symbol);
                                setQuantity(p.quantity);
                                fetchSymbolPrice(p.symbol);
                                if (onSelectSymbol) onSelectSymbol(p.symbol);
                              }}
                              className="px-2 py-1 text-[10px] font-bold rounded bg-blue-600/20 hover:bg-blue-600/40 text-blue-300 border border-blue-500/30 transition-all"
                            >
                              Trade
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Quick Instrument Carousel at Bottom */}
          <div className="pt-4 mt-6 border-t border-[#1C2330]">
            <div className="text-[10px] uppercase font-bold text-[#8B949E] mb-2 flex items-center justify-between">
              <span>Quick Instrument Selector</span>
              <span className="text-blue-400 text-[9px]">Click to load into ticket</span>
            </div>
            <div className="flex items-center space-x-1.5 overflow-x-auto pb-1">
              {INSTRUMENT_CATALOG.slice(0, 8).map((inst) => (
                <button
                  key={inst.symbol}
                  onClick={() => handleSelectInstrument(inst)}
                  className={`px-2.5 py-1 text-[10px] font-mono rounded border transition-all shrink-0 flex items-center space-x-1 ${
                    inst.symbol === tradeSymbol
                      ? "bg-blue-600/20 border-blue-500 text-blue-200 font-bold"
                      : "bg-[#151A22] border-[#232936] text-[#8B949E] hover:text-white"
                  }`}
                >
                  <span>{inst.symbol}</span>
                  <span className="text-[8px] opacity-60">({inst.marketLabel})</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
