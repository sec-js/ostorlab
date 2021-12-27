"""This module is the entry point for ostorlab CLI."""
import click


@click.group()
@click.pass_context
def rootcli(ctx: click.core.Context) -> None:
    """Ostorlab is an open-source project to help automate security testing.\n
    Ostorlab standardizes interoperability between tools in a consistent, scalable, and performant way."""

    ctx.obj = {}


@rootcli.group()
def agent():
    raise click.ClickException('NotImplementedError.')


@rootcli.group()
def agentgroup():
    raise click.ClickException('NotImplementedError.')


@rootcli.group()
def auth():
    """You can use auth [subcommand] [options] to authenticate."""
    pass
