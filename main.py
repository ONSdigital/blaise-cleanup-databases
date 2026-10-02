import logging
import os
from datetime import UTC, datetime, timedelta

import flask
import pymysql
import requests

LOGGER = logging.getLogger(__name__)
RETENTION_DAYS = 90
QUESTIONNAIRE_TABLES = ("CMA_Launcher_Form", "CMA_Attempts_Form")
LOGGING_TABLE = "CMA_Logging_Form"


def installed_questionnaires() -> set[str]:
    url = os.environ["QUESTIONNAIRES_URL"]
    headers = {}
    if token := os.environ.get("QUESTIONNAIRES_BEARER_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"

    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict):
        payload = payload.get("questionnaires")
    if not isinstance(payload, list):
        raise ValueError("Questionnaire API did not return a list")

    names: set[str] = set()
    for item in payload:
        name = item.get("name") if isinstance(item, dict) else item
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Questionnaire API returned an invalid name")
        names.add(name)
    if not names:
        raise ValueError("Questionnaire API returned no installed questionnaires")
    return names


def cleanup_tables(names: set[str], cutoff: datetime) -> dict[str, int]:
    connection = pymysql.connect(
        host=os.environ.get("DATABASE_HOST", "localhost"),
        port=int(os.environ.get("DATABASE_PORT", "3306")),
        unix_socket=os.environ.get("DATABASE_SOCKET"),
        user=os.environ["DATABASE_USER"],
        password=os.environ["DATABASE_PASSWORD"],
        database="blaise",
        charset="utf8mb4",
        autocommit=False,
    )
    deleted: dict[str, int] = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET time_zone = '+00:00'")
            cursor.execute(
                f"DELETE FROM `{LOGGING_TABLE}` WHERE `TimeCreated` < %s",
                (cutoff,),
            )
            deleted[LOGGING_TABLE] = cursor.rowcount
            placeholders = ", ".join(["%s"] * len(names))
            for table in QUESTIONNAIRE_TABLES:
                cursor.execute(
                    f"DELETE FROM `{table}` WHERE `TimeCreated` < %s "
                    f"AND `MainSurveyId` NOT IN ({placeholders})",
                    (cutoff, *sorted(names)),
                )
                deleted[table] = cursor.rowcount
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return deleted


def cma_database_cleanup(request: flask.Request) -> tuple[str, int]:
    """HTTP entry point for scheduled CMA database cleanup."""
    if request.method != "POST":
        return "Method not allowed", 405
    try:
        names = installed_questionnaires()
        cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=RETENTION_DAYS)
        deleted = cleanup_tables(names, cutoff)
    except Exception:
        LOGGER.exception("CMA cleanup failed")
        return "Cleanup failed", 500

    LOGGER.info("CMA cleanup completed; deleted=%s", deleted)
    return "OK", 200
