import polars as pl

"""
  1. Use pl.scan_parquet instead of pl.read_parquet
  2. Rename columns with .rename()
  3. Chain with_columns → filter → with_columns (casting) directly on the LazyFrame — no clean() function, write it inline
  4. Call .collect(engine="streaming") at the end
  5. Print the shape
"""


def main():
    pf = pl.scan_parquet("data/yellow_tripdata_2026-05.parquet").rename(
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

    print(f"Explain: {pf.explain()}")
    pf = pf.collect(engine="streaming")
    print(f"Shape: {pf.shape}")


if __name__ == "__main__":
    main()
