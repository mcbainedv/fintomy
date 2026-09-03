import React from "react";
import { formatMarketCap, formatNumber } from "../api.js";

function Fact({ k, v }) {
  return (
    <div className="fact">
      <div className="k">{k}</div>
      <div className="v">{v}</div>
    </div>
  );
}

export default function CompanyInfo({ company }) {
  if (!company) return null;
  const dy =
    company.dividend_yield != null
      ? `${formatNumber(company.dividend_yield * 100, 2)}%`
      : "–";
  return (
    <>
      <div className="facts">
        <Fact k="Market cap" v={`${formatMarketCap(company.market_cap)} ${company.currency || ""}`} />
        <Fact k="Beta" v={formatNumber(company.beta)} />
        <Fact k="P/E (trailing)" v={formatNumber(company.trailing_pe)} />
        <Fact k="P/E (forward)" v={formatNumber(company.forward_pe)} />
        <Fact k="Dividend yield" v={dy} />
        <Fact k="52w raspon" v={`${formatNumber(company.week52_low)} – ${formatNumber(company.week52_high)}`} />
        <Fact k="Sektor" v={company.sector || "–"} />
        <Fact k="Berza" v={company.exchange || "–"} />
      </div>
      {company.description && <p className="description">{company.description}</p>}
    </>
  );
}
