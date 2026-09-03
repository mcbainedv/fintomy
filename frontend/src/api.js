const BASE = "/api";

async function request(path, options) {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch (_) {
      /* ignore */
    }
    throw new Error(`${res.status} ${detail}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  meta: () => request("/meta"),
  companies: ({ region, sector, favoritesOnly, maPeriod } = {}) => {
    const p = new URLSearchParams();
    if (region) p.set("region", region);
    if (sector) p.set("sector", sector);
    if (favoritesOnly) p.set("favorites_only", "true");
    if (maPeriod) p.set("ma_period", String(maPeriod));
    return request(`/companies?${p.toString()}`);
  },
  company: (ticker) => request(`/companies/${encodeURIComponent(ticker)}`),
  analysis: (ticker, maPeriod) =>
    request(`/companies/${encodeURIComponent(ticker)}/analysis?ma_period=${maPeriod}`),
  chart: (ticker, maPeriod, range) =>
    request(
      `/companies/${encodeURIComponent(ticker)}/chart?ma_period=${maPeriod}&range=${range}`
    ),
  signals: (maPeriod, region) => {
    const p = new URLSearchParams({ ma_period: String(maPeriod) });
    if (region) p.set("region", region);
    return request(`/signals?${p.toString()}`);
  },
  addFavorite: (ticker) =>
    request(`/favorites/${encodeURIComponent(ticker)}`, { method: "PUT" }),
  removeFavorite: (ticker) =>
    request(`/favorites/${encodeURIComponent(ticker)}`, { method: "DELETE" }),
  refresh: () => request("/refresh", { method: "POST" }),
  refreshStatus: () => request("/refresh/status"),
};

export function formatMarketCap(value) {
  if (value == null) return "–";
  const abs = Math.abs(value);
  if (abs >= 1e12) return `${(value / 1e12).toFixed(2)}T`;
  if (abs >= 1e9) return `${(value / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `${(value / 1e6).toFixed(2)}M`;
  return String(value);
}

export function formatNumber(value, digits = 2) {
  if (value == null || Number.isNaN(value)) return "–";
  return Number(value).toFixed(digits);
}

export function formatLocalDateTime(iso) {
  if (!iso) return "–";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString();
}
