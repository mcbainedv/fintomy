import React, { useEffect, useRef } from "react";
import { createChart, ColorType, CrosshairMode } from "lightweight-charts";

const CHART_BASE = {
  layout: {
    background: { type: ColorType.Solid, color: "#161b22" },
    textColor: "#8b949e",
  },
  grid: {
    vertLines: { color: "#222a33" },
    horzLines: { color: "#222a33" },
  },
  crosshair: { mode: CrosshairMode.Normal },
  rightPriceScale: { borderColor: "#2a323d" },
  timeScale: { borderColor: "#2a323d" },
  autoSize: true,
};

function useChart(setup, deps) {
  const ref = useRef(null);
  useEffect(() => {
    if (!ref.current) return undefined;
    const chart = createChart(ref.current, CHART_BASE);
    const cleanup = setup(chart);
    return () => {
      if (typeof cleanup === "function") cleanup();
      chart.remove();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return ref;
}

export default function ChartPanel({ data }) {
  const candles = data?.candles || [];

  const priceRef = useChart(
    (chart) => {
      const candle = chart.addCandlestickSeries({
        upColor: "#2ea043",
        downColor: "#f85149",
        borderVisible: false,
        wickUpColor: "#2ea043",
        wickDownColor: "#f85149",
      });
      candle.setData(
        candles.map((c) => ({
          time: c.date,
          open: c.open,
          high: c.high,
          low: c.low,
          close: c.close,
        }))
      );

      const sma = chart.addLineSeries({ color: "#58a6ff", lineWidth: 2 });
      sma.setData((data.sma || []).map((p) => ({ time: p.date, value: p.value })));

      const upper = chart.addLineSeries({ color: "#8b949e", lineWidth: 1, lineStyle: 2 });
      upper.setData(
        (data.bollinger?.upper || []).map((p) => ({ time: p.date, value: p.value }))
      );
      const lower = chart.addLineSeries({ color: "#8b949e", lineWidth: 1, lineStyle: 2 });
      lower.setData(
        (data.bollinger?.lower || []).map((p) => ({ time: p.date, value: p.value }))
      );

      const seen = new Set();
      const markers = (data.markers || [])
        .filter((m) => {
          const key = `${m.date}-${m.type}`;
          if (seen.has(key)) return false;
          seen.add(key);
          return true;
        })
        .map((m) => ({
          time: m.date,
          position: m.type === "BUY" ? "belowBar" : "aboveBar",
          color: m.type === "BUY" ? "#2ea043" : "#f85149",
          shape: m.type === "BUY" ? "arrowUp" : "arrowDown",
          text: `${m.type} ${m.source}`,
        }));
      candle.setMarkers(markers);

      chart.timeScale().fitContent();
      return undefined;
    },
    [data]
  );

  const rsiRef = useChart(
    (chart) => {
      const line = chart.addLineSeries({ color: "#d29922", lineWidth: 2 });
      line.setData((data.rsi || []).map((p) => ({ time: p.date, value: p.value })));
      line.createPriceLine({ price: 70, color: "#f85149", lineStyle: 2, lineWidth: 1 });
      line.createPriceLine({ price: 30, color: "#2ea043", lineStyle: 2, lineWidth: 1 });
      chart.timeScale().fitContent();
      return undefined;
    },
    [data]
  );

  const macdRef = useChart(
    (chart) => {
      const macd = data.macd || [];
      const hist = chart.addHistogramSeries({ base: 0 });
      hist.setData(
        macd.map((p) => ({
          time: p.date,
          value: p.hist,
          color: p.hist >= 0 ? "rgba(46,160,67,0.6)" : "rgba(248,81,73,0.6)",
        }))
      );
      const macdLine = chart.addLineSeries({ color: "#58a6ff", lineWidth: 2 });
      macdLine.setData(macd.map((p) => ({ time: p.date, value: p.macd })));
      const signalLine = chart.addLineSeries({ color: "#d29922", lineWidth: 1 });
      signalLine.setData(macd.map((p) => ({ time: p.date, value: p.signal })));
      chart.timeScale().fitContent();
      return undefined;
    },
    [data]
  );

  if (!candles.length) {
    return (
      <div className="chart-card">
        <div style={{ color: "var(--text-dim)", padding: 20 }}>
          Nema cenovnih podataka za ovaj period. Pokreni skrejper.
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="chart-card">
        <h3>Cena · SMA{data.ma_period} · Bollinger · signali</h3>
        <div ref={priceRef} style={{ height: 340 }} />
      </div>
      <div className="chart-card">
        <h3>RSI (14)</h3>
        <div ref={rsiRef} style={{ height: 140 }} />
      </div>
      <div className="chart-card">
        <h3>MACD (12, 26, 9)</h3>
        <div ref={macdRef} style={{ height: 150 }} />
      </div>
    </>
  );
}
