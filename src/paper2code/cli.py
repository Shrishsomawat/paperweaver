from __future__ import annotations

import json

import typer

from paper2code.config import get_settings
from paper2code.logging_utils import configure_logging
from paper2code.service import Paper2CodeService

app = typer.Typer(add_completion=False, help="Paper2Code CLI")


@app.command("run")
def run_pipeline(arxiv_url: str, open_folder: bool = typer.Option(True, "--open/--no-open")) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    service = Paper2CodeService(settings)
    result = service.run(arxiv_url)
    if open_folder:
        service.open_run_folder(result["run_dir"])
    typer.echo(json.dumps(result, indent=2))


@app.command("health")
def health() -> None:
    settings = get_settings()
    typer.echo(
        json.dumps(
            {
                "app": settings.app_name,
                "env": settings.env,
                "data_dir": str(settings.data_dir),
                "output_dir": str(settings.output_dir),
            },
            indent=2,
        )
    )
