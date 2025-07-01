from __future__ import with_statement

import os
import sys
from logging.config import fileConfig
import importlib

from sqlalchemy import engine_from_config, pool
from alembic import context  # type: ignore

# Add service src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

# Import metadata from repository definition
evaluation_repo_module = importlib.import_module("src.infrastructure.database.evaluation_repository")
metadata = evaluation_repo_module.metadata

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name:
    fileConfig(config.config_file_name)

# Set SQLALCHEMY URL from env, fallback to default local Postgres
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL", "postgresql://atomia_user:atomia_password@localhost/atomia_dev"))

target_metadata = metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""

    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online() 