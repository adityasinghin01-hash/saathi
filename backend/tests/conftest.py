import pytest
from fastapi.testclient import TestClient

from app.domain.ai import DeterministicFakeAI
from app.main import create_app


@pytest.fixture(scope="module")
def client():
    with TestClient(create_app("sqlite:///:memory:", ai=DeterministicFakeAI())) as test_client:
        yield test_client


def auth(user):
    return {"X-Demo-User": user}
