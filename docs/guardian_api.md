## Overview

The `guardian_api` module provides a simple wrapper class for interacting with the Guardian API, allowing users to search for articles based on various criteria.

## Classes

### GuardianAPI

A wrapper class for the Guardian API, enables article search with customizable parameters.

#### Initialization

```python
GuardianAPI(api_key: str | None = None, request_timeout: int = 20)
```

**Parameters:**

- `api_key` (str, optional): The API key for accessing the Guardian API. If not provided directly, it is read from the `GUARDIAN_API_KEY` environment variable.
- `request_timeout` (int, optional): Timeout for HTTP requests in seconds. Defaults to 20 seconds.

**Raises:**

- `GuardianAPIError`: If the API key is not found during initialization.

#### Example:

```python
from newslaunch.guardian_api import GuardianAPI

# Using API key from the environment
api = GuardianAPI()

# Passing API key directly
api = GuardianAPI(api_key="your_api_key", request_timeout=60)
```

### Methods

#### `search_articles`

Search for articles using the Guardian API based on the provided criteria.

```python
search_articles(
    search_term: str,
    page_size: int | None = 10,
    from_date: str | None = None,
    filter_response: bool | None = True,
    order_by: str | None = None
) -> list[dict] | None
```

**Parameters:**

- `search_term` (str): The search query for articles. Supports AND, OR, and NOT operators, and exact phrase queries using double quotes. Example: `smoothies`, `"fruit smoothies"`, `smoothies AND (berries OR spinach)`, `smoothies AND NOT (dairy OR sugar)`.
- `page_size` (int, optional): The number of items displayed per query (up to 200). Defaults to 10.
- `from_date` (str, optional): The earliest publication date (YYYY-MM-DD format). Defaults to None.
- `filter_response` (bool, optional): Returns a filtered response if True, else returns the full API response. Defaults to True.
- `order_by` (str, optional): The order to sort the articles by. Must be one of 'newest', 'oldest', 'relevance'. Defaults to 'relevance'.

**Returns:**

- `list[dict] | None`: A list of articles if found, None if no articles matching the
  criteria are found.

**Raises:**

- `GuardianAPIError`: If parameter validation fails or if an error occurs while fetching articles from the Guardian API.

**Examples:**

```python
# Search articles with default settings
articles = api.search_articles('"machine learning"')

# Search articles with custom page size and date filter
articles = api.search_articles(
    "python AND programming",
    page_size=20,
    from_date="2023-01-01"
)

# Search articles with specific order
articles = api.search_articles(
    "health",
    order_by="newest"
)

# Get full API response without filtering
articles = api.search_articles(
    "science",
    filter_response=False
)
```

### Custom Exceptions

#### `GuardianAPIError`

A custom exception class for handling errors related to the Guardian API.

**Usage:**

```python
from newslaunch.guardian_api import GuardianAPIError

try:
    articles = api.search_articles("search_query")
except GuardianAPIError as e:
    print(f"An error occurred while fetching Guardian articles: {e}")
```

### GuardianArticlePreview

The `GuardianArticlePreview` is a Pydantic model that parses the full response from the Guardian API. It represents a subset of fields retrieved by default (when `filter_response` is set to True).

#### Fields:

- `web_publication_date` (str): The publication date of the article.
- `web_title` (str): The title of the article.
- `web_url` (str): The URL of the article.
- `content_preview` (str): A truncated preview of the article content (up to 1000 characters).

```python
articles = api.search_articles("search_query", from_date="2023-01-01")

# By default, search_articles returns a list of dictionaries with the following key-value pairs:
# articles = [
#     {
#         "webPublicationDate": "2023-01-01T00:00:00Z",
#         "webTitle": "Example Article Title",
#         "webUrl": "https://www.theguardian.com/example_article",
#         "contentPreview": "Preview of the main article body up to 1000 characters..."
#     },
#     ...
# ]
```
