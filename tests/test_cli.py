import json
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
from click.testing import CliRunner

from newslaunch.cli import cli
from newslaunch.guardian_api import GuardianAPI, GuardianAPIError


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_config():
    with patch.object(Path, "exists") as mock_exists_config, patch(
        "builtins.open",
        mock_open(read_data=json.dumps({"guardian": "test_guardian_api_key"})),
    ):
        mock_exists_config.return_value = True
        yield


def test_version(runner):
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.output


def test_no_api_key_set(runner):
    with patch.object(Path, "exists") as mock_exists:
        mock_exists.return_value = False
        result = runner.invoke(cli, ["guardian", "test search"])
        assert result.exit_code == 1
        assert (
            "Guardian API key not found. Please add it using 'newslaunch set-key --guardian <API_KEY>'."
            in result.output
        )


def test_set_key_guardian(runner):
    with patch.object(Path, "exists") as mock_exists, patch(
        "builtins.open", mock_open()
    ) as mock_file, patch("newslaunch.cli.json.dump") as mock_json_dump:
        mock_exists.return_value = False
        result = runner.invoke(cli, ["set-key", "--guardian", "test_guardian_api_key"])
        assert result.exit_code == 0
        assert "Guardian API key saved" in result.output
        mock_json_dump.assert_called_once_with(
            {"guardian": "test_guardian_api_key"}, mock_file()
        )


def test_guardian_search_articles_no_results(runner, mock_config):
    with patch.object(GuardianAPI, "search_articles", return_value=None):
        result = runner.invoke(cli, ["guardian", "test search"])
        assert result.exit_code == 0
        assert "No articles found." in result.output


def test_guardian_search_invalid_date(runner, mock_config):
    result = runner.invoke(
        cli, ["guardian", "test search", "--from-date", "invalid-date"]
    )
    assert result.exit_code == 1
    assert "Error: The from_date must be in the format YYYY-MM-DD.\n" in result.output


def test_guardian_search_articles_api_error(runner, mock_config):
    with patch.object(
        GuardianAPI, "search_articles", side_effect=GuardianAPIError("API error")
    ):
        result = runner.invoke(cli, ["guardian", "test search"])
        assert result.exit_code == 1
        assert "Error: API error" in result.output


def test_guardian_search_articles_success(runner, mock_config):
    mock_response = [
        {
            "webPublicationDate": "2023-01-01T11:11:11Z",
            "webTitle": "Test Article",
            "webUrl": "https://www.theguardian.com/test-article",
            "contentPreview": "This is a shortened preview of the test article.",
        }
    ]

    with patch.object(GuardianAPI, "search_articles", return_value=mock_response):
        result = runner.invoke(cli, ["guardian", "test search"])
        assert result.exit_code == 0
        assert json.dumps(mock_response, indent=4) in result.output
