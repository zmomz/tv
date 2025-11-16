import os
import sys
import os
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import your models here to ensure they are registered with SQLAlchemy Base.metadata
from app.db import Base

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ... other imports

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import your models here to ensure they are registered with SQLAlchemy Base.metadata
from app.db import Base

target_metadata = Base.metadata

def get_url():
    """
    Returns the database URL from the environment variables, ensuring the
    driver is compatible with Alembic's synchronous operations.
    """
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable not set.")
    
    # Alembic's sync operations require a sync driver.
    # Replace the asyncpg driver with psycopg2 for the migration script.
    return url.replace("postgresql+asyncpg", "postgresql+psycopg2")

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Get the database URL from the environment
    url = get_url()
    
    # Create a new dictionary for engine_from_config
    # to avoid modifying the original config object
    connectable_config = {
        'sqlalchemy.url': url
    }

    connectable = engine_from_config(
        connectable_config,
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
