"""Shared test fixtures — in-memory SQLite, test client, seed data."""

import os

# Ensure tests never use the default JWT secret — must be set BEFORE any app import.
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-secret-key-for-pytest-do-not-use-in-production",
)

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import generate_refresh_token, hash_password, hash_token
from app.database import get_db
from app.main import app
from app.models.base import Base
from app.models.auth_session import AuthSession
from app.models.device import Device
from app.models.risk_log import RiskLog
from app.models.user import User

# ---------------------------------------------------------------------------
# Test database
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Force a session-scoped event loop so that the engine lives long enough."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine():
    """Create an async SQLite engine — shared across all tests."""
    e = create_async_engine(TEST_DB_URL, echo=False)
    async with e.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield e
    await e.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    """Yield a new transaction-scoped session, rolled back after each test."""
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    """FastAPI test client with the session override in place."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Seed data helpers
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def test_user(db_session) -> User:
    """A normal active user with known password."""
    user = User(
        id=uuid.uuid4(),
        account="test@example.com",
        password_hash=hash_password("correct-password"),
        plan_code="standard",
        status="active",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def test_device(db_session, test_user) -> Device:
    """A device bound to test_user."""
    import hashlib
    fp = hashlib.sha256(b"device-fingerprint-abc").hexdigest()
    device = Device(
        id=uuid.uuid4(),
        user_id=test_user.id,
        device_fingerprint_hash=fp,
        device_name="Test Device 1",
        status="active",
    )
    db_session.add(device)
    await db_session.flush()
    return device


@pytest_asyncio.fixture
async def test_session(db_session, test_user, test_device) -> tuple[AuthSession, str]:
    """A valid auth_session + plaintext refresh_token."""
    plain = generate_refresh_token()
    session = AuthSession(
        id=uuid.uuid4(),
        user_id=test_user.id,
        device_id=test_device.id,
        refresh_token_hash=hash_token(plain),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(session)
    await db_session.flush()
    return session, plain


# ---------------------------------------------------------------------------
# Fingerprint helper
# ---------------------------------------------------------------------------

FINGERPRINT = "device-fingerprint-abc"
