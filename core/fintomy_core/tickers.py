"""Curated universe of companies scraped by Fintomy.

Each entry is ``(ticker, name, region, sector)``.  ``region`` is ``US`` or ``EU``.
The ``name``/``sector`` values here are only a fallback shown until the scraper
fetches the authoritative data from Yahoo Finance.  Edit these lists freely — the
scraper seeds/updates the ``companies`` table from them on every start.

European tickers use Yahoo exchange suffixes:
``.PA`` Paris · ``.DE`` Xetra · ``.AS`` Amsterdam · ``.L`` London ·
``.SW`` SIX Swiss · ``.MI`` Milan · ``.MC`` Madrid · ``.ST`` Stockholm ·
``.CO`` Copenhagen · ``.HE`` Helsinki · ``.OL`` Oslo · ``.BR`` Brussels ·
``.LS`` Lisbon · ``.IR`` Dublin.
"""
from __future__ import annotations

# --- United States: ~100 large caps spread across GICS sectors -----------------
US_TICKERS: list[tuple[str, str, str, str]] = [
    # Information Technology
    ("AAPL", "Apple Inc.", "US", "Information Technology"),
    ("MSFT", "Microsoft Corporation", "US", "Information Technology"),
    ("NVDA", "NVIDIA Corporation", "US", "Information Technology"),
    ("AVGO", "Broadcom Inc.", "US", "Information Technology"),
    ("ORCL", "Oracle Corporation", "US", "Information Technology"),
    ("CRM", "Salesforce, Inc.", "US", "Information Technology"),
    ("ADBE", "Adobe Inc.", "US", "Information Technology"),
    ("CSCO", "Cisco Systems, Inc.", "US", "Information Technology"),
    ("ACN", "Accenture plc", "US", "Information Technology"),
    ("AMD", "Advanced Micro Devices, Inc.", "US", "Information Technology"),
    ("INTC", "Intel Corporation", "US", "Information Technology"),
    ("IBM", "International Business Machines", "US", "Information Technology"),
    ("QCOM", "QUALCOMM Incorporated", "US", "Information Technology"),
    ("TXN", "Texas Instruments Incorporated", "US", "Information Technology"),
    ("NOW", "ServiceNow, Inc.", "US", "Information Technology"),
    ("INTU", "Intuit Inc.", "US", "Information Technology"),
    ("AMAT", "Applied Materials, Inc.", "US", "Information Technology"),
    ("MU", "Micron Technology, Inc.", "US", "Information Technology"),
    ("LRCX", "Lam Research Corporation", "US", "Information Technology"),
    ("PANW", "Palo Alto Networks, Inc.", "US", "Information Technology"),
    # Communication Services
    ("GOOGL", "Alphabet Inc.", "US", "Communication Services"),
    ("META", "Meta Platforms, Inc.", "US", "Communication Services"),
    ("NFLX", "Netflix, Inc.", "US", "Communication Services"),
    ("DIS", "The Walt Disney Company", "US", "Communication Services"),
    ("CMCSA", "Comcast Corporation", "US", "Communication Services"),
    ("T", "AT&T Inc.", "US", "Communication Services"),
    ("VZ", "Verizon Communications Inc.", "US", "Communication Services"),
    ("TMUS", "T-Mobile US, Inc.", "US", "Communication Services"),
    # Consumer Discretionary
    ("AMZN", "Amazon.com, Inc.", "US", "Consumer Discretionary"),
    ("TSLA", "Tesla, Inc.", "US", "Consumer Discretionary"),
    ("HD", "The Home Depot, Inc.", "US", "Consumer Discretionary"),
    ("MCD", "McDonald's Corporation", "US", "Consumer Discretionary"),
    ("NKE", "NIKE, Inc.", "US", "Consumer Discretionary"),
    ("LOW", "Lowe's Companies, Inc.", "US", "Consumer Discretionary"),
    ("SBUX", "Starbucks Corporation", "US", "Consumer Discretionary"),
    ("BKNG", "Booking Holdings Inc.", "US", "Consumer Discretionary"),
    ("TJX", "The TJX Companies, Inc.", "US", "Consumer Discretionary"),
    ("GM", "General Motors Company", "US", "Consumer Discretionary"),
    # Consumer Staples
    ("WMT", "Walmart Inc.", "US", "Consumer Staples"),
    ("PG", "The Procter & Gamble Company", "US", "Consumer Staples"),
    ("KO", "The Coca-Cola Company", "US", "Consumer Staples"),
    ("PEP", "PepsiCo, Inc.", "US", "Consumer Staples"),
    ("COST", "Costco Wholesale Corporation", "US", "Consumer Staples"),
    ("PM", "Philip Morris International Inc.", "US", "Consumer Staples"),
    ("MO", "Altria Group, Inc.", "US", "Consumer Staples"),
    ("MDLZ", "Mondelez International, Inc.", "US", "Consumer Staples"),
    ("CL", "Colgate-Palmolive Company", "US", "Consumer Staples"),
    # Health Care
    ("UNH", "UnitedHealth Group Incorporated", "US", "Health Care"),
    ("JNJ", "Johnson & Johnson", "US", "Health Care"),
    ("LLY", "Eli Lilly and Company", "US", "Health Care"),
    ("MRK", "Merck & Co., Inc.", "US", "Health Care"),
    ("ABBV", "AbbVie Inc.", "US", "Health Care"),
    ("PFE", "Pfizer Inc.", "US", "Health Care"),
    ("TMO", "Thermo Fisher Scientific Inc.", "US", "Health Care"),
    ("ABT", "Abbott Laboratories", "US", "Health Care"),
    ("DHR", "Danaher Corporation", "US", "Health Care"),
    ("BMY", "Bristol-Myers Squibb Company", "US", "Health Care"),
    ("AMGN", "Amgen Inc.", "US", "Health Care"),
    ("MDT", "Medtronic plc", "US", "Health Care"),
    ("GILD", "Gilead Sciences, Inc.", "US", "Health Care"),
    ("ISRG", "Intuitive Surgical, Inc.", "US", "Health Care"),
    # Financials
    ("BRK-B", "Berkshire Hathaway Inc.", "US", "Financials"),
    ("JPM", "JPMorgan Chase & Co.", "US", "Financials"),
    ("V", "Visa Inc.", "US", "Financials"),
    ("MA", "Mastercard Incorporated", "US", "Financials"),
    ("BAC", "Bank of America Corporation", "US", "Financials"),
    ("WFC", "Wells Fargo & Company", "US", "Financials"),
    ("GS", "The Goldman Sachs Group, Inc.", "US", "Financials"),
    ("MS", "Morgan Stanley", "US", "Financials"),
    ("SPGI", "S&P Global Inc.", "US", "Financials"),
    ("AXP", "American Express Company", "US", "Financials"),
    ("BLK", "BlackRock, Inc.", "US", "Financials"),
    ("SCHW", "The Charles Schwab Corporation", "US", "Financials"),
    ("PGR", "The Progressive Corporation", "US", "Financials"),
    # Industrials
    ("CAT", "Caterpillar Inc.", "US", "Industrials"),
    ("HON", "Honeywell International Inc.", "US", "Industrials"),
    ("UNP", "Union Pacific Corporation", "US", "Industrials"),
    ("GE", "GE Aerospace", "US", "Industrials"),
    ("BA", "The Boeing Company", "US", "Industrials"),
    ("RTX", "RTX Corporation", "US", "Industrials"),
    ("LMT", "Lockheed Martin Corporation", "US", "Industrials"),
    ("DE", "Deere & Company", "US", "Industrials"),
    ("UPS", "United Parcel Service, Inc.", "US", "Industrials"),
    ("ADP", "Automatic Data Processing, Inc.", "US", "Industrials"),
    ("MMM", "3M Company", "US", "Industrials"),
    ("ETN", "Eaton Corporation plc", "US", "Industrials"),
    # Energy
    ("XOM", "Exxon Mobil Corporation", "US", "Energy"),
    ("CVX", "Chevron Corporation", "US", "Energy"),
    ("COP", "ConocoPhillips", "US", "Energy"),
    ("SLB", "Schlumberger Limited", "US", "Energy"),
    ("EOG", "EOG Resources, Inc.", "US", "Energy"),
    ("MPC", "Marathon Petroleum Corporation", "US", "Energy"),
    ("PSX", "Phillips 66", "US", "Energy"),
    # Utilities
    ("NEE", "NextEra Energy, Inc.", "US", "Utilities"),
    ("DUK", "Duke Energy Corporation", "US", "Utilities"),
    ("SO", "The Southern Company", "US", "Utilities"),
    # Real Estate
    ("PLD", "Prologis, Inc.", "US", "Real Estate"),
    ("AMT", "American Tower Corporation", "US", "Real Estate"),
    ("EQIX", "Equinix, Inc.", "US", "Real Estate"),
    # Materials
    ("LIN", "Linde plc", "US", "Materials"),
    ("SHW", "The Sherwin-Williams Company", "US", "Materials"),
    ("APD", "Air Products and Chemicals, Inc.", "US", "Materials"),
    ("FCX", "Freeport-McMoRan Inc.", "US", "Materials"),
]

# --- Europe: ~100 large caps across countries / sectors ------------------------
EU_TICKERS: list[tuple[str, str, str, str]] = [
    # France
    ("MC.PA", "LVMH Moet Hennessy Louis Vuitton", "EU", "Consumer Discretionary"),
    ("OR.PA", "L'Oreal S.A.", "EU", "Consumer Staples"),
    ("TTE.PA", "TotalEnergies SE", "EU", "Energy"),
    ("SAN.PA", "Sanofi S.A.", "EU", "Health Care"),
    ("AIR.PA", "Airbus SE", "EU", "Industrials"),
    ("SU.PA", "Schneider Electric SE", "EU", "Industrials"),
    ("AI.PA", "Air Liquide S.A.", "EU", "Materials"),
    ("EL.PA", "EssilorLuxottica S.A.", "EU", "Health Care"),
    ("CS.PA", "AXA SA", "EU", "Financials"),
    ("BNP.PA", "BNP Paribas SA", "EU", "Financials"),
    ("DG.PA", "Vinci SA", "EU", "Industrials"),
    ("RMS.PA", "Hermes International", "EU", "Consumer Discretionary"),
    ("SAF.PA", "Safran SA", "EU", "Industrials"),
    ("KER.PA", "Kering SA", "EU", "Consumer Discretionary"),
    ("BN.PA", "Danone S.A.", "EU", "Consumer Staples"),
    ("ENGI.PA", "Engie SA", "EU", "Utilities"),
    ("DSY.PA", "Dassault Systemes SE", "EU", "Information Technology"),
    ("ORA.PA", "Orange S.A.", "EU", "Communication Services"),
    ("RI.PA", "Pernod Ricard SA", "EU", "Consumer Staples"),
    ("CAP.PA", "Capgemini SE", "EU", "Information Technology"),
    # Germany
    ("SAP.DE", "SAP SE", "EU", "Information Technology"),
    ("SIE.DE", "Siemens AG", "EU", "Industrials"),
    ("ALV.DE", "Allianz SE", "EU", "Financials"),
    ("DTE.DE", "Deutsche Telekom AG", "EU", "Communication Services"),
    ("MBG.DE", "Mercedes-Benz Group AG", "EU", "Consumer Discretionary"),
    ("BMW.DE", "Bayerische Motoren Werke AG", "EU", "Consumer Discretionary"),
    ("VOW3.DE", "Volkswagen AG", "EU", "Consumer Discretionary"),
    ("BAS.DE", "BASF SE", "EU", "Materials"),
    ("BAYN.DE", "Bayer AG", "EU", "Health Care"),
    ("MUV2.DE", "Muenchener Rueckversicherungs-Gesellschaft AG", "EU", "Financials"),
    ("DHL.DE", "DHL Group", "EU", "Industrials"),
    ("IFX.DE", "Infineon Technologies AG", "EU", "Information Technology"),
    ("ADS.DE", "adidas AG", "EU", "Consumer Discretionary"),
    ("DB1.DE", "Deutsche Boerse AG", "EU", "Financials"),
    ("RWE.DE", "RWE AG", "EU", "Utilities"),
    ("HEN3.DE", "Henkel AG & Co. KGaA", "EU", "Consumer Staples"),
    ("DBK.DE", "Deutsche Bank AG", "EU", "Financials"),
    ("MRK.DE", "Merck KGaA", "EU", "Health Care"),
    ("SHL.DE", "Siemens Healthineers AG", "EU", "Health Care"),
    # Netherlands
    ("ASML.AS", "ASML Holding N.V.", "EU", "Information Technology"),
    ("PRX.AS", "Prosus N.V.", "EU", "Consumer Discretionary"),
    ("INGA.AS", "ING Groep N.V.", "EU", "Financials"),
    ("AD.AS", "Koninklijke Ahold Delhaize N.V.", "EU", "Consumer Staples"),
    ("PHIA.AS", "Koninklijke Philips N.V.", "EU", "Health Care"),
    ("HEIA.AS", "Heineken N.V.", "EU", "Consumer Staples"),
    ("WKL.AS", "Wolters Kluwer N.V.", "EU", "Industrials"),
    ("ADYEN.AS", "Adyen N.V.", "EU", "Financials"),
    ("ASM.AS", "ASM International N.V.", "EU", "Information Technology"),
    # United Kingdom
    ("AZN.L", "AstraZeneca PLC", "EU", "Health Care"),
    ("SHEL.L", "Shell plc", "EU", "Energy"),
    ("HSBA.L", "HSBC Holdings plc", "EU", "Financials"),
    ("ULVR.L", "Unilever PLC", "EU", "Consumer Staples"),
    ("BP.L", "BP p.l.c.", "EU", "Energy"),
    ("GSK.L", "GSK plc", "EU", "Health Care"),
    ("RIO.L", "Rio Tinto Group", "EU", "Materials"),
    ("DGE.L", "Diageo plc", "EU", "Consumer Staples"),
    ("REL.L", "RELX PLC", "EU", "Industrials"),
    ("GLEN.L", "Glencore plc", "EU", "Materials"),
    ("BATS.L", "British American Tobacco p.l.c.", "EU", "Consumer Staples"),
    ("LSEG.L", "London Stock Exchange Group plc", "EU", "Financials"),
    ("NG.L", "National Grid plc", "EU", "Utilities"),
    ("BARC.L", "Barclays PLC", "EU", "Financials"),
    ("VOD.L", "Vodafone Group Plc", "EU", "Communication Services"),
    ("RKT.L", "Reckitt Benckiser Group plc", "EU", "Consumer Staples"),
    ("BA.L", "BAE Systems plc", "EU", "Industrials"),
    # Switzerland
    ("NESN.SW", "Nestle S.A.", "EU", "Consumer Staples"),
    ("RO.SW", "Roche Holding AG", "EU", "Health Care"),
    ("NOVN.SW", "Novartis AG", "EU", "Health Care"),
    ("UBSG.SW", "UBS Group AG", "EU", "Financials"),
    ("ZURN.SW", "Zurich Insurance Group AG", "EU", "Financials"),
    ("ABBN.SW", "ABB Ltd", "EU", "Industrials"),
    ("LONN.SW", "Lonza Group AG", "EU", "Health Care"),
    ("SIKA.SW", "Sika AG", "EU", "Materials"),
    ("CFR.SW", "Compagnie Financiere Richemont SA", "EU", "Consumer Discretionary"),
    ("HOLN.SW", "Holcim AG", "EU", "Materials"),
    # Italy
    ("ISP.MI", "Intesa Sanpaolo S.p.A.", "EU", "Financials"),
    ("ENEL.MI", "Enel SpA", "EU", "Utilities"),
    ("ENI.MI", "Eni S.p.A.", "EU", "Energy"),
    ("UCG.MI", "UniCredit S.p.A.", "EU", "Financials"),
    ("RACE.MI", "Ferrari N.V.", "EU", "Consumer Discretionary"),
    # Spain
    ("SAN.MC", "Banco Santander, S.A.", "EU", "Financials"),
    ("IBE.MC", "Iberdrola, S.A.", "EU", "Utilities"),
    ("ITX.MC", "Industria de Diseno Textil, S.A.", "EU", "Consumer Discretionary"),
    ("TEF.MC", "Telefonica, S.A.", "EU", "Communication Services"),
    # Nordics
    ("NOVO-B.CO", "Novo Nordisk A/S", "EU", "Health Care"),
    ("DSV.CO", "DSV A/S", "EU", "Industrials"),
    ("ORSTED.CO", "Orsted A/S", "EU", "Utilities"),
    ("MAERSK-B.CO", "A.P. Moller - Maersk A/S", "EU", "Industrials"),
    ("INVE-B.ST", "Investor AB", "EU", "Financials"),
    ("ATCO-A.ST", "Atlas Copco AB", "EU", "Industrials"),
    ("VOLV-B.ST", "AB Volvo", "EU", "Industrials"),
    ("ERIC-B.ST", "Telefonaktiebolaget LM Ericsson", "EU", "Information Technology"),
    ("HM-B.ST", "H & M Hennes & Mauritz AB", "EU", "Consumer Discretionary"),
    ("NOKIA.HE", "Nokia Oyj", "EU", "Information Technology"),
    ("NDA-FI.HE", "Nordea Bank Abp", "EU", "Financials"),
    ("KNEBV.HE", "KONE Oyj", "EU", "Industrials"),
    ("SAMPO.HE", "Sampo Oyj", "EU", "Financials"),
    ("EQNR.OL", "Equinor ASA", "EU", "Energy"),
    ("DNB.OL", "DNB Bank ASA", "EU", "Financials"),
    ("TEL.OL", "Telenor ASA", "EU", "Communication Services"),
    ("NHY.OL", "Norsk Hydro ASA", "EU", "Materials"),
    # Belgium
    ("ABI.BR", "Anheuser-Busch InBev SA/NV", "EU", "Consumer Staples"),
    ("UCB.BR", "UCB SA", "EU", "Health Care"),
]

ALL_TICKERS: list[tuple[str, str, str, str]] = US_TICKERS + EU_TICKERS


def seed_rows() -> list[dict]:
    return [
        {"ticker": t, "name": n, "region": r, "sector": s}
        for (t, n, r, s) in ALL_TICKERS
    ]
