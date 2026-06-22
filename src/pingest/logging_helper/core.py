import logging, json


class JsonFormatter(logging.Formatter):
    _STANDARDS = logging.makeLogRecord({}).__dict__

    def format(self, record):
        extra_fields = {
            k: v for k, v in record.__dict__.items() if k not in self._STANDARDS
        }
        log = {
            "time": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            **extra_fields,
        }

        return json.dumps(log, default=str)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler) and isinstance(
            handler, JsonFormatter
        ):
            return logger

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)

    return logger
