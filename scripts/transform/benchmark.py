from pingest.logging_helper.core import get_logger
from pingest.models import create_one_mock
from pingest.transforms.core import haversine, run_haversine_parallel
import time

logger = get_logger(__name__)


def main():
    mock_taxi_records = [create_one_mock() for _ in range(50_000)]
    logger.info("Start sequential transform, starting timer ... ")

    seq_start = time.perf_counter()

    extracted_records = [
        (r.pickup_lat, r.pickup_lon, r.dropoff_lat, r.dropoff_lon)
        for r in mock_taxi_records
    ]
    seq_result = [haversine(*args) for args in extracted_records]
    seq_end = time.perf_counter()
    seq_duration = (seq_end - seq_start) * 1000

    logger.info("Sequential transform done", extra={"duration_ms": seq_duration})

    logger.info("Start parallel transform, starting timer ... ")
    process_num = [1, 2, 4, 8]

    for process in process_num:
        run_haversine_parallel(mock_taxi_records, max_workers=process)


if __name__ == "__main__":
    main()
