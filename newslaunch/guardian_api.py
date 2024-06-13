from __future__ import annotations

import os
from datetime import datetime

import requests
from pydantic import AliasPath, BaseModel, Field, field_validator


class GuardianArticlePreview(BaseModel):
    """Represents a subset of fields to retrieve from the Guardian API response."""

    web_publication_date: str = Field(..., alias="webPublicationDate")
    web_title: str = Field(..., alias="webTitle")
    web_url: str = Field(..., alias="webUrl")
    content_preview: str = Field(
        ...,
        validation_alias=AliasPath("fields", "bodyText"),
        serialization_alias="contentPreview",
    )

    @field_validator("content_preview")
    @classmethod
    def truncate_article_content(cls, content: str) -> str:
        """Truncate the article content to 1000 characters."""
        if len(content) > 1000:
            preview = content[:1000].strip()
            if preview[-1].isalpha():
                return preview + "..."
            return preview.rstrip(",") + ("..." if preview[-1] != "." else "")
        else:
            return content


class GuardianAPIError(Exception):
    """Custom exception for Guardian API errors."""

    pass


class GuardianAPI:
    """Wrapper class for interacting with Guardian API.

    Args:
        api_key (str, optional): API access key. Reads from env if not provided.
        request_timeout (int, optional): HTTP request timeout. Defaults to 20s.
    """

    API_URL = "https://content.guardianapis.com"

    def __init__(self, api_key: str | None = None, request_timeout: int = 20):
        self.api_key = api_key or os.getenv("GUARDIAN_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Please provide it or set the 'GUARDIAN_API_KEY' environment variable."
            )
        self.request_timeout = request_timeout

    def search_articles(
        self,
        search_term: str,
        page_size: int | None = 10,
        from_date: str | None = None,
        filter_response: bool | None = True,
        order_by: str | None = None,
    ) -> list[dict] | None:
        """Search for Guardian articles.

        Args:
            search_term (str): The search query for articles.
            page_size (int, optional): The number of items displayed per page (up to 200). Defaults to 10.
            from_date (str, optional): The earliest publication date (YYYY-MM-DD format). Defaults to None.
            filter_response (bool, optional): Returns a filtered response if True, else returns the full response. Defaults to True.
            order_by (str, optional): The order to sort the articles by. Must be one of 'newest', 'oldest', 'relevance'. Defaults to 'relevance'.

        Returns:
            (list[dict] | None): A list of articles if found, None otherwise.

        Raises:
            ValueError:
                If search_term is empty or None.
                If from_date is provided but not in 'YYYY-MM-DD' format.
                If order_by is not in allowed values.
                If page_size exceed current API limit.
            GuardianAPIError:
                If an error occurs while fetching articles from the Guardian API.
        """
        if not search_term:
            raise ValueError("Search term required.")

        if order_by and order_by not in ["newest", "oldest", "relevance"]:
            raise ValueError(
                "The order_by must be one of 'newest', 'oldest', 'relevance'."
            )

        if page_size and (
            isinstance(page_size, int)
            and page_size > 200
            or not isinstance(page_size, int)
        ):
            raise ValueError("Page_size must be integer between 1-200.")
            # current API limit

        if from_date:
            try:
                datetime.strptime(from_date, "%Y-%m-%d")  # noqa: DTZ007
            except ValueError:
                raise ValueError("The from_date must be in the format YYYY-MM-DD.")

        req_params = {
            "q": search_term,
            "api-key": self.api_key,
            "format": "json",
            "show-fields": "all",
            "page-size": page_size,
        }

        if from_date:
            req_params["from-date"] = from_date

        if order_by:
            req_params["order-by"] = order_by

        try:
            response = requests.get(
                f"{self.API_URL}/search",
                params=req_params,
                timeout=self.request_timeout,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise GuardianAPIError(f"Error fetching Guardian articles: {e}")

        data = response.json()
        results = data.get("response", {}).get("results")

        if not results:
            return None

        if filter_response:
            filtered_results = [
                article.model_dump(by_alias=True)
                for article in self._filter_articles(results)
            ]
            return filtered_results
        else:
            return results

    def _filter_articles(self, articles: list[dict]) -> list[GuardianArticlePreview]:
        """Parse the API response and extract a subset of fields.

        Args:
            articles (list[dict]): List of articles from the API response.

        Returns:
            list[GuardianContent]: List of GuardianContent models representing parsed search results.
        """
        filtered_articles = [GuardianArticlePreview(**article) for article in articles]
        return filtered_articles
