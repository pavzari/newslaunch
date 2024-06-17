## Overview

The newslaunch provides a CLI interface for querying news sources. Currently, it only supports the Guardian API.

## Commands

### `newslaunch`

The main entry point for the CLI.

```bash
newslaunch [OPTIONS] COMMAND [ARGS]...
```

**Options:**

- `--version`: Show the version and exit.
- `--help`: Show this message and exit.

**Commands:**

- `set-key`: Set the API key for the specified news source.
- `guardian`: Search and fetch articles from the Guardian API.

### `newslaunch set-key`

Sets the API key for the specified news source.

```bash
newslaunch set-key --guardian <API_KEY>
```

**Options:**

- `-g`, `--guardian` (str, required): Set Guardian API key.

### `newslaunch guardian`

Searches and fetches articles from the Guardian API.

```bash
newslaunch guardian [OPTIONS] SEARCH_TERM
```

**Arguments:**

- `search_term` (str, required): The search query for articles.

**Options:**

- `-fd`, `--from-date` (str, optional): The earliest publication date (YYYY-MM-DD format). Defaults to None.
- `-ps`, `--page-size` (int, optional): The number of items displayed per query (1-200). Defaults to 10.
- `-o`, `--order-by` (str, optional): The order to sort the articles by. Choices are 'newest', 'oldest', 'relevance'. Defaults to 'relevance'.
- `-f`, `--full-response` (bool, optional): Returns a full API response, else return only a subset of fields (webPublicationDate, webTitle, webUrl, contentPreview).

**Examples:**

```bash
newslaunch guardian "python programming" --from-date 2023-01-01 --page-size 20 --order-by newest
```

## Usage Examples

Search for articles related to "technology" with default settings:

```bash
newslaunch guardian "technology"
```

Search for articles with a specific date and order:

```bash
newslaunch guardian '"health AND crisis"' --from-date 2023-01-01 --order-by newest
```

Search for articles with a custom page size and save to a file:

```bash
newslaunch guardian "science" --page-size 150 >> articles.json
```

To format and filter full response using jq:

```bash
newslaunch guardian "politics" -f | jq '.[] | {title: .webTitle, url: .webUrl, words: .fields.wordcount}'
```
