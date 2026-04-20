import os
from pathlib import Path
from dynaconf import Dynaconf, Validator

root = Path(__file__).resolve().parent.parent
conf_path = root / 'core'

settings = Dynaconf(
    envvar_prefix=False,
    root_path=conf_path,
    settings_files=['settings.toml', '.secrets.toml'],
    load_dotenv=True,
    environments=True,
    env_switch_for_dynaconf='ENV_FOR_DYNACONF', 
    default_env='development',
)

# --- Validadores de Grado Profesional ---

# 1. Infraestructura Core (El sistema no arranca sin esto)
core_validators = [
    Validator("DATABASE_URL", must_exist=True),
    Validator("REDIS_URL", must_exist=True),
]

# 2. Servicios Externos (Opcionales o específicos)
external_validators = [
    Validator("GOOGLE_AI_API_KEY", must_exist=True, when=Validator("ENV_FOR_DYNACONF", eq="production")),
    Validator("GOOGLE_CLIENT_ID", must_exist=True, when=Validator("ENV_FOR_DYNACONF", eq="production")),
    Validator("RESEND_API_KEY", must_exist=True, when=Validator("ENV_FOR_DYNACONF", eq="production")),
    Validator("META_WHATSAPP_TOKEN", must_exist=True, when=Validator("ENV_FOR_DYNACONF", eq="production")),
    Validator("META_PHONE_NUMBER_ID", must_exist=True, when=Validator("ENV_FOR_DYNACONF", eq="production")),
    Validator("META_VERIFY_TOKEN", must_exist=True, when=Validator("ENV_FOR_DYNACONF", eq="production")),
]

# Nota: En Railway, si usas Supabase para Auth, DEBES poner las variables.
# Pero si solo quieres que el Worker procese colas, esto le permitirá arrancar.

if not os.environ.get("CI"):
    settings.validators.register(*core_validators)
    settings.validators.register(*external_validators)
    
    try:
        settings.validators.validate()
    except Exception as e:
        # En producción somos estrictos, pero permitimos ver qué falta
        print(f"Config Validation Error: {e}")
        raise e
