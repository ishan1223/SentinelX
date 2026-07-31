"""Test configuration.

Points the app at a throwaway SQLite file and disables the background
telemetry generation loop so tests are deterministic and don't leak
long-running asyncio tasks across the test session.
"""

import os
import tempfile

os.environ["SENTINELX_DISABLE_TELEMETRY_LOOP"] = "1"
os.environ["SENTINELX_DB_PATH"] = tempfile.NamedTemporaryFile(
    prefix="sentinelx_test_", suffix=".db", delete=False
).name

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client
