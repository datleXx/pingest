from pingest.logging_helper.core import get_logger
from pingest.models import create_one_mock
import pandas as pd

from pingest.transforms.pandas_engine import aggregate, clean, enrich


logger = get_logger(__name__)


def main():
    mock_records = [create_one_mock() for _ in range(4)]

    d_frames = pd.DataFrame([r.model_dump() for r in mock_records])

    logger.info("Set up done", extra={"data": d_frames})

    cleaned = clean(d_frames)

    logger.info("Clean up done", extra={"data": cleaned})

    lookup = pd.DataFrame({"vendor_id": ["v1"], "zone_name": ["HaNoi"]})

    enriched = enrich(cleaned, lookup)

    logger.info("Enrich done", extra={"data": enriched})

    aggregated = aggregate(enriched)

    logger.info("Aggregate done", extra={"data": aggregated})


if __name__ == "__main__":
    main()
