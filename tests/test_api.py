import sys
import os
import pytest

# Ensure the app/ directory is on the path so imports resolve
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../app"))

from app import app as flask_app
import store


@pytest.fixture(autouse=True)
def reset_store():
    """Reset shared in-memory state before each test."""
    store.POLICIES.clear()
    store.TRANSACTIONS.clear()
    store.ACTIVITY.clear()
    store.WALLET["connected"] = False
    store.WALLET["address"] = None
    yield


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# GET /api/dashboard
# ---------------------------------------------------------------------------

def test_dashboard_returns_correct_structure(client):
    res = client.get("/api/dashboard")
    assert res.status_code == 200
    data = res.get_json()
    assert "kpi" in data
    assert "transactions" in data
    assert "activity" in data
    assert "wallet" in data


def test_dashboard_kpi_starts_at_zero(client):
    res = client.get("/api/dashboard")
    kpi = res.get_json()["kpi"]
    assert kpi["policies"] == 0
    assert kpi["payments"] == 0
    assert kpi["volume"] == 0


# ---------------------------------------------------------------------------
# POST /api/policies
# ---------------------------------------------------------------------------

def test_create_policy_returns_policy_id(client):
    payload = {
        "agent": "0xAgentABC",
        "token": "USDC",
        "totalBudget": "5000",
        "perTxLimit": "500",
        "validFrom": "0",
        "validUntil": "0",
        "purpose": "test payments"
    }
    res = client.post("/api/policies", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert "policyId" in data
    assert "txHash" in data


def test_create_policy_increments_kpi(client):
    payload = {
        "agent": "0xAgentABC",
        "token": "ETH",
        "totalBudget": "1000",
        "perTxLimit": "100",
        "validFrom": "0",
        "validUntil": "0",
        "purpose": "testing"
    }
    client.post("/api/policies", json=payload)
    kpi = client.get("/api/dashboard").get_json()["kpi"]
    assert kpi["policies"] == 1
    assert kpi["payments"] == 1  # initial tx added on policy creation


def test_create_policy_adds_activity(client):
    payload = {
        "agent": "0xTest",
        "token": "DAI",
        "totalBudget": "2000",
        "perTxLimit": "200",
        "validFrom": "0",
        "validUntil": "0",
        "purpose": "vendor"
    }
    client.post("/api/policies", json=payload)
    activity = client.get("/api/dashboard").get_json()["activity"]
    assert any("Policy Created" in a["action"] for a in activity)


# ---------------------------------------------------------------------------
# POST /api/wallet/connect
# ---------------------------------------------------------------------------

def test_wallet_connect(client):
    res = client.post("/api/wallet/connect")
    assert res.status_code == 200
    data = res.get_json()
    assert data["connected"] is True
    assert data["address"] is not None


def test_wallet_connect_updates_dashboard(client):
    client.post("/api/wallet/connect")
    wallet = client.get("/api/dashboard").get_json()["wallet"]
    assert wallet["connected"] is True


# ---------------------------------------------------------------------------
# GET /api/charts/payments
# ---------------------------------------------------------------------------

def test_chart_returns_seven_days(client):
    res = client.get("/api/charts/payments")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data) == 7
    days = [d["day"] for d in data]
    assert "Mon" in days and "Sun" in days


def test_chart_values_are_positive(client):
    data = client.get("/api/charts/payments").get_json()
    assert all(d["value"] > 0 for d in data)


# ---------------------------------------------------------------------------
# GET / (dashboard page)
# ---------------------------------------------------------------------------

def test_dashboard_page_loads(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Codex PayRails" in res.data
