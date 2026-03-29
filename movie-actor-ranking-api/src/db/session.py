from collections.abc import AsyncIterator
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from config import DATABASE_URL
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession


def _build_async_database_url() -> tuple[str, dict[str, dict[str, str]]]:
    database_url = DATABASE_URL
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set.")

    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)

    parsed = urlparse(database_url)
    query_params = parse_qs(parsed.query, keep_blank_values=True)
    schema_values = query_params.pop("schema", None)

    connect_args: dict[str, dict[str, str]] = {}
    if schema_values and schema_values[0]:
        connect_args = {
            "server_settings": {
                "search_path": schema_values[0],
            }
        }

    normalized_query = urlencode(query_params, doseq=True)
    normalized_url = urlunparse(parsed._replace(query=normalized_query))

    return normalized_url, connect_args


database_url, connect_args = _build_async_database_url()
engine = create_async_engine(database_url, connect_args=connect_args, echo=False)
SessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


async def init_db_schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
