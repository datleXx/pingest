import polars as pl

from pingest.transforms.polars_engine import clean
from pingest.logging_helper.core import get_logger

"""
1. Create scripts/transform/test_polars.py
2. Import polars as pl and clean from pingest.transforms.polars_engine
3. Read the parquet file: pl.read_parquet("data/yellow_tripdata_2026-05.parquet")
4. Rename two columns:
  - tpep_pickup_datetime → pickup_datetime
  - tpep_dropoff_datetime → dropoff_datetime
5. Pass the renamed DataFrame into clean()
6. Print the shape of the result with print(df.shape)
7. Print the first 5 rows with print(df.head())
8. Run it: uv run python scripts/transform/test_polars.py
9. Paste the output here
"""

logger = get_logger(__name__)


def main():
    pf = pl.read_parquet("data/yellow_tripdata_2026-05.parquet")
    pf = pf.rename(
        {
            "tpep_pickup_datetime": "pickup_datetime",
            "tpep_dropoff_datetime": "dropoff_datetime",
        }
    )

    pf = clean(pf)
    logger.info("Clean polars done", extra={"shape": pf.shape, "head": pf.head(5)})


if __name__ == "__main__":
    main()
