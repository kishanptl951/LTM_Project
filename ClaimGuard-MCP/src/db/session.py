import logging
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import duckdb

from src.config import settings

logger = logging.getLogger(__name__)


@contextmanager
def get_db_connection(read_only: bool = False) -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Yield a DuckDB connection that is guaranteed to close on exit."""
    database_path = Path(settings.database_path)

    database_path.parent.mkdir(parents=True, exist_ok=True)

    logger.debug("Opening DuckDB connection (read_only=%s): %s", read_only, database_path)
    try:
        conn = duckdb.connect(str(database_path), read_only=read_only)
    except duckdb.IOException:
        # If write lock was contested but caller can accept read_only, fallback
        if not read_only:
            raise
        conn = duckdb.connect(str(database_path), read_only=True)

    try:
        yield conn
    finally:
        conn.close()
        logger.debug("Closed DuckDB connection: %s", database_path)