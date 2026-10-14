import os

import boto3
import psycopg
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings


# Base class for all application models.
class Base(DeclarativeBase):
    pass


db_url = settings.database_url

if db_url.startswith("postgres://"):
    db_url = "postgresql+psycopg://" + db_url[len("postgres://"):]
elif db_url.startswith("postgresql://") and "+psycopg" not in db_url:
    db_url = "postgresql+psycopg://" + db_url[len("postgresql://"):]


# Aurora PostgreSQL IAM authentication.
RDS_IAM_AUTH = settings.rds_iam_auth


if RDS_IAM_AUTH:
    parsed_url = make_url(db_url)
    rds_client = boto3.client("rds", region_name=settings.aws_region)

    engine = create_engine(
        db_url,
        connect_args={"sslmode": "require"},
        pool_pre_ping=True,
    )

    from sqlalchemy import event

    @event.listens_for(engine, "do_connect")
    def provide_iam_token(
        dialect,
        conn_rec,
        cargs,
        cparams,
    ):
        hostname = parsed_url.host
        port = parsed_url.port or 5432
        username = parsed_url.username or "postgres"

        token = rds_client.generate_db_auth_token(
            DBHostname=hostname,
            Port=port,
            DBUsername=username,
        )

        cparams["password"] = token
        cparams["sslmode"] = "require"
else:
    connect_args = (
        {"check_same_thread": False}
        if db_url.startswith("sqlite")
        else {}
    )

    if db_url.startswith("postgresql"):
        connect_args["password"] = os.getenv("DB_PASSWORD")
        connect_args["sslmode"] = "require"

    engine = create_engine(
        db_url,
        connect_args=connect_args,
        pool_pre_ping=True,
    )


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def _add_missing_column(table: str, column: str, ddl: str) -> None:
    """Add a small backward-compatible column to an existing database."""
    inspector = inspect(engine)

    if table not in inspector.get_table_names():
        return

    columns = {c["name"] for c in inspector.get_columns(table)}

    if column in columns:
        return

    with engine.begin() as conn:
        conn.execute(
            text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
        )


def init_db():
    # Import models so every mapped table is registered before create_all.
    from app.database import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # create_all does not alter existing tables.
    _add_missing_column(
        "approvals",
        "thread_id",
        "VARCHAR(255)",
    )