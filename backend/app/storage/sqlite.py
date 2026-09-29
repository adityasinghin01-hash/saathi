from __future__ import annotations

from threading import RLock

from sqlalchemy import JSON, Column
from sqlalchemy.pool import StaticPool
from sqlmodel import Field, Session, SQLModel, create_engine, delete, select


class Record(SQLModel, table=True):
    kind: str = Field(primary_key=True)
    id: str = Field(primary_key=True)
    payload: dict = Field(sa_column=Column(JSON, nullable=False))


class ForecastView:
    """Read-only snapshot of the inputs consumed by the existing forecast functions."""

    def __init__(self, rows: dict[str, list[dict]]):
        self.rows = rows

    def list(self, kind: str) -> list[dict]:
        return self.rows[kind]


class SQLiteStore:
    def __init__(self, url: str):
        options = {"connect_args": {"check_same_thread": False}}
        if url.endswith(":memory:"):
            options["poolclass"] = StaticPool
        self.engine = create_engine(url, **options)
        SQLModel.metadata.create_all(self.engine)
        self._overview_lock = RLock()
        self._forecast_cache: dict[tuple[str, str, int], tuple[int, float, dict]] = {}

    def overview_forecasts(self, pairs: list[tuple[str, str]], horizon_days: int) -> dict:
        from app.domain.forecast import cohort_need, dispensing_forecast, forecast_components

        with self._overview_lock:
            missing = [(facility_id, drug_id) for facility_id, drug_id in pairs
                       if (facility_id, drug_id, horizon_days) not in self._forecast_cache]
            if missing:
                view = ForecastView({kind: self.list(kind) for kind in (
                    "patient", "prescription", "dispensing", "daily_stock", "stockout_day")})
                for facility_id, drug_id in missing:
                    self._forecast_cache[(facility_id, drug_id, horizon_days)] = (
                        cohort_need(view, facility_id, drug_id, horizon_days),
                        dispensing_forecast(view, facility_id, drug_id, horizon_days),
                        forecast_components(view, facility_id, drug_id, horizon_days),
                    )
            return {(facility_id, drug_id): self._forecast_cache[
                (facility_id, drug_id, horizon_days)] for facility_id, drug_id in pairs}

    def prime_overview_forecasts(self) -> None:
        from app.domain.forecast import HORIZON_DAYS

        pairs = [(facility["id"], drug["id"])
                 for facility in self.list("facility") for drug in self.list("drug")]
        self.overview_forecasts(pairs, HORIZON_DAYS)

    def get(self, kind: str, id: str) -> dict | None:
        with Session(self.engine) as session:
            record = session.get(Record, (kind, id))
            return dict(record.payload) if record else None

    def list(self, kind: str) -> list[dict]:
        with Session(self.engine) as session:
            records = session.exec(select(Record).where(Record.kind == kind)).all()
            return [dict(record.payload) for record in records]

    def put(self, kind: str, item: dict) -> None:
        with self._overview_lock:
            with Session(self.engine) as session:
                record = session.get(Record, (kind, item["id"]))
                previous = record.payload if record else None
                if record:
                    record.payload = item
                else:
                    session.add(Record(kind=kind, id=item["id"], payload=item))
                session.commit()
            if kind in {"facility", "drug", "patient", "prescription"}:
                self._forecast_cache.clear()
            elif kind in {"daily_stock", "stockout_day", "dispensing"}:
                pairs = {(item["facility_id"], item["drug_id"])}
                if previous:
                    pairs.add((previous["facility_id"], previous["drug_id"]))
                for key in list(self._forecast_cache):
                    if key[:2] in pairs:
                        del self._forecast_cache[key]

    def put_many(self, items: list[tuple[str, dict]]) -> None:
        """Insert the deterministic seed in one transaction."""
        with self._overview_lock:
            with Session(self.engine) as session:
                session.add_all(Record(kind=kind, id=item["id"], payload=item)
                                for kind, item in items)
                session.commit()
            self._forecast_cache.clear()

    def reset(self) -> None:
        with self._overview_lock:
            with Session(self.engine) as session:
                session.exec(delete(Record))
                session.commit()
            self._forecast_cache.clear()
