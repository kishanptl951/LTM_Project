import pytest

from src.db.schema import initialize_database
from src.db.session import get_db_connection


@pytest.fixture(autouse=True)
def clean_test_database(tmp_path, monkeypatch):
    test_database = tmp_path / "test_claimguard.duckdb"

    monkeypatch.setattr(
        "src.config.settings.database_path",
        str(test_database),
    )

    initialize_database()

    yield