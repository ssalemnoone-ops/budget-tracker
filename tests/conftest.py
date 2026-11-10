import pytest
import storage


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_FILE", tmp_path / "budget.db")
    storage.migrate_legacy_data()
