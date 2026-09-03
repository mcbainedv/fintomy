"""SQLAlchemy ORM models for Fintomy."""
from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "companies"

    ticker: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), default="")
    region: Mapped[str] = mapped_column(String(2), index=True)  # 'US' | 'EU'
    sector: Mapped[str] = mapped_column(String(80), default="", index=True)
    industry: Mapped[str] = mapped_column(String(120), default="")
    exchange: Mapped[str] = mapped_column(String(40), default="")
    currency: Mapped[str] = mapped_column(String(10), default="")
    description: Mapped[str] = mapped_column(Text, default="")

    market_cap: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    beta: Mapped[float | None] = mapped_column(Float, nullable=True)
    trailing_pe: Mapped[float | None] = mapped_column(Float, nullable=True)
    forward_pe: Mapped[float | None] = mapped_column(Float, nullable=True)
    dividend_yield: Mapped[float | None] = mapped_column(Float, nullable=True)
    week52_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    week52_low: Mapped[float | None] = mapped_column(Float, nullable=True)

    fundamentals_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    prices: Mapped[list["Price"]] = relationship(
        back_populates="company", cascade="all, delete-orphan", passive_deletes=True
    )


class Price(Base):
    __tablename__ = "prices"
    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_prices_ticker_date"),
        Index("ix_prices_ticker_date", "ticker", "date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(
        String(20), ForeignKey("companies.ticker", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    open: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    high: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    low: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    close: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    adj_close: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    volume: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    company: Mapped[Company] = relationship(back_populates="prices")


class Favorite(Base):
    __tablename__ = "favorites"

    ticker: Mapped[str] = mapped_column(
        String(20), ForeignKey("companies.ticker", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(20))  # scheduled | manual | backfill
    status: Mapped[str] = mapped_column(String(20), default="running")  # running | ok | error
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ok_count: Mapped[int] = mapped_column(Integer, default=0)
    fail_count: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str] = mapped_column(Text, default="")

    # Live progress (updated while the run is in flight).
    phase: Mapped[str] = mapped_column(String(20), default="starting")  # prices|fundamentals|done|error
    total: Mapped[int] = mapped_column(Integer, default=0)   # tickers in current phase
    done: Mapped[int] = mapped_column(Integer, default=0)    # tickers processed in current phase
    rows_written: Mapped[int] = mapped_column(Integer, default=0)  # price rows upserted so far
    current: Mapped[str] = mapped_column(String(40), default="")   # ticker being processed
    errors: Mapped[str] = mapped_column(Text, default="")   # newline-separated "TICKER: reason"


class RefreshRequest(Base):
    """A row here is a manual "refresh now" request from the UI."""

    __tablename__ = "refresh_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    picked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    run_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
