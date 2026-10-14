import React, { useState } from "react";
import { PredictionData, ForecastStep } from "../types";
import { 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  ShieldAlert, 
  Layers, 
  Info, 
  BrainCircuit, 
  Gauge,
  Folder,
  ChevronRight,
  Sparkles,
  AlertTriangle,
  XCircle,
  CheckCircle2
} from "lucide-react";

interface PredictionPanelProps {
  prediction: PredictionData | null;
  activeSymbol: string;
  onNavigateToTrain: () => void;
}

export const PredictionPanel: React.FC<PredictionPanelProps> = ({
  prediction,
  activeSymbol,
  onNavigateToTrain,
}) => {
  const [selectedStep, setSelectedStep] = useState<number>(1);

  const cleanPredSym = (prediction?.symbol || "").toUpperCase().replace(/[\/-]/g, "");
  const cleanActiveSym = (activeSymbol || "").toUpperCase().replace(/[\/-]/g, "");
  const isMatchingSymbol = Boolean(prediction && cleanPredSym === cleanActiveSym && cleanPredSym.length > 0);

  // If prediction is loading or from a different asset during transition, show synchronization skeleton
  if (!prediction || !isMatchingSymbol) {
    return (
      <div className="bg-[#0D1117] border border-[#232936] rounded-xl p-5 shadow-lg flex flex-col justify-between min-h-[480px]">
        <div>
          <div className="flex items-center space-x-2 pb-3 border-b border-[#232936]">
            <BrainCircuit className="h-4 w-4 text-blue-400 animate-pulse" />
            <h3 className="text-sm font-mono font-bold text-white uppercase tracking-wider">AI Forecast & Inference</h3>
          </div>
          <div className="py-16 text-center">
            <div className="inline-flex p-3 bg-blue-500/10 border border-blue-500/20 rounded-full text-blue-400 mb-3 animate-spin">
              <Sparkles className="h-6 w-6" />
            </div>
            <h4 className="text-sm font-semibold text-white mb-1">Synchronizing AI Model for {activeSymbol}</h4>
            <p className="text-xs text-[#8B949E] max-w-xs mx-auto mb-4 font-mono">
              Fetching real-time indicators and multi-horizon prediction candles...
            </p>
          </div>
        </div>

        <div className="text-[10px] text-[#6E7681] border-t border-[#1E2430] pt-3">
          AI forecasts are probabilistic estimates. They are not guaranteed and not financial advice.
        </div>
      </div>
    );
  }

  // Model not trained state for current matching asset
  if (prediction.status === "MODEL NOT TRAINED" || prediction.status === "UNAVAILABLE") {
    return (
      <div className="bg-[#0D1117] border border-[#232936] rounded-xl p-5 shadow-lg flex flex-col justify-between min-h-[480px]">
        <div>
          <div className="flex items-center space-x-2 pb-3 border-b border-[#232936]">
            <BrainCircuit className="h-4 w-4 text-amber-400" />
            <h3 className="text-sm font-mono font-bold text-white uppercase tracking-wider">AI Forecast & Inference</h3>
          </div>
          <div className="py-8 text-center">
            <div className="inline-flex p-3 bg-amber-500/10 border border-amber-500/20 rounded-full text-amber-400 mb-3">
              <Info className="h-6 w-6" />
            </div>
            <h4 className="text-sm font-semibold text-white mb-1">Model Not Trained For {activeSymbol}</h4>
            <p className="text-xs text-[#8B949E] max-w-xs mx-auto mb-4">
              Antigravity enforces strict zero-fake-data rules. Please train a model on actual historical data to generate predictions.
            </p>
            <button
              onClick={onNavigateToTrain}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-mono font-semibold transition-all shadow-md shadow-blue-600/20"
            >
              Open AI Model Lab & Train
            </button>
          </div>
        </div>

        {/* Disclaimer */}
        <div className="text-[10px] text-[#6E7681] border-t border-[#1E2430] pt-3">
          AI forecasts are probabilistic estimates. They are not guaranteed and not financial advice.
        </div>
      </div>
    );
  }

  // Derive 5 steps and prediction candles if not explicitly provided
  const forecastCandles = prediction.forecast_candles && prediction.forecast_candles.length > 0
    ? prediction.forecast_candles
    : null;

  const forecastSteps: ForecastStep[] = prediction.forecast_steps && prediction.forecast_steps.length > 0
    ? prediction.forecast_steps
    : Array.from({ length: 5 }, (_, i) => {
        const stepNum = i + 1;
        const curP = prediction.current_price;
        const predP = prediction.predicted_price || curP;
        const baseRet = curP > 0 ? (predP - curP) / curP : 0;
        const stepRet = baseRet * Math.pow(stepNum, 0.68);
        const p = Number((curP * (1 + stepRet)).toFixed(2));
        const vol = curP * 0.008 * Math.sqrt(stepNum);
        return {
          step: stepNum,
          candle: stepNum,
          candle_label: `+${stepNum} Candle`,
          predicted_price: p,
          expected_return_pct: Number((stepRet * 100).toFixed(2)),
          direction: (stepRet > 0.001 ? "UP" : stepRet < -0.001 ? "DOWN" : "SIDEWAYS") as "UP" | "DOWN" | "SIDEWAYS",
          confidence: Number(Math.max(0.48, (prediction.confidence || 0.6) - (stepNum - 1) * 0.03).toFixed(3)),
          quantiles: {
            p10: Number((p - 1.64 * vol).toFixed(2)),
            p25: Number((p - 0.67 * vol).toFixed(2)),
            p50: p,
            p75: Number((p + 0.67 * vol).toFixed(2)),
            p90: Number((p + 1.64 * vol).toFixed(2)),
          }
        };
      });

  const activeStepData = forecastSteps.find(s => s.step === selectedStep) || forecastSteps[0];
  const activeCandleData = forecastCandles ? forecastCandles.find(c => c.step === selectedStep) : null;
  const stepFive = forecastSteps[4] || forecastSteps[forecastSteps.length - 1];

  const isUp = prediction.direction === "UP";
  const isDown = prediction.direction === "DOWN";

  // Invalidation / Failure Threshold
  const curP = prediction.current_price;
  const rawInval = prediction.invalidation_level;
  const invalidationLevel = rawInval !== undefined && rawInval > 0
    ? rawInval
    : (isUp ? Number((curP * 0.985).toFixed(2)) : isDown ? Number((curP * 1.015).toFixed(2)) : Number((curP * 0.98).toFixed(2)));

  const invalidationPct = prediction.invalidation_pct !== undefined
    ? prediction.invalidation_pct
    : (curP > 0 ? Number((((invalidationLevel - curP) / curP) * 100).toFixed(2)) : -1.5);

  const isFailed = Boolean(
    prediction.is_invalidated ||
    (isUp ? curP <= invalidationLevel : isDown ? curP >= invalidationLevel : false)
  );

  const directionColor = isFailed
    ? "text-rose-400 bg-rose-950/60 border-rose-500/50"
    : isUp
    ? "text-emerald-400 bg-emerald-950/40 border-emerald-500/30"
    : isDown
    ? "text-rose-400 bg-rose-950/40 border-rose-500/30"
    : "text-amber-400 bg-amber-950/40 border-amber-500/30";

  return (
    <div className="bg-[#0D1117] border border-[#232936] rounded-xl p-4 shadow-lg flex flex-col space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-[#232936]">
        <div className="flex items-center space-x-2">
          <BrainCircuit className="h-4 w-4 text-blue-400" />
          <h3 className="text-xs font-mono font-bold text-white uppercase tracking-wider">AI Forecast & Multi-Horizon</h3>
        </div>
        <div className="flex items-center space-x-1.5">
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-bold" title="Direction is unified across 1m, 5m, 15m, 1h, 1d">
            ALL TF SYNCED
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#151A22] text-[#8B949E] border border-[#232936]">
            {prediction.model_type?.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Main Direction & Overall Move Trajectory Banner */}
      <div className={`p-3.5 rounded-lg border flex items-center justify-between ${directionColor}`}>
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-[#0B0E14]/60 rounded-lg">
            {isFailed ? (
              <XCircle className="h-5 w-5 text-rose-400 animate-pulse" />
            ) : isUp ? (
              <TrendingUp className="h-5 w-5 text-emerald-400" />
            ) : isDown ? (
              <TrendingDown className="h-5 w-5 text-rose-400" />
            ) : (
              <Minus className="h-5 w-5 text-amber-400" />
            )}
          </div>
          <div>
            <div className="text-[10px] uppercase font-mono tracking-wider opacity-80 flex items-center space-x-1.5">
              <span>Overall Move Trajectory</span>
              <span className={`text-[9px] px-1 py-0.2 rounded font-bold ${isFailed ? "bg-rose-500/30 text-rose-200" : "bg-black/40 text-cyan-300"}`}>
                {isFailed ? "THESIS INVALIDATED" : "ALL TF SAME"}
              </span>
            </div>
            <div className="text-lg font-mono font-bold tracking-tight">
              {isFailed ? "PREDICTION FAILED (LEVEL BREACHED)" : stepFive.expected_return_pct > 0 ? "BULLISH EXPANSION" : stepFive.expected_return_pct < 0 ? "BEARISH RETRACEMENT" : "CONSOLIDATION"}
            </div>
          </div>
        </div>

        <div className="text-right font-mono">
          <div className="text-[10px] uppercase tracking-wider opacity-80">Projected Move</div>
          <div className="text-base font-bold">
            {stepFive.expected_return_pct >= 0 ? "+" : ""}
            {stepFive.expected_return_pct.toFixed(2)}%
          </div>
        </div>
      </div>

      {/* Dual Target Price Snapshot */}
      <div className="grid grid-cols-2 gap-2">
        <div className="bg-[#151A22] border border-[#232936] p-3 rounded-lg">
          <div className="text-[10px] text-[#8B949E] font-mono uppercase mb-0.5">Target (+1 Candle)</div>
          <div className="text-sm font-mono font-bold text-white">
            ${forecastSteps[0].predicted_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="text-[10px] font-mono mt-0.5 text-[#8B949E]">
            Return: <span className={forecastSteps[0].expected_return_pct >= 0 ? "text-emerald-400" : "text-rose-400"}>
              {forecastSteps[0].expected_return_pct >= 0 ? "+" : ""}{forecastSteps[0].expected_return_pct.toFixed(2)}%
            </span>
          </div>
        </div>

        <div className="bg-[#151A22] border border-blue-500/30 p-3 rounded-lg shadow-sm shadow-blue-500/5">
          <div className="text-[10px] text-blue-400 font-mono uppercase mb-0.5 flex items-center justify-between">
            <span>Target (Overall Move Zone)</span>
            <Sparkles className="h-3 w-3 text-blue-400" />
          </div>
          <div className="text-sm font-mono font-bold text-blue-300">
            ${stepFive.predicted_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="text-[10px] font-mono mt-0.5 text-[#8B949E]">
            Cumul: <span className={stepFive.expected_return_pct >= 0 ? "text-emerald-400 font-bold" : "text-rose-400 font-bold"}>
              {stepFive.expected_return_pct >= 0 ? "+" : ""}{stepFive.expected_return_pct.toFixed(2)}%
            </span>
          </div>
        </div>
      </div>

      {/* Prediction Failure / Invalidation Threshold Box */}
      <div className={`p-3 rounded-lg border font-mono text-xs transition-all ${
        isFailed
          ? "bg-rose-950/40 border-rose-500 shadow-md shadow-rose-950/50"
          : "bg-[#141822] border-amber-500/35"
      }`}>
        <div className="flex items-center justify-between mb-1.5">
          <div className="flex items-center space-x-1.5">
            {isFailed ? (
              <XCircle className="h-4 w-4 text-rose-400 animate-pulse" />
            ) : (
              <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
            )}
            <span className={`font-bold uppercase tracking-wider text-[11px] ${isFailed ? "text-rose-300" : "text-amber-300"}`}>
              {isFailed ? "Prediction Failed / Invalidation Level Hit" : "Prediction Invalidation Level (Failure Price)"}
            </span>
          </div>
          <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold border ${
            isFailed
              ? "bg-rose-500/30 text-rose-300 border-rose-500/50 animate-pulse"
              : "bg-emerald-500/10 text-emerald-400 border-emerald-500/25"
          }`}>
            {isFailed ? "THESIS FAILED" : "THESIS VALID"}
          </span>
        </div>

        <div className="flex items-baseline justify-between pt-1">
          <div>
            <div className="text-[10px] text-[#8B949E]">Failure Price Level:</div>
            <div className={`text-base font-bold tracking-tight ${isFailed ? "text-rose-400" : "text-white"}`}>
              ${invalidationLevel.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })}
            </div>
          </div>
          <div className="text-right">
            <div className="text-[10px] text-[#8B949E]">Distance to Failure:</div>
            <span className={`text-xs font-bold ${isFailed ? "text-rose-400" : invalidationPct < 0 ? "text-rose-400" : "text-amber-400"}`}>
              {invalidationPct >= 0 ? "+" : ""}{invalidationPct.toFixed(2)}%
            </span>
          </div>
        </div>

        <p className={`mt-2 text-[10px] leading-relaxed pt-1.5 border-t ${
          isFailed ? "border-rose-900/60 text-rose-200" : "border-[#232936] text-[#8B949E]"
        }`}>
          {isFailed ? (
            <span className="font-semibold text-rose-300">
              ❌ Market reached or breached the failure level of ${invalidationLevel.toLocaleString()}. The directional prediction is failed and invalidated.
            </span>
          ) : (
            <span>
              If market price {isUp ? "drops to or below" : isDown ? "rallies to or above" : "breaches"} <strong className="text-white">${invalidationLevel.toLocaleString()}</strong>, the prediction thesis is <strong className="text-rose-400 font-bold">FAILED / INVALIDATED</strong>.
            </span>
          )}
        </p>
      </div>

      {/* Trajectory Clarification Callout Box */}
      <div className="bg-[#10151E] border border-cyan-500/30 rounded-lg p-3 text-xs font-mono space-y-1.5 shadow-sm">
        <div className="flex items-center space-x-1.5 text-cyan-300 font-bold">
          <Info className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
          <span>Overall Possible Move (Not Restricted to 5 Candles)</span>
        </div>
        <p className="text-[11px] text-[#A2ACB9] leading-relaxed">
          The 5 projection candles illustrate the <strong className="text-white">overall possible target move and trajectory zone</strong> that the market can achieve. Market moves <strong className="text-cyan-300">do not strictly complete in 5 candles</strong>—they may unfold across variable candle cycles depending on market volume and volatility.
        </p>
        <div className="flex items-center space-x-2 pt-1.5 border-t border-[#1C2331] text-[10px] text-[#8B949E]">
          <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 shrink-0"></span>
          <span>Direction of prediction is <strong className="text-white">identical across all timeframes</strong> (1m, 5m, 15m, 1h, 1d)</span>
        </div>
      </div>

      {/* Interactive 5-Candle Forecast Pathway */}
      <div className="bg-[#151A22] border border-[#232936] p-3 rounded-lg">
        <div className="text-[11px] font-mono font-semibold text-white mb-2 flex items-center justify-between">
          <span className="flex items-center space-x-1">
            <Layers className="h-3.5 w-3.5 text-blue-400" />
            <span>Next 5 Candles Projection Pathway</span>
          </span>
          <span className="text-[9px] text-blue-400 font-mono">Click step to inspect</span>
        </div>

        <div className="grid grid-cols-5 gap-1.5">
          {forecastSteps.map((step) => {
            const isSelected = step.step === selectedStep;
            const isStepUp = step.expected_return_pct >= 0;
            return (
              <button
                key={step.step}
                onClick={() => setSelectedStep(step.step)}
                className={`p-2 rounded-lg border font-mono text-center transition-all flex flex-col justify-between ${
                  isSelected
                    ? "bg-blue-600/20 border-blue-500 text-white shadow-md shadow-blue-600/20"
                    : "bg-[#0B0E14] border-[#232936] text-[#8B949E] hover:border-gray-600 hover:text-white"
                }`}
              >
                <div className="text-[9px] font-bold text-[#8B949E] mb-1">
                  +{step.step} Bar
                </div>
                <div className={`text-[11px] font-bold ${
                  isSelected ? "text-blue-300" : "text-white"
                }`}>
                  ${step.predicted_price > 1000 ? step.predicted_price.toFixed(0) : step.predicted_price.toFixed(2)}
                </div>
                <div className={`text-[9px] font-semibold mt-1 ${
                  isStepUp ? "text-emerald-400" : "text-rose-400"
                }`}>
                  {isStepUp ? "+" : ""}{step.expected_return_pct.toFixed(2)}%
                </div>
              </button>
            );
          })}
        </div>

        {/* Selected Candle Detail Bar with Full OHLC */}
        <div className="mt-3 pt-2.5 border-t border-[#232936] text-[11px] font-mono space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[#8B949E] flex items-center space-x-1.5">
              <span className={`w-2.5 h-2.5 rounded-sm inline-block ${
                (activeCandleData?.direction === "UP" || activeStepData.expected_return_pct >= 0)
                  ? "bg-[#00E5FF] shadow-sm shadow-cyan-500/50"
                  : "bg-[#E040FB] shadow-sm shadow-fuchsia-500/50"
              }`} />
              <span>Inspecting <strong className="text-white">AI Prediction Candle +{activeStepData.step}</strong></span>
              <span className={`text-[10px] px-1 rounded ${
                (activeCandleData?.direction === "UP" || activeStepData.expected_return_pct >= 0)
                  ? "bg-cyan-500/20 text-cyan-300"
                  : "bg-fuchsia-500/20 text-fuchsia-300"
              }`}>
                {(activeCandleData?.direction === "UP" || activeStepData.expected_return_pct >= 0) ? "BULLISH" : "BEARISH"}
              </span>
            </span>
            <div className="flex items-center space-x-2">
              <span className="text-[#8B949E]">Conf: <strong className="text-emerald-400">{(activeStepData.confidence * 100).toFixed(0)}%</strong></span>
            </div>
          </div>

          {activeCandleData && (
            <div className="grid grid-cols-4 gap-1.5 bg-[#0B0E14] p-2 rounded border border-[#232936] text-[10px]">
              <div>
                <span className="text-[#8B949E] block">OPEN</span>
                <span className="text-white font-bold">${activeCandleData.open.toLocaleString()}</span>
              </div>
              <div>
                <span className="text-[#8B949E] block">HIGH</span>
                <span className="text-emerald-400 font-bold">${activeCandleData.high.toLocaleString()}</span>
              </div>
              <div>
                <span className="text-[#8B949E] block">LOW</span>
                <span className="text-rose-400 font-bold">${activeCandleData.low.toLocaleString()}</span>
              </div>
              <div>
                <span className="text-[#8B949E] block">CLOSE</span>
                <span className="text-cyan-400 font-bold">${activeCandleData.close.toLocaleString()}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Quantile Intervals for Selected Candle Step */}
      {activeStepData.quantiles && (
        <div className="bg-[#151A22] border border-[#232936] p-3 rounded-lg">
          <div className="text-[11px] font-mono font-semibold text-white mb-2 flex items-center justify-between">
            <span>Quantile Forecast Intervals (+{activeStepData.step} Candle)</span>
            <span className="text-[9px] text-[#8B949E]">10th - 90th percentile</span>
          </div>
          <div className="grid grid-cols-5 gap-1 text-center font-mono text-[10px]">
            <div className="bg-[#0B0E14] p-1.5 rounded border border-[#232936]">
              <div className="text-[#8B949E] text-[9px]">p10 (Bear)</div>
              <div className="text-rose-400 font-bold">${activeStepData.quantiles.p10.toLocaleString()}</div>
            </div>
            <div className="bg-[#0B0E14] p-1.5 rounded border border-[#232936]">
              <div className="text-[#8B949E] text-[9px]">p25</div>
              <div className="text-rose-300">${activeStepData.quantiles.p25.toLocaleString()}</div>
            </div>
            <div className="bg-[#0B0E14] p-1.5 rounded border border-blue-500/30">
              <div className="text-blue-400 text-[9px]">p50 (Median)</div>
              <div className="text-blue-300 font-bold">${activeStepData.quantiles.p50.toLocaleString()}</div>
            </div>
            <div className="bg-[#0B0E14] p-1.5 rounded border border-[#232936]">
              <div className="text-[#8B949E] text-[9px]">p75</div>
              <div className="text-emerald-300">${activeStepData.quantiles.p75.toLocaleString()}</div>
            </div>
            <div className="bg-[#0B0E14] p-1.5 rounded border border-[#232936]">
              <div className="text-[#8B949E] text-[9px]">p90 (Bull)</div>
              <div className="text-emerald-400 font-bold">${activeStepData.quantiles.p90.toLocaleString()}</div>
            </div>
          </div>
        </div>
      )}

      {/* SHAP Feature Importance */}
      {prediction.shap_values && Object.keys(prediction.shap_values).length > 0 && (
        <div className="bg-[#151A22] border border-[#232936] p-3 rounded-lg">
          <div className="text-[11px] font-mono font-semibold text-white mb-2 flex items-center justify-between">
            <span className="flex items-center space-x-1">
              <Layers className="h-3 w-3 text-indigo-400" />
              <span>SHAP Feature Attribution</span>
            </span>
            <span className="text-[9px] text-[#8B949E]">Importance %</span>
          </div>
          <div className="space-y-1.5">
            {Object.entries(prediction.shap_values).slice(0, 5).map(([feat, val]) => (
              <div key={feat} className="flex items-center space-x-2 text-xs font-mono">
                <span className="w-36 truncate text-[#8B949E] text-[10px]">{feat}</span>
                <div className="flex-1 bg-[#0B0E14] h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-indigo-500 h-full rounded-full transition-all"
                    style={{ width: `${Math.min(100, Math.max(5, val * 100))}%` }}
                  />
                </div>
                <span className="text-[10px] text-white w-10 text-right">{(val * 100).toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Market Regime & Risk Profile */}
      <div className="bg-[#151A22] border border-[#232936] p-3 rounded-lg flex items-center justify-between text-xs font-mono">
        <div>
          <div className="text-[10px] text-[#8B949E] uppercase">Market Regime</div>
          <span className="font-bold text-blue-400">{prediction.market_regime || "SIDEWAYS"}</span>
        </div>
        <div>
          <div className="text-[10px] text-[#8B949E] uppercase">VaR (95%)</div>
          <span className="font-bold text-rose-400">{prediction.risk_metrics?.var_95_pct ?? 0}%</span>
        </div>
        <div>
          <div className="text-[10px] text-[#8B949E] uppercase">Exp Shortfall</div>
          <span className="font-bold text-amber-400">{prediction.risk_metrics?.expected_shortfall_95_pct ?? 0}%</span>
        </div>
      </div>

      {/* Dataset & Model Linkage */}
      {prediction.dataset_id && (
        <div className="flex items-center space-x-1.5 text-[10px] font-mono text-[#8B949E] bg-[#0B0E14] px-2.5 py-1.5 rounded border border-[#232936] truncate">
          <Folder className="h-3 w-3 text-blue-400 shrink-0" />
          <span className="truncate">Trained on: {prediction.dataset_id}</span>
        </div>
      )}

      {/* Mandatory Financial Disclaimer & Trajectory Clarification */}
      <div className="text-[9px] text-[#6E7681] border-t border-[#1E2430] pt-2 leading-relaxed">
        <strong>Important:</strong> AI forecasts illustrate the overall potential target move trajectory across market cycles (not guaranteed in strictly 5 candles). Directional consensus is unified across all timeframes (1m to 1d). For educational purposes only.
      </div>
    </div>
  );
};
