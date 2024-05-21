import json
from datetime import datetime

import requests
from config import get_config
from pydantic import AliasPath, BaseModel, Field, HttpUrl, field_validator


class GuardianContent(BaseModel):
    """Represents fields to retrieve from the Guardian API response."""

    web_publication_date: str = Field(..., alias="webPublicationDate")
    web_title: str = Field(..., alias="webTitle")
    web_url: HttpUrl = Field(..., alias="webUrl")
    content_preview: str = Field(
        ...,
        validation_alias=AliasPath("fields", "bodyText"),
        serialization_alias="contentPreview",
    )

    @field_validator("content_preview")
    @classmethod
    def truncate_article_content(cls, content: str) -> str:
        if len(content) > 1000:
            return content[:1000]
        else:
            return content


class GuardianAPIError(Exception):
    """Custom exception for Guardian API errors."""

    pass


class GuardianAPI:
    API_URL = "https://content.guardianapis.com"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_articles(
        self,
        search_term: str,
        from_date: str | None = None,
        response_format: str = "json",
        page: int = 1,
    ) -> str:
        """
        Search for Guardian articles.

        Parameters:
        search_term (str): The search query for articles.
        from_date (str | None, optional): The earliest publication date in the search results (YYYY-MM-DD format). Defaults to None.
        response_format (str, optional): The format of the API response. Defaults to 'json'.
        page (int, optional): The page number of the search results to retrieve. Defaults to 1.

        Returns:
        A serialized JSON string of 10 parsed articles.
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
                timeout=get_config().HTTP_REQ_TIMEOUT,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise GuardianAPIError(f"Error fetching Guardian articles: {e}")

        data = response.json()
        results = data.get("response", {}).get("results", [])
        parsed_results = [
            article.model_dump_json(by_alias=True)
            for article in self._parse_articles(results)
        ]
        return json.dumps(parsed_results)

    def _parse_articles(self, articles: list[dict]) -> list[GuardianContent]:
        """
        Parse the API response and extract required fields.

        Parameters:
        articles (list[dict]): List of articles from the API response.

        Returns:
        A list of GuardianContent models representing parsed search results.
        """
        parsed_articles = []
        for article in articles:
            parsed_articles.append(GuardianContent(**article))
        return parsed_articles


if __name__ == "__main__":
    guardian_api = GuardianAPI(get_config().GUARDIAN_API_KEY)
    articles = guardian_api.get_articles("machine learning", "2023-01-01")
    print(articles)
