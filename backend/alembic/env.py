import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from infisical_sdk import InfisicalSDKClient

# Import our models' Base for autogenerate support
from app.core.database import Base

# Import all models so Alembic can detect them
from app.models.player import Player
from app.models.inventory import Inventory
from app.models.quest import Quest
from app.models.title import Title
from app.models.monster import Monster
from app.models.equipement import Weapon, Spell
from app.models.player_shop import PlayerShop

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Get secrets from environment variables first (works with infisical run)
SQL_ALCHEMY_DB = os.getenv("POSTGRES_DB")
SQL_ALCHEMY_PASSWORD = os.getenv("POSTGRES_PASSWORD")
SQL_ALCHEMY_USER = os.getenv("POSTGRES_USER")

# If env vars not set, fallback to Infisical SDK
if not all([SQL_ALCHEMY_DB, SQL_ALCHEMY_PASSWORD, SQL_ALCHEMY_USER]):
    PROJECT_ID = os.getenv("INFISICAL_PROJECT_ID", "9edf2628-e6d1-4b45-a5d0-c5c7fde078a6")
    
    client = InfisicalSDKClient(
        host=os.getenv("INFISICAL_API_URL"),
        token=os.getenv("INFISICAL_TOKEN"),
    )
    
    SQL_ALCHEMY_DB = client.secrets.get_secret_by_name(
        secret_name="POSTGRES_DB",
        project_id=PROJECT_ID,
        environment_slug="dev",
        secret_path="/"
    ).secretValue
    
    SQL_ALCHEMY_PASSWORD = client.secrets.get_secret_by_name(
        secret_name="POSTGRES_PASSWORD",
        project_id=PROJECT_ID,
        environment_slug="dev",
        secret_path="/"
    ).secretValue
    
    SQL_ALCHEMY_USER = client.secrets.get_secret_by_name(
        secret_name="POSTGRES_USER",
        project_id=PROJECT_ID,
        environment_slug="dev",
        secret_path="/"
    ).secretValue

# Auto-detect host: use localhost when running locally, db in Docker
DB_HOST = os.getenv("DB_HOST", "localhost")
SQLALCHEMY_DATABASE_URL = f"postgresql://{SQL_ALCHEMY_USER}:{SQL_ALCHEMY_PASSWORD}@{DB_HOST}:5432/{SQL_ALCHEMY_DB}"

if not SQLALCHEMY_DATABASE_URL:
    raise Exception("Error fetching db URL")

config.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
