import React from "react";

function Chip({ entry, kind, onSelect }) {
  const chg = entry.change_pct;
  return (
    <button
      className={`chip ${kind}`}
      title={(entry.reasons || []).join("\n") || entry.name}
      onClick={() => onSelect(entry.ticker)}
    >
      {entry.is_favorite ? "★ " : ""}
      {entry.ticker}
      {chg != null && <small>{chg > 0 ? "+" : ""}{chg}%</small>}
    </button>
  );
}

export default function SignalBar({ signals, loading, onSelect }) {
  const buy = signals?.buy || [];
  const sell = signals?.sell || [];
  return (
    <div className="signalbar">
      <div className="col buy">
        <div className="title">Buy signali ({buy.length})</div>
        <div className="chip-row">
          {loading && buy.length === 0 && <span className="chip buy">…</span>}
          {!loading && buy.length === 0 && (
            <span style={{ color: "var(--text-dim)", fontSize: 12 }}>nema aktivnih</span>
          )}
          {buy.map((e) => (
            <Chip key={e.ticker} entry={e} kind="buy" onSelect={onSelect} />
          ))}
        </div>
      </div>
      <div className="col sell">
        <div className="title">Sell signali ({sell.length})</div>
        <div className="chip-row">
          {loading && sell.length === 0 && <span className="chip sell">…</span>}
          {!loading && sell.length === 0 && (
            <span style={{ color: "var(--text-dim)", fontSize: 12 }}>nema aktivnih</span>
          )}
          {sell.map((e) => (
            <Chip key={e.ticker} entry={e} kind="sell" onSelect={onSelect} />
          ))}
        </div>
      </div>
    </div>
  );
}
