import React, { useState } from "react";
import { formatLocalDateTime } from "../api.js";

const PHASE_LABEL = {
  starting: "priprema",
  prices: "cene",
  fundamentals: "fundamentali",
  done: "gotovo",
  error: "greška",
};

export default function RefreshBar({ status, meta, onRefresh }) {
  const [showErrors, setShowErrors] = useState(false);
  const run = status?.last_run;
  const running = !!status?.running;

  const phase = run?.phase ? PHASE_LABEL[run.phase] || run.phase : "";
  const pct = run?.percent ?? 0;
  const lastUpdate =
    meta?.last_successful_scrape || status?.last_success?.finished_at || null;
  const errors = run?.errors || [];
  const errorCount = run?.error_count ?? errors.length;

  return (
    <div className="refreshbar">
      <div className="refreshbar-top">
        <button className="btn primary" onClick={onRefresh} disabled={running}>
          {running ? "Osvežavanje…" : "Osveži podatke"}
        </button>

        {running && run && (
          <div className="progress-wrap">
            <div className="progress-track">
              <div
                className={`progress-fill ${run.phase}`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <div className="progress-text">
              {phase}: {run.done}/{run.total} ({pct}%)
              {run.current ? ` · ${run.current}` : ""} · upisano {run.rows_written} redova ·
              ok {run.ok_count} / greške {run.fail_count}
            </div>
          </div>
        )}

        {!running && (
          <div className="refreshbar-meta">
            <div>Poslednje uspešno: {formatLocalDateTime(lastUpdate)}</div>
            <div>
              {meta?.company_count ?? "–"} firmi · {meta?.price_count ?? "–"} cenovnih zapisa
              {meta?.latest_price_date ? ` · do ${meta.latest_price_date}` : ""}
              {run
                ? ` · #${run.id} ${run.status} (ok ${run.ok_count}/greške ${run.fail_count})`
                : ""}
            </div>
          </div>
        )}

        {errorCount > 0 && (
          <button className="btn err-toggle" onClick={() => setShowErrors((v) => !v)}>
            ⚠ {errorCount} {showErrors ? "▲" : "▼"}
          </button>
        )}
      </div>

      {showErrors && errorCount > 0 && (
        <ul className="error-list">
          {errors.map((e, i) => (
            <li key={i}>{e}</li>
          ))}
          {errorCount > errors.length && (
            <li className="muted">… i još {errorCount - errors.length} (vidi logove skrejpera)</li>
          )}
        </ul>
      )}
    </div>
  );
}
