import React, { useState, useEffect, useRef, Component, ErrorInfo, ReactNode } from "react";
import { TickerData, CandleData, PredictionData, ModelMetadata } from "./types";
import { api, wsManager } from "./services/api";
import { Header } from "./components/Header";
import { TradingChart } from "./components/TradingChart";
import { PredictionPanel } from "./components/PredictionPanel";
import { ModelLab } from "./components/ModelLab";
import { BacktestStudio } from "./components/BacktestStudio";
import { DatasetsViewer } from "./components/DatasetsViewer";
import { PaperTrading } from "./components/PaperTrading";
import { IRIntelligence } from "./components/IRIntelligence";
import { SystemHealthModal } from "./components/SystemHealthModal";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Dashboard Error caught:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#080B10] text-[#E6EDF3] p-8 flex flex-col items-center justify-center font-mono">
          <div className="bg-[#151A22] border border-red-500/30 p-6 rounded-xl max-w-lg text-center space-y-4 shadow-2xl">
            <h2 className="text-lg font-bold text-red-400">Terminal Render Warning</h2>
            <p className="text-xs text-[#8B949E]">
              {this.state.error?.message || "An unexpected interface error occurred."}
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-bold"
            >
              Reload Terminal
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export const AppContent: React.FC = () => {
  const [activeSymbol, setActiveSymbol] = useState("BTCUSDT");
  const [activeTab, setActiveTab] = useState("terminal");
  const [timeframe, setTimeframe] = useState("1m");

  const [currentTicker, setCurrentTicker] = useState<TickerData | null>(null);
  const [candles, setCandles] = useState<CandleData[]>([]);
  const [prediction, setPrediction] = useState<PredictionData | null>(null);
  const [models, setModels] = useState<ModelMetadata[]>([]);
  
  const [isWsConnected, setIsWsConnected] = useState(false);
  const [isLoadingChart, setIsLoadingChart] = useState(false);
  const [isHealthOpen, setIsHealthOpen] = useState(false);

  const activeRequestSeqRef = useRef<number>(0);

  const handleSelectSymbol = (newSym: string) => {
    const cleanNew = newSym.trim();
    if (cleanNew === activeSymbol) return;
    // Invalidate in-flight async requests immediately
    activeRequestSeqRef.current++;
    // Immediately clear previous asset data so nothing from the old asset lingers
    setCandles([]);
    setCurrentTicker(null);
    setPrediction(null);
    setIsLoadingChart(true);
    setActiveSymbol(cleanNew);
  };

  const handleSelectTimeframe = (newTf: string) => {
    if (newTf === timeframe) return;
    // Invalidate in-flight async requests and clear chart candles & predictions
    activeRequestSeqRef.current++;
    setCandles([]);
    setPrediction(null);
    setIsLoadingChart(true);
    setTimeframe(newTf);
  };

  // 1. Initial WebSocket Connection
  useEffect(() => {
    wsManager.connectMarket(
      (tick: TickerData) => {
        if (tick && tick.symbol) {
          const tickSym = tick.symbol.toUpperCase().replace(/[\/-]/g, "");
          const activeSym = activeSymbol.toUpperCase().replace(/[\/-]/g, "");
          if (tickSym === activeSym) {
            setCurrentTicker(tick);
          }
        }
      },
      (connected: boolean) => setIsWsConnected(connected)
    );

    wsManager.connectTraining((data: any) => {
      window.dispatchEvent(new CustomEvent("app_training_update", { detail: data }));
    });
  }, [activeSymbol]);

  // 2. Load Models Registry
  const loadModels = async () => {
    try {
      const data = await api.getModels();
      if (Array.isArray(data)) {
        setModels(data);
      }
    } catch (e) {
      console.error("Failed loading models", e);
    }
  };

  useEffect(() => {
    loadModels();
  }, []);

  // 3. Load Active Symbol Data & Predictions with strict race-condition guards
  const loadSymbolData = async (sym: string, tf: string) => {
    const seq = ++activeRequestSeqRef.current;
    setIsLoadingChart(true);
    setCandles([]);
    setCurrentTicker(null);
    setPrediction(null);

    const cleanTargetSym = sym.toUpperCase().replace(/[\/-]/g, "");

    try {
      // 1. Fetch historical bars first so chart initializes with target asset's data
      const history = await api.getHistory(sym, tf, 300);
      if (activeRequestSeqRef.current !== seq) return; // Stale request, discard!
      if (history && Array.isArray(history.bars)) {
        setCandles(history.bars);
      }

      // 2. Fetch ticker snapshot to immediately update latest price
      const ticker = await api.getTicker(sym);
      if (activeRequestSeqRef.current !== seq) return; // Stale request, discard!
      if (ticker && ticker.symbol) {
        const tickSym = ticker.symbol.toUpperCase().replace(/[\/-]/g, "");
        if (tickSym === cleanTargetSym) {
          setCurrentTicker(ticker);
        }
      }

      // 3. Fetch real prediction with the active timeframe
      const pred = await api.getPrediction(sym, undefined, tf);
      if (activeRequestSeqRef.current !== seq) return; // Stale request, discard!
      if (pred && pred.symbol) {
        const predSym = pred.symbol.toUpperCase().replace(/[\/-]/g, "");
        if (predSym === cleanTargetSym) {
          setPrediction(pred);
        }
      }
    } catch (e) {
      if (activeRequestSeqRef.current === seq) {
        console.error("Error loading market data", e);
      }
    } finally {
      if (activeRequestSeqRef.current === seq) {
        setIsLoadingChart(false);
      }
    }
  };

  useEffect(() => {
    loadSymbolData(activeSymbol, timeframe);
    const interval = setInterval(() => {
      api.getTicker(activeSymbol).then((t) => {
        if (t && t.symbol) {
          const tickSym = t.symbol.toUpperCase().replace(/[\/-]/g, "");
          const activeSym = activeSymbol.toUpperCase().replace(/[\/-]/g, "");
          if (tickSym === activeSym) {
            setCurrentTicker(t);
          }
        }
      }).catch(console.error);
    }, 2500);
    return () => clearInterval(interval);
  }, [activeSymbol, timeframe]);

  return (
    <div className="min-h-screen bg-[#080B10] text-[#E6EDF3] flex flex-col selection:bg-blue-600 selection:text-white">
      {/* Top Trading Header */}
      <Header
        currentTicker={currentTicker}
        activeSymbol={activeSymbol}
        onSelectSymbol={handleSelectSymbol}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        isWsConnected={isWsConnected}
        onOpenHealth={() => setIsHealthOpen(true)}
      />

      {/* Main Container */}
      <main className="flex-1 p-4 max-w-[1800px] w-full mx-auto">
        {activeTab === "terminal" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Left 2 Cols: Real-Time TradingView Candlestick Chart */}
            <div className="lg:col-span-2">
              <TradingChart
                symbol={activeSymbol}
                candles={candles}
                currentTicker={currentTicker}
                prediction={prediction}
                timeframe={timeframe}
                onChangeTimeframe={handleSelectTimeframe}
                isLoading={isLoadingChart}
              />
            </div>

            {/* Right 1 Col: Real-Time AI Prediction & Cones */}
            <div>
              <PredictionPanel
                prediction={prediction}
                activeSymbol={activeSymbol}
                onNavigateToTrain={() => setActiveTab("model_lab")}
              />
            </div>
          </div>
        )}

        {activeTab === "model_lab" && (
          <ModelLab
            activeSymbol={activeSymbol}
            models={models}
            onRefreshModels={loadModels}
            onTrainingFinished={() => {
              loadModels();
              loadSymbolData(activeSymbol, timeframe);
            }}
          />
        )}

        {activeTab === "ir_intelligence" && (
          <IRIntelligence
            activeSymbol={activeSymbol}
            onSelectSymbol={(sym) => {
              handleSelectSymbol(sym);
              setActiveTab("terminal");
            }}
          />
        )}

        {activeTab === "backtest" && (
          <BacktestStudio activeSymbol={activeSymbol} models={models} />
        )}

        {activeTab === "datasets" && <DatasetsViewer />}

        {activeTab === "paper_trading" && (
          <PaperTrading 
            currentTicker={currentTicker} 
            activeSymbol={activeSymbol} 
            onSelectSymbol={handleSelectSymbol} 
          />
        )}
      </main>

      {/* System Health Diagnostic Modal */}
      <SystemHealthModal isOpen={isHealthOpen} onClose={() => setIsHealthOpen(false)} />
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <AppContent />
    </ErrorBoundary>
  );
};

export default App;
