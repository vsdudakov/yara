import typing as tp

import typer

typer_app = typer.Typer()


@typer_app.command()
def startproject(
    name: tp.Annotated[
        str,
        typer.Option(
            help="Project name",
        ),
    ],
) -> None:
    # TODO: Implement this function
    typer.echo(f"Project {name} has been created")


@typer_app.command()
def startappt(
    name: tp.Annotated[
        str,
        typer.Option(
            help="App name",
        ),
    ],
) -> None:
    # TODO: Implement this function
    typer.echo(f"App {name} has been created")


def run_command() -> None:
    typer_app()
