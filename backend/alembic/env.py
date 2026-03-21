import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Import our models' Base for autogenerate support
from app.core.database import Base

# Import all models so Alembic can detect them
from app.models.player import Player
from app.models.inventory import Inventory
from app.models.quest import Quest
from app.models.title import Title
from app.models.monster import Monster
from app.models.player_shop import PlayerShop
from app.models.combat_session import CombatSession, CombatLog, CombatSpellCooldown

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Get DB credentials from environment variables (.env loaded by Docker)
SQL_ALCHEMY_DB = os.getenv("POSTGRES_DB")
SQL_ALCHEMY_PASSWORD = os.getenv("POSTGRES_PASSWORD")
SQL_ALCHEMY_USER = os.getenv("POSTGRES_USER")
DB_HOST = os.getenv("DB_HOST", "localhost")

if not all([SQL_ALCHEMY_DB, SQL_ALCHEMY_PASSWORD, SQL_ALCHEMY_USER]):
    raise Exception("Missing DB env vars: POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER")

SQLALCHEMY_DATABASE_URL = f"postgresql://{SQL_ALCHEMY_USER}:{SQL_ALCHEMY_PASSWORD}@{DB_HOST}:5432/{SQL_ALCHEMY_DB}"

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
