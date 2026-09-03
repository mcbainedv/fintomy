import React from "react";

function Row({ c, active, onSelect, onToggleFav }) {
  const chg = c.change_pct;
  const chgClass = chg == null ? "" : chg >= 0 ? "pos" : "neg";
  return (
    <button
      className={`ticker-row ${active ? "active" : ""}`}
      onClick={() => onSelect(c.ticker)}
    >
      <span
        className={`star ${c.is_favorite ? "on" : ""}`}
        role="button"
        tabIndex={-1}
        title={c.is_favorite ? "Ukloni iz favorita" : "Dodaj u favorite"}
        onClick={(e) => {
          e.stopPropagation();
          onToggleFav(c.ticker, !c.is_favorite);
        }}
      >
        {c.is_favorite ? "★" : "☆"}
      </span>
      <span style={{ minWidth: 0 }}>
        <span className="sym">{c.ticker}</span>
        <span className={`dot ${c.signal || "HOLD"}`} title={c.signal} />
        <br />
        <span className="name">{c.name}</span>
      </span>
      <span className={`chg ${chgClass}`}>
        {chg == null ? "–" : `${chg > 0 ? "+" : ""}${chg}%`}
      </span>
    </button>
  );
}

export default function TickerList({
  companies,
  selected,
  onSelect,
  onToggleFav,
  filters,
  setFilters,
  sectors,
}) {
  return (
    <div className="sidebar">
      <div className="filters">
        <div className="seg">
          {["ALL", "US", "EU"].map((r) => (
            <button
              key={r}
              className={filters.region === r ? "active" : ""}
              onClick={() => setFilters((f) => ({ ...f, region: r }))}
            >
              {r}
            </button>
          ))}
        </div>
        <label>
          <input
            type="checkbox"
            checked={filters.favoritesOnly}
            onChange={(e) =>
              setFilters((f) => ({ ...f, favoritesOnly: e.target.checked }))
            }
          />{" "}
          ★ samo favoriti
        </label>
        <select
          value={filters.sector}
          onChange={(e) => setFilters((f) => ({ ...f, sector: e.target.value }))}
        >
          <option value="">svi sektori</option>
          {sectors.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <span style={{ color: "var(--text-dim)", fontSize: 11, marginLeft: "auto" }}>
          {companies.length}
        </span>
      </div>
      <div className="tickerlist">
        {companies.map((c) => (
          <Row
            key={c.ticker}
            c={c}
            active={c.ticker === selected}
            onSelect={onSelect}
            onToggleFav={onToggleFav}
          />
        ))}
        {companies.length === 0 && (
          <div style={{ padding: 16, color: "var(--text-dim)" }}>Nema rezultata.</div>
        )}
      </div>
    </div>
  );
}
