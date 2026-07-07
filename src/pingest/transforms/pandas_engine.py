import pandas as pd


def clean(df: pd.DataFrame):
    df["pickup_datetime"] = pd.to_datetime(df["pickup_datetime"])
    df["dropoff_datetime"] = pd.to_datetime(df["dropoff_datetime"])
    df["trip_duration"] = (
        df["dropoff_datetime"] - df["pickup_datetime"]
    ).dt.total_seconds() / 60
    df["speed"] = df["trip_distance"] / (df["trip_duration"] / 60)
    df = df[(df["speed"] < 150) & (df["trip_distance"] > 0) & (df["trip_duration"] > 0)]

    df["passenger_count"] = pd.to_numeric(df["passenger_count"], downcast="integer")
    df[["trip_distance", "fare_amount", "tip_amount"]] = df[
        ["trip_distance", "fare_amount", "tip_amount"]
    ].apply(pd.to_numeric, downcast="float")

    return df


def enrich(df: pd.DataFrame, lookup: pd.DataFrame):
    return pd.merge(left=df, right=lookup, how="left", on="vendor_id")


def aggregate(df: pd.DataFrame):
    return df.groupby(["zone_name", df["pickup_datetime"].dt.date]).agg(
        revenue=("fare_amount", "sum")
    )
