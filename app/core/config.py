import os
from pathlib import Path
from dynaconf import Dynaconf, Validator

root = Path(__file__).resolve().parent.parent
conf_path = root / 'core'

# Professional Cloud-Native Configuration
# Logic: If running in Railway/Docker, prioritize raw Env Vars
settings = Dynaconf(
    envvar_prefix=False,      # Read DATABASE_URL instead of DYNACONF_DATABASE_URL
    root_path=conf_path,
    settings_files=['settings.toml', '.secrets.toml'],
    load_dotenv=True,         # Local .env support
    environments=True,        # Multi-env support [development, production]
    env_switch_for_dynaconf='ENV_FOR_DYNACONF', 
    default_env='development',
)

# 3. Critical environment variable validation
# We use 'when' or 'environments' logic if needed, but for core infra 
# it must exist in any environment when running in production
validators = [
    Validator("DATABASE_URL", must_exist=True),
    Validator("REDIS_URL", must_exist=True),
    Validator("SUPABASE_URL", must_exist=True),
    Validator("SUPABASE_ANON_KEY", must_exist=True),
]

# Only validate if not in a CI environment to avoid build breaks
if not os.environ.get("CI"):
    settings.validators.register(*validators)
    settings.validators.validate()
