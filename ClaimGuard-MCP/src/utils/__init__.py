import logging


def setup_logging(level: int = logging.INFO) -> None:
    """Configure project-wide logging with a consistent format."""

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
