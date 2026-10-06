from datetime import datetime
from unittest.mock import MagicMock

import pytest

import main


def _set_database_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_IP_ADDRESS", "10.0.0.5")
    monkeypatch.setenv("DATABASE_PORT", "3306")
    monkeypatch.setenv("DATABASE_USER", "cleanup-service-account")
    monkeypatch.setenv("DATABASE_PASSWORD", "secret-password")


def _mock_connection(monkeypatch, cursor):
    connection = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    monkeypatch.setattr(main.pymysql, "connect", MagicMock(return_value=connection))
    return connection


def test_installed_questionnaire_guids_uses_blaise_service(monkeypatch):
    service = MagicMock()
    service.get_guid_of_questionnaire_in_blaise.return_value = ["guid-a"]
    service_factory = MagicMock(return_value=service)
    config = MagicMock()
    config_factory = MagicMock(return_value=config)
    monkeypatch.setattr(main, "BlaiseService", service_factory)
    monkeypatch.setattr(main.BlaiseConfig, "from_env", config_factory)

    assert main.installed_questionnaire_guids() == {"guid-a"}

    config_factory.assert_called_once_with()
    service_factory.assert_called_once_with(config)
    service.get_guid_of_questionnaire_in_blaise.assert_called_once_with()


def test_cleanup_tables_previews_only_eligible_records(monkeypatch, capsys):
    _set_database_environment(monkeypatch)
    cursor = MagicMock()
    cursor.description = (("RecordId",),)
    cursor.fetchall.return_value = [(1,), (2,)]
    connection = _mock_connection(monkeypatch, cursor)
    cutoff = datetime(2026, 7, 4)

    previewed = main.cleanup_tables({"guid-b", "guid-a"}, cutoff)

    assert previewed == {
        "CMA_Logging_Form": 2,
        "CMA_Launcher_Form": 2,
        "CMA_Attempts_Form": 2,
    }
    statements = cursor.execute.call_args_list
    assert "SET time_zone" in statements[0].args[0]
    expected_preview_count = len(main.QUESTIONNAIRE_TABLES) + 1
    assert statements[1].args == (
        "SELECT * FROM `CMA_Logging_Form` WHERE `TimeCreated` < %s "
        "AND (`LastModification` IS NULL OR `LastModification` < %s)",
        (cutoff, cutoff),
    )
    for call, table in zip(statements[2:], main.QUESTIONNAIRE_TABLES, strict=True):
        assert call.args == (
            f"SELECT * FROM `{table}` WHERE `TimeCreated` < %s "
            "AND (`MainSurveyID` IS NULL OR `MainSurveyID` NOT IN (%s, %s))",
            (cutoff, "guid-a", "guid-b"),
        )
    main.pymysql.connect.assert_called_once_with(
        host="10.0.0.5",
        port=3306,
        user="cleanup-service-account",
        password="secret-password",
        database="blaise",
        charset="utf8mb4",
    )
    assert cursor.fetchall.call_count == expected_preview_count
    output = capsys.readouterr().out
    assert output.count("matching rows (2)") == expected_preview_count
    assert "{'RecordId': 1}" in output
    connection.commit.assert_not_called()
    connection.close.assert_called_once()


def test_cleanup_tables_refuses_empty_questionnaire_list():
    with pytest.raises(ValueError, match="No installed questionnaire GUIDs"):
        main.cleanup_tables(set(), datetime(2026, 7, 4))


def test_cleanup_rolls_back_if_a_preview_query_fails(monkeypatch):
    _set_database_environment(monkeypatch)
    cursor = MagicMock()
    cursor.execute.side_effect = [None, None, RuntimeError("database failed")]
    connection = _mock_connection(monkeypatch, cursor)

    with pytest.raises(RuntimeError, match="database failed"):
        main.cleanup_tables({"guid-a"}, datetime(2026, 7, 4))

    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()
    connection.close.assert_called_once()


def test_handler_does_not_delete_when_questionnaire_fetch_fails(monkeypatch):
    monkeypatch.setattr(
        main,
        "installed_questionnaire_guids",
        lambda: (_ for _ in ()).throw(ValueError()),
    )
    cleanup = MagicMock()
    monkeypatch.setattr(main, "cleanup_tables", cleanup)
    request = MagicMock(method="POST")

    assert main.cma_database_cleanup(request) == ("Cleanup failed", 500)
    cleanup.assert_not_called()


def test_handler_rejects_get_without_fetching(monkeypatch):
    fetch = MagicMock()
    monkeypatch.setattr(main, "installed_questionnaire_guids", fetch)

    assert main.cma_database_cleanup(MagicMock(method="GET")) == (
        "Method not allowed",
        405,
    )
    fetch.assert_not_called()


def test_handler_uses_configured_cutoff(monkeypatch):
    monkeypatch.setenv("CMA_TIME_THRESHOLD", "45")
    monkeypatch.setattr(main, "installed_questionnaire_guids", lambda: {"guid-a"})
    cleanup = MagicMock(return_value={})
    monkeypatch.setattr(main, "cleanup_tables", cleanup)
    before = main.datetime.now(main.UTC)

    assert main.cma_database_cleanup(MagicMock(method="POST")) == ("OK", 200)

    after = main.datetime.now(main.UTC)
    names, cutoff = cleanup.call_args.args
    assert names == {"guid-a"}
    assert before - main.timedelta(days=45) <= cutoff.replace(tzinfo=main.UTC)
    assert cutoff.replace(tzinfo=main.UTC) <= after - main.timedelta(days=45)


def test_handler_rejects_nonpositive_retention_threshold(monkeypatch):
    monkeypatch.setenv("CMA_TIME_THRESHOLD", "0")
    monkeypatch.setattr(main, "installed_questionnaire_guids", lambda: {"guid-a"})
    cleanup = MagicMock()
    monkeypatch.setattr(main, "cleanup_tables", cleanup)

    assert main.cma_database_cleanup(MagicMock(method="POST")) == (
        "Cleanup failed",
        500,
    )
    cleanup.assert_not_called()
