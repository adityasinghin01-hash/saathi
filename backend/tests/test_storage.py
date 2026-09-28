from app.storage.sqlite import SQLiteStore


def test_sqlite_store_persists_and_replaces_records(tmp_path):
    url = f"sqlite:///{tmp_path / 'demo.db'}"
    first = SQLiteStore(url)
    first.put("case", {"id": "one", "status": "reported"})
    first.put("case", {"id": "one", "status": "verified"})
    second = SQLiteStore(url)
    assert second.get("case", "one") == {"id": "one", "status": "verified"}
    assert second.list("case") == [{"id": "one", "status": "verified"}]
    assert second.get("case", "missing") is None
