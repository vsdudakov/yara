import os

import typer
from dotenv import load_dotenv

from yara.main import YaraRootApp

load_dotenv(os.getenv("YARA_ENV_FILE") or ".env")

typer_app = typer.Typer()
root_app = YaraRootApp()


for app in root_app.apps.values():
    commands = app.get_commands()
    if not commands:
        continue
    for command in commands:
        typer_app.command()(command)


def run_command() -> None:
    typer_app()
