"""
1. Read the parquet file into a DataFrame with pd.read_parquet
2. Run it through your clean() function from pandas_engine.py
3. Print how many rows survived
"""

import pandas as pd
from pingest.sink import write_parquet_partitioned
from pingest.transforms.pandas_engine import clean
from pingest.logging_helper.core import get_logger
import tracemalloc
import pyarrow.parquet as pd

logger = get_logger(__name__)


def main():
    tracemalloc.start()

    path = "data/yellow_tripdata_2026-05.parquet"
    pf = pd.ParquetFile(path)
    count = 0

    for batch in pf.iter_batches(batch_size=50_000):
        df = batch.to_pandas().rename(
            columns={
                "tpep_pickup_datetime": "pickup_datetime",
                "tpep_dropoff_datetime": "dropoff_datetime",
            }
        )
        df = clean(df)
        df["pickup_date"] = df["pickup_datetime"].dt.date
        write_parquet_partitioned(
            df.to_dict(orient="records"), "data/out", ["pickup_date"], 50_000
        )
        count += df.shape[0]

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    logger.info(f"Peak memory: {peak / 1024 / 1024:.1f} MB", extra={"Records": count})


if __name__ == "__main__":
    main()
