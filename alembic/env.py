import os
from logging.config import fileConfig
from urllib.parse import quote_plus
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import dotenv_values

# Load environment variables from .env in project root
# Get the directory of this file (alembic/env.py)
current_dir = Path(__file__).resolve().parent
# Go up one level to get project root
project_root = current_dir.parent
env_path = project_root / ".env"

# Use dotenv_values to load into a dictionary
env_vars = dotenv_values(env_path)

# Set environment variables explicitly
for key, value in env_vars.items():
    if value is not None:
        os.environ[key] = value

# Alembic Config object
config = context.config

# Setup Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import your SQLAlchemy models here
from app.models import *

# Set target_metadata for 'autogenerate'
# If using declarative base, replace `Base` with your actual Base
from app.database import Base  # <-- Make sure Base is imported from your project
target_metadata = Base.metadata

# Build the database URL from .env
DB_TYPE = os.getenv("DB_TYPE", "mysql")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")

# URL-encode the password to handle special characters like @
encoded_password = quote_plus(DB_PASSWORD) if DB_PASSWORD else ""
DATABASE_URL = f"{DB_TYPE}+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Override sqlalchemy.url in config (escape % for configparser)
# ConfigParser uses % for interpolation, so we need to escape it
escaped_url = DATABASE_URL.replace('%', '%%')
config.set_main_option("sqlalchemy.url", escaped_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no DB connection)."""
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
    """Run migrations in 'online' mode (with DB connection)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
