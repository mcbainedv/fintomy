import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, formatNumber } from "./api.js";
import SignalBar from "./components/SignalBar.jsx";
import RefreshBar from "./components/RefreshBar.jsx";
import TickerList from "./components/TickerList.jsx";
import ChartPanel from "./components/ChartPanel.jsx";
import CompanyInfo from "./components/CompanyInfo.jsx";
import MASettings from "./components/MASettings.jsx";

const DEFAULT_MA = 14;

export default function App() {
  const [meta, setMeta] = useState(null);
  const [filters, setFilters] = useState({ region: "ALL", sector: "", favoritesOnly: false });
  const [maPeriod, setMaPeriod] = useState(DEFAULT_MA);
  const [range, setRange] = useState("1y");

  const [companies, setCompanies] = useState([]);
  const [companiesLoading, setCompaniesLoading] = useState(true);
  const [signals, setSignals] = useState(null);
  const [signalsLoading, setSignalsLoading] = useState(true);

  const [selected, setSelected] = useState(null);
  const [company, setCompany] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [chart, setChart] = useState(null);

  const [refreshStatus, setRefreshStatus] = useState(null);
  const [toast, setToast] = useState(null);
  const wasRunning = useRef(false);

  const showToast = useCallback((msg, isErr = false) => {
    setToast({ msg, isErr });
    setTimeout(() => setToast(null), 4000);
  }, []);

  const regionParam = filters.region === "ALL" ? undefined : filters.region;

  const loadCompanies = useCallback(async () => {
    setCompaniesLoading(true);
    try {
      const res = await api.companies({
        region: regionParam,
        sector: filters.sector || undefined,
        favoritesOnly: filters.favoritesOnly,
        maPeriod,
      });
      setCompanies(res.items);
      setSelected((cur) => cur || (res.items[0] && res.items[0].ticker) || null);
    } catch (e) {
      showToast(`Greska pri ucitavanju firmi: ${e.message}`, true);
    } finally {
      setCompaniesLoading(false);
    }
  }, [regionParam, filters.sector, filters.favoritesOnly, maPeriod, showToast]);

  const loadSignals = useCallback(async () => {
    setSignalsLoading(true);
    try {
      setSignals(await api.signals(maPeriod, regionParam));
    } catch (e) {
      showToast(`Greska pri ucitavanju signala: ${e.message}`, true);
    } finally {
      setSignalsLoading(false);
    }
  }, [maPeriod, regionParam, showToast]);

  const loadDetail = useCallback(async () => {
    if (!selected) return;
    try {
      const [c, a, ch] = await Promise.all([
        api.company(selected),
        api.analysis(selected, maPeriod),
        api.chart(selected, maPeriod, range),
      ]);
      setCompany(c);
      setAnalysis(a);
      setChart(ch);
    } catch (e) {
      showToast(`Greska pri ucitavanju detalja: ${e.message}`, true);
    }
  }, [selected, maPeriod, range, showToast]);

  useEffect(() => {
    api
      .meta()
      .then((m) => {
        setMeta(m);
        if (m.default_ma_period) setMaPeriod(m.default_ma_period);
      })
      .catch((e) => showToast(`Meta nedostupna: ${e.message}`, true));
  }, [showToast]);

  useEffect(() => {
    loadCompanies();
    loadSignals();
  }, [loadCompanies, loadSignals]);

  useEffect(() => {
    loadDetail();
  }, [loadDetail]);

  // Poll refresh status; poll fast while a scrape runs, slow when idle.
  // Reload everything when a scrape finishes.
  useEffect(() => {
    let alive = true;
    let timer = null;
    const tick = async () => {
      let nextDelay = 20000;
      try {
        const st = await api.refreshStatus();
        if (!alive) return;
        setRefreshStatus(st);
        if (st.running) nextDelay = 4000;
        if (wasRunning.current && !st.running) {
          const fails = st.last_run?.fail_count || 0;
          showToast(
            fails > 0 ? `Podaci osveženi (${fails} grešaka – vidi ⚠).` : "Podaci osveženi."
          );
          api.meta().then(setMeta).catch(() => {});
          loadCompanies();
          loadSignals();
          loadDetail();
        }
        wasRunning.current = st.running;
      } catch (_) {
        /* ignore transient */
      }
      if (alive) timer = setTimeout(tick, nextDelay);
    };
    tick();
    return () => {
      alive = false;
      if (timer) clearTimeout(timer);
    };
  }, [loadCompanies, loadSignals, loadDetail, showToast]);

  const onToggleFav = useCallback(
    async (ticker, makeFav) => {
      try {
        if (makeFav) await api.addFavorite(ticker);
        else await api.removeFavorite(ticker);
        setCompanies((list) =>
          list.map((c) => (c.ticker === ticker ? { ...c, is_favorite: makeFav } : c))
        );
        setCompany((c) => (c && c.ticker === ticker ? { ...c, is_favorite: makeFav } : c));
      } catch (e) {
        showToast(`Favorit nije sacuvan: ${e.message}`, true);
      }
    },
    [showToast]
  );

  const onRefresh = useCallback(async () => {
    try {
      await api.refresh();
      wasRunning.current = true;
      setRefreshStatus((s) => ({ ...(s || {}), running: true }));
      showToast("Skrejper pokrenut – osvezavanje u toku…");
    } catch (e) {
      showToast(`Ne mogu da pokrenem skrejper: ${e.message}`, true);
    }
  }, [showToast]);

  const sortedCompanies = useMemo(
    () => [...companies].sort((a, b) => a.ticker.localeCompare(b.ticker)),
    [companies]
  );

  return (
    <div className="app">
      <header className="appbar">
        <h1>FINTOMY</h1>
        <RefreshBar status={refreshStatus} meta={meta} onRefresh={onRefresh} />
      </header>

      <SignalBar signals={signals} loading={signalsLoading} onSelect={setSelected} />

      <div className="body">
        <TickerList
          companies={sortedCompanies}
          selected={selected}
          onSelect={setSelected}
          onToggleFav={onToggleFav}
          filters={filters}
          setFilters={setFilters}
          sectors={meta?.sectors || []}
        />

        <div className="detail">
          {!selected && (
            <div className="empty">
              {companiesLoading ? "Ucitavanje…" : "Izaberi ticker sa liste."}
            </div>
          )}

          {selected && (
            <>
              <div className="detail-head">
                <h2>
                  {selected}
                  {company?.name ? ` · ${company.name}` : ""}
                </h2>
                {analysis?.close != null && (
                  <span className="price">
                    {formatNumber(analysis.close)} {company?.currency || ""}
                  </span>
                )}
                {analysis?.change_pct != null && (
                  <span className={analysis.change_pct >= 0 ? "pos" : "neg"}>
                    {analysis.change_pct > 0 ? "+" : ""}
                    {analysis.change_pct}%
                  </span>
                )}
                {analysis?.aggregate && (
                  <span className={`badge ${analysis.aggregate}`}>{analysis.aggregate}</span>
                )}
                {analysis?.as_of && (
                  <span style={{ color: "var(--text-dim)", fontSize: 12 }}>
                    na dan {analysis.as_of}
                  </span>
                )}
              </div>

              <MASettings
                maPeriod={maPeriod}
                setMaPeriod={setMaPeriod}
                periods={meta?.ma_periods}
                range={range}
                setRange={setRange}
                ranges={meta?.ranges}
              />

              {analysis?.indicators && (
                <div className="indicators">
                  {analysis.indicators.map((s) => (
                    <div key={s.name} className={`ind ${s.signal}`}>
                      <div className="n">
                        {s.name} — {s.signal}
                      </div>
                      <div className="d">{s.detail}</div>
                    </div>
                  ))}
                </div>
              )}

              <ChartPanel data={chart} />

              <CompanyInfo company={company} />
            </>
          )}
        </div>
      </div>

      {toast && <div className={`toast ${toast.isErr ? "err" : ""}`}>{toast.msg}</div>}
    </div>
  );
}
