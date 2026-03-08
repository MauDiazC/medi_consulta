from pathlib import Path
from dynaconf import Dynaconf, Validator

root = Path(__file__).resolve().parent.parent
conf_path = root / 'core'

# Professional configuration for Cloud environments (Railway/Docker)
settings = Dynaconf(
    envvar_prefix=False,  # Permite leer DATABASE_URL directamente sin prefijo DYNACONF_
    root_path=conf_path,
    settings_files=['settings.toml', '.secrets.toml'],
    load_dotenv=True,     # Carga archivos .env si existen localmente
    environments=True,    # Soporta multi-entornos [development, production]
)

# 3. Critical environment variable validation
settings.validators.register(
    Validator("DATABASE_URL", must_exist=True, is_type_of=str),
    Validator("REDIS_URL", must_exist=True, is_type_of=str),
    Validator("SUPABASE_URL", must_exist=True),
    Validator("SUPABASE_ANON_KEY", must_exist=True),
    Validator("GROQ_API_KEY", must_exist=True),
)

# Trigger validation
settings.validators.validate()
