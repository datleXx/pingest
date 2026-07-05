from typing import Generator, Iterable
from pydantic import BaseModel, Field, ValidationError
from pingest.logging_helper.core import get_logger
import random

logger = get_logger(__name__)


class TaxiRecord(BaseModel):
    vendor_id: str
    pickup_datetime: str
    dropoff_datetime: str
    passenger_count: int = Field(ge=1)
    trip_distance: float = Field(ge=0.0)
    fare_amount: float
    tip_amount: float = 0.0
    pickup_lat: float = Field(ge=-90, le=90)
    pickup_lon: float = Field(ge=-180, le=180)
    dropoff_lat: float = Field(ge=-90, le=90)
    dropoff_lon: float = Field(ge=-180, le=180)


def validate(
    records: Iterable[dict], quarantine: list[dict]
) -> Generator[TaxiRecord, None, None]:
    for record in records:
        try:
            validated = TaxiRecord.model_validate(record)
            yield validated
        except ValidationError as e:
            quarantine.append({"record": record, "errors": e.errors()})
            logger.warning(
                f"Invalid record skipped: {e.error_count()} error(s) | {record}"
            )


def create_one_mock() -> TaxiRecord:
    return TaxiRecord(
        vendor_id="v1",
        pickup_datetime="test",
        dropoff_datetime="test",
        fare_amount=0.0,
        passenger_count=1,
        trip_distance=0.0,
        pickup_lat=random.uniform(40.5, 40.9),
        pickup_lon=random.uniform(-74.3, 73.7),
        dropoff_lat=random.uniform(40.5, 40.9),
        dropoff_lon=random.uniform(-74.3, 73.7),
    )
