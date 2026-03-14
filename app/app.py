from flask import Flask, render_template, jsonify, request
from store import POLICIES, TRANSACTIONS, ACTIVITY, WALLET, add_activity, new_tx
from routes.policies import policies_bp
from routes.payments import payments_bp
from routes.uniswap import uniswap_bp

app = Flask(__name__)

app.register_blueprint(policies_bp)
app.register_blueprint(payments_bp)
app.register_blueprint(uniswap_bp)

# -------------------------
# Pages
# -------------------------

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

# -------------------------
# Dashboard Data API
# -------------------------

@app.route("/api/dashboard")
def dashboard_data():
    volume = sum(t["amount"] for t in TRANSACTIONS) if TRANSACTIONS else 0
    approved = sum(1 for t in TRANSACTIONS if t["status"] == "Completed")
    approval_rate = round(approved / len(TRANSACTIONS) * 100, 1) if TRANSACTIONS else 96.2

    return jsonify({
        "kpi": {
            "policies": len(POLICIES),
            "payments": len(TRANSACTIONS),
            "volume": volume,
            "approval_rate": approval_rate
        },
        "transactions": TRANSACTIONS[:10],
        "activity": ACTIVITY[:10],
        "wallet": WALLET
    })

# -------------------------
# Wallet Connect
# -------------------------

@app.route("/api/wallet/connect", methods=["POST"])
def wallet_connect():
    WALLET["connected"] = True
    WALLET["address"] = "0xA91F73C2"
    add_activity("Wallet Connected", f"Wallet {WALLET['address']} connected")
    return jsonify(WALLET)

# -------------------------
# Chart Data
# -------------------------

@app.route("/api/charts/payments")
def chart_payments():
    data = [
        {"day": "Mon", "value": 4200},
        {"day": "Tue", "value": 5500},
        {"day": "Wed", "value": 6100},
        {"day": "Thu", "value": 4800},
        {"day": "Fri", "value": 7200},
        {"day": "Sat", "value": 6300},
        {"day": "Sun", "value": 7000}
    ]
    return jsonify(data)

# -------------------------

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
