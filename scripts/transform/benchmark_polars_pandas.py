import time
import tracemalloc
import pyarrow.parquet as pq
import polars as pl

from pingest.transforms.pandas_engine import clean


def bench_pandas(path: str) -> dict:
    tracemalloc.start()
    start = time.perf_counter()
    pf = pq.ParquetFile(path)
    for batch in pf.iter_batches(batch_size=50_000):
        df = batch.to_pandas().rename(
            columns={
                "tpep_pickup_datetime": "pickup_datetime",
                "tpep_dropoff_datetime": "dropoff_datetime",
            }
        )
        clean(df)
    end = time.perf_counter()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {"runtime_ms": (end - start) * 1000, "peak_mb": peak / 1024 / 1024}


def bench_polars(path: str) -> dict:
    tracemalloc.start()
    start = time.perf_counter()

    pf = pl.scan_parquet(path).rename(
        {
            "tpep_pickup_datetime": "pickup_datetime",
            "tpep_dropoff_datetime": "dropoff_datetime",
        }
    )

    pf = pf.with_columns(
        (
            (pl.col("dropoff_datetime") - pl.col("pickup_datetime")).dt.total_seconds()
            / 60
        ).alias("trip_duration"),
    )

    pf = pf.with_columns(
        (pl.col("trip_distance") / (pl.col("trip_duration") / 60)).alias("speed"),
    )

    pf = pf.filter(
        (pl.col("trip_distance") > 0),
        ((pl.col("speed") > 0) & (pl.col("speed") < 150)),
        (pl.col("trip_duration") > 0),
    ).with_columns(
        pl.col("passenger_count").cast(pl.Int32),
        *[
            pl.col(col).cast(pl.Float32)
            for col in ["fare_amount", "tip_amount", "trip_distance"]
        ],
    )

    pf = pf.collect(engine="streaming")
    end = time.perf_counter()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop

    return {"runtime_ms": (end - start) * 1000, "peak_mb": peak / 1024 / 1024}


def main():
    path = "data/yellow_tripdata_2026-05.parquet"
    pandas_res = bench_pandas(path)
    polars_res = bench_polars(path)
    print(f"{'Engine':<20} {'Runtime (ms)':<20} {'Peak RAM (MB)':<15}")
    print(
        f"{'pandas-chunked':<20} {pandas_res['runtime_ms']:<20.1f} {pandas_res['peak_mb']:<15.1f}"
    )
    print(
        f"{'polars-lazy':<20} {polars_res['runtime_ms']:<20.1f} {polars_res['peak_mb']:<15.1f}"
    )


if __name__ == "__main__":
    main()
