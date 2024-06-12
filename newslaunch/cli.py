import click


@click.group()
@click.version_option()
def cli() -> None:
    """newslaunch"""
    pass


@cli.command()
@click.argument("placeholder")
@click.option(
    "-o",
    "--option",
    help="A placeholder",
)
def first_command(example, option):
    """Placeholder"""
    click.echo("Placeholder")
