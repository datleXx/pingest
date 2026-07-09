import polars as pl


def clean(pf: pl.DataFrame) -> pl.DataFrame:
    for col in ["pickup_datetime", "dropoff_datetime"]:
        if pf.schema[col] == pl.Utf8:
            pf = pf.with_columns(pl.col(col).str.to_datetime())

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

    return pf


def enrich(left: pl.DataFrame, right: pl.DataFrame) -> pl.DataFrame:
    return left.join(right, how="left", on="vendor_id")


def aggregate(pf: pl.DataFrame) -> pl.DataFrame:
    return pf.group_by("zone_name", pl.col("pickup_datetime").dt.date()).agg(
        pl.col("fare_amount").sum().alias("revenue")
    )
