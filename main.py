import logging
from datetime import UTC, datetime, timedelta

import flask
import pymysql

from config import Settings
from models.blaise_config_model import BlaiseConfig
from services.blaise_service import BlaiseService

LOGGER = logging.getLogger(__name__)
QUESTIONNAIRE_TABLES = ("CMA_Launcher_Form", "CMA_Attempts_Form")
LOGGING_TABLE = "CMA_Logging_Form"


def installed_questionnaire_guids() -> set[str]:
    service = BlaiseService(BlaiseConfig.from_env())
    return set(service.get_guid_of_questionnaire_in_blaise())


def cleanup_tables(guids: set[str], cutoff: datetime) -> dict[str, int]:
    if not guids:
        raise ValueError("No installed questionnaire GUIDs; refusing to delete data")

    previewed: dict[str, int] = {}
    placeholders = ", ".join(["%s"] * len(guids))
    connection = pymysql.connect(
        host=Settings.DATABASE_IP_ADDRESS,
        port=Settings.DATABASE_PORT,
        user=Settings.DATABASE_USER,
        password=Settings.DATABASE_PASSWORD,
        database="blaise",
        charset="utf8mb4",
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET time_zone = '+00:00'")
            # cursor.execute(
            #     f"DELETE FROM `{LOGGING_TABLE}` "
            #     "WHERE `TimeCreated` < %s "
            #     "AND (`LastModification` IS NULL OR `LastModification` < %s)",
            #     (cutoff, cutoff),
            # )
            cursor.execute(
                f"SELECT * FROM `{LOGGING_TABLE}` "
                "WHERE `TimeCreated` < %s "
                "AND (`LastModification` IS NULL OR `LastModification` < %s)",
                (cutoff, cutoff),
            )
            rows = [
                dict(zip((column[0] for column in cursor.description), row, strict=True))
                for row in cursor.fetchall()
            ]
            print(f"{LOGGING_TABLE} matching rows ({len(rows)}): {rows}")
            previewed[LOGGING_TABLE] = len(rows)
            for table in QUESTIONNAIRE_TABLES:
                # cursor.execute(
                #     f"DELETE FROM `{table}` WHERE `TimeCreated` < %s "
                #     f"AND (`MainSurveyID` IS NULL OR "
                #     f"`MainSurveyID` NOT IN ({placeholders}))",
                #     (cutoff, *sorted(guids)),
                # )
                cursor.execute(
                    f"SELECT * FROM `{table}` WHERE `TimeCreated` < %s "
                    f"AND (`MainSurveyID` IS NULL OR "
                    f"`MainSurveyID` NOT IN ({placeholders}))",
                    (cutoff, *sorted(guids)),
                )
                rows = [
                    dict(zip((column[0] for column in cursor.description), row, strict=True))
                    for row in cursor.fetchall()
                ]
                print(f"{table} matching rows ({len(rows)}): {rows}")
                previewed[table] = len(rows)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return previewed


def cma_database_cleanup(request: flask.Request) -> tuple[str, int]:
    """HTTP entry point for scheduled CMA database cleanup."""
    if request.method != "POST":
        return "Method not allowed", 405
    try:
        guids = installed_questionnaire_guids()
        threshold = Settings.CMA_TIME_THRESHOLD
        if threshold <= 0:
            raise ValueError("CMA_TIME_THRESHOLD must be greater than zero")
        cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=threshold)
        previewed = cleanup_tables(guids, cutoff)
    except Exception:
        LOGGER.exception("CMA cleanup failed")
        return "Cleanup failed", 500

    
    print(f"CMA cleanup preview completed; matching_rows={previewed}")
    LOGGER.info("CMA cleanup preview completed; matching_rows=%s", previewed)
    return "OK", 200
