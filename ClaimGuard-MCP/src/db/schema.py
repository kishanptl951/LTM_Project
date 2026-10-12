import logging

from src.db.session import get_db_connection

logger = logging.getLogger(__name__)


def initialize_database() -> None:
    """Create all application tables inside a single transaction."""
    logger.info("Initializing database schema...")

    with get_db_connection() as conn:
        conn.execute("BEGIN TRANSACTION")

        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS claims (
                    claim_id VARCHAR PRIMARY KEY,
                    policy_number VARCHAR NOT NULL,
                    claimant_name VARCHAR,
                    claim_type VARCHAR,
                    incident_date DATE,
                    reported_date DATE,
                    vehicle_registration VARCHAR,
                    status VARCHAR DEFAULT 'PENDING',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    document_id VARCHAR PRIMARY KEY,
                    claim_id VARCHAR NOT NULL,
                    document_type VARCHAR NOT NULL,
                    file_name VARCHAR NOT NULL,
                    file_path VARCHAR NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS extracted_evidence (
                    evidence_id VARCHAR PRIMARY KEY,
                    claim_id VARCHAR NOT NULL,
                    document_id VARCHAR NOT NULL,
                    field_name VARCHAR NOT NULL,
                    field_value VARCHAR,
                    confidence DOUBLE,
                    page_number INTEGER,
                    evidence_text VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS policy_evaluations (
                    evaluation_id VARCHAR PRIMARY KEY,
                    claim_id VARCHAR NOT NULL,
                    rule_id VARCHAR NOT NULL,
                    result VARCHAR NOT NULL,
                    explanation VARCHAR,
                    repair_cost DOUBLE,
                    coverage_limit DOUBLE,
                    deductible DOUBLE,
                    estimated_payable DOUBLE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Ensure backward-compatible migrations for existing databases
            for col in ["repair_cost", "coverage_limit", "deductible", "estimated_payable"]:
                try:
                    conn.execute(f"ALTER TABLE policy_evaluations ADD COLUMN IF NOT EXISTS {col} DOUBLE")
                except Exception:
                    pass

            conn.execute("""
                CREATE TABLE IF NOT EXISTS invariant_results (
                    result_id VARCHAR PRIMARY KEY,
                    claim_id VARCHAR NOT NULL,
                    invariant_id VARCHAR NOT NULL,
                    result VARCHAR NOT NULL,
                    severity VARCHAR,
                    explanation VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("COMMIT")
            logger.info("Database schema initialized successfully.")

        except Exception:
            conn.execute("ROLLBACK")
            logger.exception("Failed to initialize database schema.")
            raise