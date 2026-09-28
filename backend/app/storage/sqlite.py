from collections.abc import Callable
from threading import RLock

from sqlalchemy import JSON, Column
from sqlalchemy.pool import StaticPool
from sqlmodel import Field, Session, SQLModel, create_engine, delete, select


class Record(SQLModel, table=True):
    kind: str = Field(primary_key=True)
    id: str = Field(primary_key=True)
    payload: dict = Field(sa_column=Column(JSON, nullable=False))


class SQLiteStore:
    def __init__(self, url: str):
        options = {"connect_args": {"check_same_thread": False}}
        if url.endswith(":memory:"):
            options["poolclass"] = StaticPool
        self.engine = create_engine(url, **options)
        SQLModel.metadata.create_all(self.engine)
        self._overview_lock = RLock()
        self._overview_cache: dict[tuple[str, int, str], list[dict]] = {}

    def cached_overview(self, key: tuple[str, int, str], compute: Callable[[], list[dict]]) -> list[dict]:
        with self._overview_lock:
            if key not in self._overview_cache:
                self._overview_cache[key] = compute()
            return self._overview_cache[key]

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
                if record:
                    record.payload = item
                else:
                    session.add(Record(kind=kind, id=item["id"], payload=item))
                session.commit()
            if kind in {"facility", "drug", "patient", "prescription", "stock_snapshot",
                        "daily_stock", "stockout_day", "dispensing", "case", "transfer"}:
                self._overview_cache.clear()

    def reset(self) -> None:
        with self._overview_lock:
            with Session(self.engine) as session:
                session.exec(delete(Record))
                session.commit()
            self._overview_cache.clear()
