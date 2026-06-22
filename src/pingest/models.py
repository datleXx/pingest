from typing import Generator, Iterable
from pydantic import BaseModel, Field, ValidationError
from pingest.logging_helper.core import get_logger

logger = get_logger(__name__)


class TaxiRecord(BaseModel):
    vendor_id: str
    pickup_datetime: str
    dropoff_datetime: str
    passenger_count: int = Field(ge=1)
    trip_distance: float = Field(ge=0.0)
    fare_amount: float
    tip_amount: float = 0.0


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
