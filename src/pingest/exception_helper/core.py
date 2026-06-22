from typing import Any


class IngestError(Exception):
    pass


class SourceError(IngestError):
    pass


class ValidationError(IngestError):
    def __init__(self, record: dict[str, Any], field: str, reason: str) -> None:
        self.record = record
        self.field = field
        self.reason = reason
        super().__init__(
            f"Record: \n{record} \nfailed, the {field} field, reason: {reason}"
        )
