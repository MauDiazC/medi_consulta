import asyncio
import typer
from rich import print
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import engine, get_db
from app.core.security import hash_password
from app.modules.users.repository import UserRepository
from app.modules.organizations.repository import OrganizationRepository

app = typer.Typer(help="Mediconsulta CLI")

@app.command()
def ping() -> None:
    """Verify database connectivity."""
    async def _ping() -> None:
        async with engine.connect() as conn:
            await conn.execute(text("select 1"))
    try:
        asyncio.run(_ping())
        print("[green]✔ Database connection OK[/green]")
    except Exception as exc:
        print("[red]✘ Database connection FAILED[/red]")
        raise typer.Exit(code=1) from exc

@app.command()
def bootstrap_saas():
    """
    Initializes the SaaS with a Global Organization and Super Admin user.
    Credentials: mdiazcabr@gmail.com / master01
    """
    async def _run():
        async with AsyncSession(engine) as db:
            user_repo = UserRepository(db)
            org_repo = OrganizationRepository(db)

            # 1. Create/Get Global Organization
            print("[blue]Step 1: Setting up Global Organization...[/blue]")
            # Check if it already exists by name
            r = await db.execute(text("SELECT id FROM organizations WHERE name = 'Mediconsulta Global'"))
            org = r.mappings().first()
            
            if not org:
                org = await org_repo.create("Mediconsulta Global")
                print(f"[green]✔ Created Organization: {org['id']}[/green]")
            else:
                print(f"[yellow]! Global Organization already exists: {org['id']}[/yellow]")

            # 2. Create Super Admin User
            print("[blue]Step 2: Setting up Super Admin...[/blue]")
            email = "mdiazcabr@gmail.com"
            existing_user = await user_repo.get_by_email(email)

            if not existing_user:
                password = "master01"
                hashed = hash_password(password)
                user = await user_repo.create(
                    email=email,
                    password_hash=hashed,
                    full_name="Super Admin",
                    role="admin",
                    org=org["id"]
                )
                await db.commit()
                print(f"[green]✔ Created Super Admin: {email}[/green]")
            else:
                print(f"[yellow]! User {email} already exists.[/yellow]")

    try:
        asyncio.run(_run())
        print("\n[bold green]SaaS Bootstrapping Complete![/bold green]")
    except Exception as e:
        print(f"[red]Error during bootstrap: {str(e)}[/red]")
        raise typer.Exit(code=1)

@app.command()
def version() -> None:
    """Show application version."""
    print(f"[bold]Mediconsulta v{settings.VERSION}[/bold]")

if __name__ == "__main__":
    app()
