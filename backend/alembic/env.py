"""
Alembic env.py — reads DATABASE URL from environment,
supports both sync (for migrations) and async (for app) engines.
"""
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Load all models so Alembic can detect changes
from app.models import (  # noqa: F401
    Scheme, SchemeEligibilityRule, SchemeBenefit, SchemeDocument,
    SchemeLocation, SchemeSource, SchemeVersion, SchemeEmbedding,
    EntrepreneurProfile, SchemeMatch,
)
from app.core.database import Base

config = context.config

# Override sqlalchemy.url from environment (never hardcode credentials)
sync_db_url = os.environ.get(
    "SYNC_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/scheme_db"
)
config.set_main_option("sqlalchemy.url", sync_db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

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
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
