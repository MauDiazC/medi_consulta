import asyncio

import typer
from rich import print
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine

app = typer.Typer(help="Mediconsulta CLI")


@app.command()
def ping() -> None:
    """
    Verify database connectivity using the same engine as the API.
    """
    async def _ping() -> None:
        async with engine.connect() as conn:
            await conn.execute(text("select 1"))

    try:
        asyncio.run(_ping())
        print("[green]✔ Database connection via supabase OK[/green]")
    except Exception as exc:
        print("[red]✘ Database connection FAILED[/red]")
        raise typer.Exit(code=1) from exc


@app.command()
def version() -> None:
    """
    Show application version from configuration.
    """
    print(f"[bold]Mediconsulta v{settings.VERSION}[/bold]")
    print(settings)
if __name__ == "__main__":
    app()