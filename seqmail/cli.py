#!/usr/bin/env python
import os
import shutil
import subprocess

import click

from . import settings, ui


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    if ctx.invoked_subcommand is None:
        run()


@cli.command()
def setup() -> None:
    editor = os.environ.get("EDITOR", "nano")

    if not settings.SETTINGS_PATH.exists():
        shutil.copy("./example-settings.toml", settings.SETTINGS_PATH)

    subprocess.call([editor, settings.SETTINGS_PATH])


@cli.command()
def run() -> None:
    ui.run()
