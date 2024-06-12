# ruff: noqa: B905
import json
import os
from unittest.mock import MagicMock, patch

import pytest
import requests

from newslaunch.guardian_api import GuardianAPI, GuardianAPIError


@pytest.fixture
def env_api_key(monkeypatch):
    monkeypatch.setenv("GUARDIAN_API_KEY", "test_api_key")
    return os.getenv("GUARDIAN_API_KEY")


@pytest.fixture
def guardian_api(env_api_key):
    return GuardianAPI(api_key=env_api_key)


@pytest.fixture
def sample_response():
    with open(
        os.path.join(os.path.dirname(__file__), "test_data/full_guardian_response.json")
    ) as f:
        return json.load(f)


@pytest.fixture
def filtered_sample_response():
    with open(
        os.path.join(
            os.path.dirname(__file__), "test_data/filtered_guardian_response.json"
        )
    ) as f:
        return json.load(f)


def test_guardian_api_with_env_key(guardian_api):
    assert guardian_api.api_key == "test_api_key"
    assert guardian_api.request_timeout == 20


def test_guardian_api_with_direct_key():
    api = GuardianAPI(api_key="explicit_api_key")
    assert api.api_key == "explicit_api_key"


def test_guardian_api_without_key_or_env_key(monkeypatch):
    monkeypatch.delenv("GUARDIAN_API_KEY", raising=False)
    with pytest.raises(ValueError):
        GuardianAPI()


def test_search_articles_no_search_term(guardian_api):
    with pytest.raises(ValueError):
        guardian_api.search_articles("")


def test_search_articles_invalid_order_by(guardian_api):
    with pytest.raises(ValueError):
        guardian_api.search_articles("test query", order_by="invalid_order")


def test_search_articles_invalid_page_size(guardian_api):
    with pytest.raises(ValueError):
        guardian_api.search_articles("test query", page_size=201)

    with pytest.raises(ValueError):
        guardian_api.search_articles("test query", page_size="not-int")


def test_search_articles_invalid_from_date(guardian_api):
    with pytest.raises(ValueError):
        guardian_api.search_articles("test query", from_date="not-a-date")

    with pytest.raises(ValueError):
        guardian_api.search_articles("test query", from_date="01-01-2012")


def test_search_articles_no_results_returns_none(guardian_api):
    empty_response = {"response": {"status": "ok", "results": []}}
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = empty_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        articles = guardian_api.search_articles("query-no-results")
        assert articles is None


@patch("requests.get")
def test_search_articles_api_error(mocked_get, guardian_api):
    mocked_get.side_effect = requests.RequestException("API error")

    with pytest.raises(GuardianAPIError):
        guardian_api.search_articles("error-search")
    mocked_get.assert_called_once()


def test_search_articles_filtered_response_default(
    guardian_api, sample_response, filtered_sample_response
):
    with patch("requests.get") as mocked_get:
        mock_response = MagicMock()
        mock_response.json.return_value = sample_response
        mock_response.status_code = 200
        mocked_get.return_value = mock_response

        articles = guardian_api.search_articles("test-query")

        assert articles is not None
        assert len(articles) == len(filtered_sample_response)
        for article, expected_article in zip(articles, filtered_sample_response):
            assert (
                article["webPublicationDate"] == expected_article["webPublicationDate"]
            )
            assert article["webTitle"] == expected_article["webTitle"]
            assert article["webUrl"] == expected_article["webUrl"]
            assert article["contentPreview"] == expected_article["contentPreview"]
            assert len(article["contentPreview"]) < 1005


def test_search_articles_full_response(guardian_api, sample_response):
    with patch("requests.get") as mocked_get:
        mock_response = MagicMock()
        mock_response.json.return_value = sample_response
        mock_response.status_code = 200
        mocked_get.return_value = mock_response

        articles = guardian_api.search_articles("test query", filter_response=False)

        assert articles is not None
        assert articles == sample_response.get("response", {}).get("results")
