import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../app"))

# Set test env vars BEFORE importing app
os.environ.setdefault("DATABASE_URL", "postgresql://stablepayguard:stablepayguard@localhost:5432/stablepayguard_test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ADMIN_PASSWORD", "testpass")

from app import app as flask_app
from models import db

# Exempt all requests from rate limiting when TESTING=True
from extensions import limiter

@limiter.request_filter
def _exempt_in_testing():
    try:
        from flask import current_app
        return current_app.config.get("TESTING", False)
    except RuntimeError:
        return False


@pytest.fixture(autouse=True)
def reset_db():
    """Recreate tables before each test (empty state, no seed data)."""
    with flask_app.app_context():
        db.drop_all()
        db.create_all()
    yield
    with flask_app.app_context():
        db.drop_all()


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


@pytest.fixture
def auth_client(client):
    """Authenticated test client."""
    client.post("/api/auth/login", json={"password": "testpass"})
    return client


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def test_login_success(client):
    res = client.post("/api/auth/login", json={"password": "testpass"})
    assert res.status_code == 200
    assert res.get_json()["success"] is True


def test_login_wrong_password(client):
    res = client.post("/api/auth/login", json={"password": "wrongpass"})
    assert res.status_code == 401


def test_auth_status_unauthenticated(client):
    res = client.get("/api/auth/status")
    assert res.status_code == 200
    assert res.get_json()["authenticated"] is False


def test_auth_status_authenticated(auth_client):
    res = auth_client.get("/api/auth/status")
    assert res.get_json()["authenticated"] is True


def test_logout(auth_client):
    auth_client.post("/api/auth/logout")
    assert auth_client.get("/api/auth/status").get_json()["authenticated"] is False


# ---------------------------------------------------------------------------
# Protected endpoints require auth
# ---------------------------------------------------------------------------

def test_create_policy_requires_auth(client):
    payload = {
        "agent": "0xAgent001", "token": "USDC",
        "totalBudget": 5000, "perTxLimit": 500, "purpose": "test"
    }
    res = client.post("/api/policies", json=payload)
    assert res.status_code == 401


def test_payment_intent_requires_auth(client):
    res = client.post("/api/payment-intent", json={"task": "pay AWS $100"})
    assert res.status_code == 401


def test_wallet_connect_requires_auth(client):
    res = client.post("/api/wallet/connect", json={})
    assert res.status_code == 401


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

def test_create_policy_returns_policy_id(auth_client):
    payload = {
        "agent": "0xAgentABC",
        "token": "USDC",
        "totalBudget": 5000,
        "perTxLimit": 500,
        "validFrom": 0,
        "validUntil": 0,
        "purpose": "test payments"
    }
    res = auth_client.post("/api/policies", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert "policyId" in data
    assert "txHash" in data


def test_create_policy_increments_kpi(auth_client):
    payload = {
        "agent": "0xAgentABC", "token": "ETH",
        "totalBudget": 1000, "perTxLimit": 100,
        "validFrom": 0, "validUntil": 0, "purpose": "testing"
    }
    auth_client.post("/api/policies", json=payload)
    kpi = auth_client.get("/api/dashboard").get_json()["kpi"]
    assert kpi["policies"] == 1
    assert kpi["payments"] == 1  # demo tx added on policy creation


def test_create_policy_adds_activity(auth_client):
    payload = {
        "agent": "0xTest", "token": "DAI",
        "totalBudget": 2000, "perTxLimit": 200,
        "validFrom": 0, "validUntil": 0, "purpose": "vendor"
    }
    auth_client.post("/api/policies", json=payload)
    activity = auth_client.get("/api/dashboard").get_json()["activity"]
    assert any("Policy Created" in a["action"] for a in activity)


def test_create_policy_missing_agent_returns_400(auth_client):
    payload = {
        "agent": "", "token": "USDC",
        "totalBudget": 1000, "perTxLimit": 100, "purpose": "test"
    }
    res = auth_client.post("/api/policies", json=payload)
    assert res.status_code == 400
    data = res.get_json()
    assert "error" in data


def test_create_policy_zero_budget_returns_400(auth_client):
    payload = {
        "agent": "0xAgent", "token": "USDC",
        "totalBudget": 0, "perTxLimit": 100, "purpose": "test"
    }
    res = auth_client.post("/api/policies", json=payload)
    assert res.status_code == 400


def test_create_policy_missing_purpose_returns_400(auth_client):
    payload = {
        "agent": "0xAgent", "token": "USDC",
        "totalBudget": 1000, "perTxLimit": 100, "purpose": ""
    }
    res = auth_client.post("/api/policies", json=payload)
    assert res.status_code == 400


def test_get_policies_list(auth_client):
    auth_client.post("/api/policies", json={
        "agent": "0xAgent", "token": "USDC",
        "totalBudget": 5000, "perTxLimit": 500, "purpose": "vendor payments"
    })
    res = auth_client.get("/api/policies")
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list)
    assert len(data) == 1


# ---------------------------------------------------------------------------
# POST /api/wallet/connect
# ---------------------------------------------------------------------------

def test_wallet_connect_demo(auth_client):
    res = auth_client.post("/api/wallet/connect", json={})
    assert res.status_code == 200
    data = res.get_json()
    assert data["connected"] is True
    assert data["address"] is not None


def test_wallet_connect_valid_address(auth_client):
    res = auth_client.post("/api/wallet/connect",
                           json={"address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["address"] == "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"


def test_wallet_connect_invalid_address_returns_400(auth_client):
    res = auth_client.post("/api/wallet/connect", json={"address": "notanaddress"})
    assert res.status_code == 400


def test_wallet_connect_updates_dashboard(auth_client):
    auth_client.post("/api/wallet/connect", json={})
    wallet = auth_client.get("/api/dashboard").get_json()["wallet"]
    assert wallet["connected"] is True


# ---------------------------------------------------------------------------
# POST /api/payment-intent
# ---------------------------------------------------------------------------

def test_payment_intent_empty_task_returns_400(auth_client):
    res = auth_client.post("/api/payment-intent", json={"task": ""})
    assert res.status_code == 400


def test_payment_intent_missing_task_returns_400(auth_client):
    res = auth_client.post("/api/payment-intent", json={})
    assert res.status_code == 400


def test_payment_intent_demo_mode(auth_client):
    """Without any API key, should return demo response."""
    os.environ.pop("SYNTH_API_KEY", None)
    os.environ.pop("OPENAI_API_KEY", None)
    res = auth_client.post("/api/payment-intent", json={"task": "Pay $100 to AWS"})
    assert res.status_code == 200
    data = res.get_json()
    assert "recipient" in data or "error" in data


def test_payment_intent_persisted(auth_client):
    """Generated payment intent should be persisted in the DB."""
    os.environ.pop("SYNTH_API_KEY", None)
    os.environ.pop("OPENAI_API_KEY", None)
    auth_client.post("/api/payment-intent", json={"task": "Pay AWS $200 for hosting"})
    from models import PaymentIntent
    with flask_app.app_context():
        count = PaymentIntent.query.count()
    assert count == 1


def test_policies_list_includes_remaining_budget(auth_client):
    """Dashboard policies_list should include remainingBudget for each policy."""
    auth_client.post("/api/policies", json={
        "agent": "0xAgent", "token": "USDC",
        "totalBudget": 5000, "perTxLimit": 500, "purpose": "vendor"
    })
    data = auth_client.get("/api/dashboard").get_json()
    assert "policies_list" in data
    policy = data["policies_list"][0]
    assert "remainingBudget" in policy
    assert "spentAmount" in policy
    assert policy["remainingBudget"] <= policy["budget"]


# ---------------------------------------------------------------------------
# GET /api/token/price/<symbol>
# ---------------------------------------------------------------------------

def test_token_price_invalid_symbol(client):
    res = client.get("/api/token/price/INVALID")
    assert res.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/token/quote
# ---------------------------------------------------------------------------

def test_swap_quote_invalid_token(client):
    res = client.post("/api/token/quote", json={
        "tokenIn": "INVALID", "tokenOut": "USDC", "amountUSD": 100
    })
    assert res.status_code == 400


def test_swap_quote_zero_amount(client):
    res = client.post("/api/token/quote", json={
        "tokenIn": "ETH", "tokenOut": "USDC", "amountUSD": 0
    })
    assert res.status_code == 400


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
# GET /api/contract/status
# ---------------------------------------------------------------------------

def test_contract_status(client):
    res = client.get("/api/contract/status")
    assert res.status_code == 200
    data = res.get_json()
    assert "mode" in data
    assert data["mode"] in ("live", "demo")


# ---------------------------------------------------------------------------
# GET / (dashboard page)
# ---------------------------------------------------------------------------

def test_dashboard_page_loads(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"StablePayGuard" in res.data
