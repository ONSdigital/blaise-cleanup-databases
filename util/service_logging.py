from google.cloud.logging_v2.handlers import StructuredLogHandler, setup_logging


def setupLogging() -> None:
    setup_logging(StructuredLogHandler())  # type: ignore[no-untyped-call]
