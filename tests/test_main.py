import sys
from datetime import datetime
from unittest.mock import MagicMock

import pytest

sys.modules.setdefault("pymysql", MagicMock())

import main  # noqa: E402


def test_installed_questionnaires_rejects_empty_list(monkeypatch):
    response = MagicMock()
    response.json.return_value = {"questionnaires": []}
    monkeypatch.setenv("QUESTIONNAIRES_URL", "https://example.invalid/questionnaires")
    monkeypatch.setattr(main.requests, "get", MagicMock(return_value=response))

    with pytest.raises(ValueError, match="no installed questionnaires"):
        main.installed_questionnaires()


def test_installed_questionnaires_reads_names(monkeypatch):
    response = MagicMock()
    response.json.return_value = {"questionnaires": [{"name": "SurveyA"}, "SurveyB"]}
    monkeypatch.setenv("QUESTIONNAIRES_URL", "https://example.invalid/questionnaires")
    get = MagicMock(return_value=response)
    monkeypatch.setattr(main.requests, "get", get)

    assert main.installed_questionnaires() == {"SurveyA", "SurveyB"}
    get.assert_called_once_with(
        "https://example.invalid/questionnaires", headers={}, timeout=15
    )


def test_cleanup_tables_filters_age_and_installed_questionnaires(monkeypatch):
    cursor = MagicMock()
    cursor.rowcount = 2
    connection = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    monkeypatch.setattr(main.pymysql, "connect", MagicMock(return_value=connection))
    monkeypatch.setenv("DATABASE_USER", "test")
    monkeypatch.setenv("DATABASE_PASSWORD", "test")
    cutoff = datetime(2026, 7, 4)

    deleted = main.cleanup_tables({"SurveyB", "SurveyA"}, cutoff)

    assert deleted == {
        "CMA_Logging_Form": 2,
        "CMA_Launcher_Form": 2,
        "CMA_Attempts_Form": 2,
    }
    statements = cursor.execute.call_args_list
    assert "SET time_zone" in statements[0].args[0]
    assert statements[1].args == (
        "DELETE FROM `CMA_Logging_Form` WHERE `TimeCreated` < %s",
        (cutoff,),
    )
    for call, table in zip(statements[2:], main.QUESTIONNAIRE_TABLES, strict=True):
        assert call.args == (
            f"DELETE FROM `{table}` WHERE `TimeCreated` < %s "
            "AND `MainSurveyId` NOT IN (%s, %s)",
            (cutoff, "SurveyA", "SurveyB"),
        )
    connection.commit.assert_called_once()
    connection.close.assert_called_once()


def test_cleanup_rolls_back_if_a_delete_fails(monkeypatch):
    cursor = MagicMock()
    cursor.execute.side_effect = [None, None, RuntimeError("database failed")]
    connection = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    monkeypatch.setattr(main.pymysql, "connect", MagicMock(return_value=connection))
    monkeypatch.setenv("DATABASE_USER", "test")
    monkeypatch.setenv("DATABASE_PASSWORD", "test")

    with pytest.raises(RuntimeError, match="database failed"):
        main.cleanup_tables({"SurveyA"}, datetime(2026, 7, 4))

    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()
    connection.close.assert_called_once()


def test_handler_does_not_delete_when_questionnaire_fetch_fails(monkeypatch):
    monkeypatch.setattr(
        main, "installed_questionnaires", lambda: (_ for _ in ()).throw(ValueError())
    )
    cleanup = MagicMock()
    monkeypatch.setattr(main, "cleanup_tables", cleanup)
    request = MagicMock(method="POST")

    assert main.cma_database_cleanup(request) == ("Cleanup failed", 500)
    cleanup.assert_not_called()


def test_handler_rejects_get_without_fetching(monkeypatch):
    fetch = MagicMock()
    monkeypatch.setattr(main, "installed_questionnaires", fetch)

    assert main.cma_database_cleanup(MagicMock(method="GET")) == (
        "Method not allowed",
        405,
    )
    fetch.assert_not_called()


def test_handler_uses_90_day_cutoff(monkeypatch):
    monkeypatch.setattr(main, "installed_questionnaires", lambda: {"SurveyA"})
    cleanup = MagicMock(return_value={})
    monkeypatch.setattr(main, "cleanup_tables", cleanup)
    before = main.datetime.now(main.UTC)

    assert main.cma_database_cleanup(MagicMock(method="POST")) == ("OK", 200)

    after = main.datetime.now(main.UTC)
    names, cutoff = cleanup.call_args.args
    assert names == {"SurveyA"}
    assert before - main.timedelta(days=90) <= cutoff.replace(tzinfo=main.UTC)
    assert cutoff.replace(tzinfo=main.UTC) <= after - main.timedelta(days=90)
