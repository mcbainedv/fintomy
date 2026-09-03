import React from "react";

export default function MASettings({
  maPeriod,
  setMaPeriod,
  periods,
  range,
  setRange,
  ranges,
}) {
  return (
    <div className="controls">
      <div className="group">
        <span>Moving average:</span>
        <div className="seg">
          {(periods || [7, 14, 28]).map((p) => (
            <button
              key={p}
              className={p === maPeriod ? "active" : ""}
              onClick={() => setMaPeriod(p)}
            >
              {p}d
            </button>
          ))}
        </div>
      </div>
      <div className="group">
        <span>Period:</span>
        <div className="seg">
          {(ranges || ["3mo", "6mo", "1y", "2y"]).map((r) => (
            <button
              key={r}
              className={r === range ? "active" : ""}
              onClick={() => setRange(r)}
            >
              {r}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
