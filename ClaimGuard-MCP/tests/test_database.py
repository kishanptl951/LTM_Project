from src.db.schema import initialize_database
from src.db.session import get_db_connection


def test_database_initialization():
    initialize_database()

    with get_db_connection() as conn:

        tables = {
            row[0]
            for row in conn.execute("SHOW TABLES").fetchall()
        }

    expected_tables = {
        "claims",
        "documents",
        "extracted_evidence",
        "policy_evaluations",
        "invariant_results",
    }

    assert expected_tables.issubset(tables)