from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.db.session import get_db_connection


def clean_test_data() -> None:
    conn = get_db_connection()

    conn.execute(
        "DELETE FROM invariant_results WHERE claim_id LIKE 'TEST-%'"
    )

    conn.execute(
        "DELETE FROM policy_evaluations WHERE claim_id LIKE 'TEST-%'"
    )

    conn.execute(
        "DELETE FROM extracted_evidence WHERE claim_id LIKE 'TEST-%'"
    )

    conn.execute(
        "DELETE FROM documents WHERE claim_id LIKE 'TEST-%'"
    )

    conn.execute(
        "DELETE FROM claims WHERE claim_id LIKE 'TEST-%'"
    )

    conn.close()

    print("Test data removed")


if __name__ == "__main__":
    clean_test_data()