import csv
from pingest.logging_helper.core import get_logger
from pingest.observability import timed
from pingest.exception_helper.core import SourceError


logger = get_logger(__name__)


@timed
def read_file(path: str):
    try:
        with open(path, encoding="utf-8") as f:
            file = csv.DictReader(f)
            for row in file:
                yield row
    except (OSError, UnicodeDecodeError, csv.Error) as e:
        raise SourceError(f"failed on path {path}: {e}") from e
    finally:
        logger.info(
            "source.read_complete",
            extra={
                "path": path,
            },
        )
