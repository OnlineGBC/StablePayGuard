import os
import logging
from secrets import load_secrets
from flask import Flask, render_template, jsonify

load_secrets()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")
db_url = os.environ.get("DATABASE_URL")
if not db_url:
    raise RuntimeError("DATABASE_URL environment variable is required (PostgreSQL)")
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# DB
from models import db
db.init_app(app)

# Rate limiting
from extensions import limiter
limiter.init_app(app)

# Blueprints
from routes.policies import policies_bp
from routes.payments import payments_bp
from routes.uniswap import uniswap_bp
from routes.auth import auth_bp
from routes.wallet import wallet_bp

app.register_blueprint(policies_bp)
app.register_blueprint(payments_bp)
app.register_blueprint(uniswap_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(wallet_bp)

# DB init + seed
with app.app_context():
    db.create_all()
    import store
    store.seed_if_empty()

# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

# ---------------------------------------------------------------------------
# Dashboard Data API
# ---------------------------------------------------------------------------

@app.route("/api/dashboard")
def dashboard_data():
    import store
    transactions = store.get_transactions()
    policies = store.get_policies()
    activity = store.get_activity(limit=10)
    wallet = store.get_wallet()

    volume = sum(t["amount"] for t in transactions) if transactions else 0
    approved = sum(1 for t in transactions if t["status"] == "Completed")
    approval_rate = round(approved / len(transactions) * 100, 1) if transactions else 96.2

    # Annotate each policy with remainingBudget calculated from DB transactions
    spent_by_policy = {}
    for t in transactions:
        if t["status"] == "Completed" and t["policy"]:
            spent_by_policy[t["policy"]] = spent_by_policy.get(t["policy"], 0) + t["amount"]

    policies_with_budget = []
    for p in policies:
        spent = spent_by_policy.get(p["id"], 0)
        p_copy = dict(p)
        p_copy["spentAmount"] = round(spent, 2)
        p_copy["remainingBudget"] = round(p["budget"] - spent, 2)
        policies_with_budget.append(p_copy)

    return jsonify({
        "kpi": {
            "policies": len(policies),
            "payments": len(transactions),
            "volume": volume,
            "approval_rate": approval_rate,
        },
        "transactions": transactions[:10],
        "activity": activity,
        "wallet": wallet,
        "policies_list": policies_with_budget,
    })

# ---------------------------------------------------------------------------
# Chart Data
# ---------------------------------------------------------------------------

@app.route("/api/charts/payments")
def chart_payments():
    data = [
        {"day": "Mon", "value": 4200},
        {"day": "Tue", "value": 5500},
        {"day": "Wed", "value": 6100},
        {"day": "Thu", "value": 4800},
        {"day": "Fri", "value": 7200},
        {"day": "Sat", "value": 6300},
        {"day": "Sun", "value": 7000},
    ]
    return jsonify(data)

# ---------------------------------------------------------------------------
# Contract Status
# ---------------------------------------------------------------------------

@app.route("/api/contract/status")
def contract_status():
    from services.web3_service import w3, contract
    connected = w3 is not None and w3.is_connected()
    return jsonify({
        "web3_connected": connected,
        "contract_loaded": contract is not None,
        "mode": "live" if (connected and contract) else "demo",
    })

# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
