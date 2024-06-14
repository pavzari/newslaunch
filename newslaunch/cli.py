from __future__ import annotations

import json
from pathlib import Path

import click

from newslaunch.guardian_api import GuardianAPI, GuardianAPIError

CONFIG_FILE = Path(click.get_app_dir("newslaunch")) / "newslaunch-config.json"


def save_api_key(source: str, api_key: str) -> None:
    """Save the API key to the config file."""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as file:
            config = json.load(file)
    else:
        config = {}

    config[source] = api_key

    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file)


def load_api_key(source: str) -> str | None:
    """Load the API key from the config file."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as file:
            config = json.load(file)
        return config.get(source)
    return None


@click.group()
@click.version_option()
def cli() -> None:
    """newslaunch CLI for fetching and processing news articles."""
    pass


@cli.command()
@click.option("-g", "--guardian", required=True, help="Set Guardian API key.")
def set_key(guardian: str) -> None:
    """Set the API key for the specified news source."""
    if guardian:
        save_api_key("guardian", guardian)
        click.secho(f"Guardian API key saved in {CONFIG_FILE}", fg="green")
    else:
        click.echo("Please provide an API key for a supported news source.")


@cli.command()
@click.argument("search_term", required=True, type=str)
@click.option(
    "-fd",
    "--from-date",
    default=None,
    type=str,
    help="The earliest publication date (YYYY-MM-DD format).",
)
@click.option(
    "-s",
    "--page-size",
    default=10,
    type=int,
    help="The number of items displayed per query (1-200).",
)
@click.option(
    "-o",
    "--order-by",
    default=None,
    type=click.Choice(["newest", "oldest", "relevance"]),
    help="The order to sort the articles by. Defaults to 'relevance'.",
)
@click.option(
    "-f",
    "--full-response",
    is_flag=True,
    default=True,
    type=bool,
    help="Returns a full response if set, else returns only a subset of fields.",
)
def guardian(
    search_term: str,
    from_date: str | None,
    page_size: int,
    order_by: str | None,
    full_response: bool,
) -> None:
    """Search and fetch articles from the Guardian API."""
    api_key = load_api_key("guardian")
    if not api_key:
        raise click.ClickException(
            "Guardian API key not found. Please add it using 'newslaunch set-key --guardian <API_KEY>'."
        )

    try:
        guardian_api = GuardianAPI(api_key=api_key)
        articles = guardian_api.search_articles(
            search_term=search_term,
            from_date=from_date,
            page_size=page_size,
            order_by=order_by,
            filter_response=full_response,
        )
        if articles:
            click.echo(json.dumps(articles, indent=4))
        else:
            click.secho("No articles found.", fg="red")
    except ValueError as e:
        raise click.ClickException(f"{e}")
    except GuardianAPIError as ge:
        raise click.ClickException(f"{ge}")
