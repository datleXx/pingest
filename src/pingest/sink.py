import time
from typing import Iterator

import pyarrow as pa
import pyarrow.parquet as pq

from pingest.logging_helper.core import get_logger
from pingest.exception_helper.core import (
    SinkError,
)

logger = get_logger(__name__)

DEFAULT_BATCH_SIZE = 10_000


def _batched(
    records: Iterator[dict[str, str | None]], size: int
) -> Iterator[list[dict]]:
    """Group the record stream into lists of at most `size`.
    The trailing partial batch is yielded too — that's the final flush, for free."""
    batch: list[dict] = []
    for record in records:
        batch.append(record)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def write_parquet(
    records: Iterator[dict[str, str | None]],
    path: str,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> int:
    start = time.perf_counter()
    records_written = 0
    try:
        batches = _batched(records, batch_size)

        # Bootstrap: the writer needs a schema before any data, and the schema
        # comes from the first batch. No first batch => empty input.
        try:
            first = next(batches)
        except StopIteration:
            raise SinkError(f"no records to write to {path}")  # empty: chosen to raise

        first_table = pa.Table.from_pylist(first)
        schema = first_table.schema  # derive once...

        with pq.ParquetWriter(path, schema) as writer:  # `with` guarantees the footer
            writer.write_table(first_table)
            records_written += first_table.num_rows
            for batch in batches:
                table = pa.Table.from_pylist(
                    batch, schema=schema
                )  # ...force every batch into it
                writer.write_table(table)
                records_written += table.num_rows

        return records_written

    except (OSError, pa.ArrowException) as e:
        raise SinkError(f"failed to write parquet to {path}: {e}") from e
    finally:
        logger.info(
            "sink.write_complete",
            extra={
                "path": path,
                "records_written": records_written,
                "duration_ms": round((time.perf_counter() - start) * 1000, 2),
            },
        )



def write_parquet_partitioned(records, path, partition_cols, batch_size):
    records_written = 0
    start = time.perf_counter()
    try:
        batches = _batched(records, batch_size)

        for batch in batches:
            table = pa.Table.from_pylist(batch)
            pq.write_to_dataset(
                table,
                path,
                partition_cols=partition_cols,
                existing_data_behavior="overwrite_or_ignore",
            )
            records_written += table.num_rows

        return records_written

    except (OSError, pa.ArrowException) as e:
        raise SinkError(f"failed to write parquet to {path}: {e}") from e
    finally:
        logger.info(
            "sink.write_complete",
            extra={
                "path": path,
                "records_written": records_written,
                "duration_ms": round((time.perf_counter() - start) * 1000, 2),
            },
        )
