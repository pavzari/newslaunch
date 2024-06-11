from datetime import datetime
import os

import requests
from pydantic import AliasPath, BaseModel, Field, field_validator


class GuardianArticlePreview(BaseModel):
    """Represents fields to retrieve from the Guardian API response."""

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
    """
    Wrapper class for interacting with Guardian API.

    Attributes:
    api_key (str): API access key.
    """

    API_URL = "https://content.guardianapis.com"

    def __init__(self, api_key: str, request_timeout: int = 20):
        self.api_key = api_key or os.getenv("GUARDIAN_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Please provide it or set the 'GUARDIAN_API_KEY' environment variable."
            )
        self.request_timeout = request_timeout

    def search_articles(
        self,
        search_term: str,
        from_date: str | None = None,
        response_format: str = "json",
        filter_response: bool = True,
        page: int = 1,
    ) -> list[dict] | None:
        """
        Search for Guardian articles.

        Parameters:
        search_term (str): The search query for articles.
        from_date (str | None, optional): The earliest publication date (YYYY-MM-DD format). Defaults to None.
        response_format (str, optional): The format of the API response. Defaults to 'json'.
        filter_response (bool): Returns a filtered response if True, else returns the full response. Defaults to True.
        page (int, optional): The page number of the search results to retrieve. Defaults to 1.

        Returns:
        list[dict] | None: A list of 10 parsed articles if found, None otherwise.

        Raises:
        ValueError: If search_term is empty or None.
        ValueError: If from_date is provided but not in 'YYYY-MM-DD' format.
        GuardianAPIError: If an error occurs while fetching articles from the Guardian API.
        """
        if not search_term:
            raise ValueError("Search term parameter required.")

        if from_date:
            try:
                datetime.strptime(from_date, "%Y-%m-%d")
            except ValueError:
                raise ValueError("The from_date must be in the format YYYY-MM-DD.")

        req_params = {
            "q": search_term,
            "api-key": self.api_key,
            "format": response_format,
            "page": page,
            "show-fields": "all",
        }

        if from_date:
            req_params["from-date"] = from_date

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
        """
        Parse the API response and extract required fields.

        Parameters:
        articles (list[dict]): List of articles from the API response.

        Returns:
        list[GuardianContent]: list of GuardianContent models representing parsed search results.
        """
        filtered_articles = []
        for article in articles:
            filtered_articles.append(GuardianArticlePreview(**article))
        return filtered_articles
