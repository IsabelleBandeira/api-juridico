import logging
import os


def configurar_logs():
    nivel = os.getenv("LOG_LEVEL", "INFO").upper()

    logging.basicConfig(
        level=nivel,
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )