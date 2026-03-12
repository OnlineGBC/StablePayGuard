from flask import Blueprint, request, jsonify
from services.policy_service import create_policy
from store import POLICIES, add_activity, new_tx

policies_bp = Blueprint("policies", __name__)


@policies_bp.route("/api/policies", methods=["POST"])
def create():
    data = request.json

    policy_id, tx_hash = create_policy(
        agent=data.get("agent", ""),
        token=data.get("token", "ETH"),
        total_budget=int(data.get("totalBudget", 0)),
        per_tx_limit=int(data.get("perTxLimit", 0)),
        valid_from=int(data.get("validFrom", 0)),
        valid_until=int(data.get("validUntil", 0)),
        purpose=data.get("purpose", "")
    )

    POLICIES.append({
        "id": policy_id,
        "agent": data.get("agent"),
        "token": data.get("token"),
        "budget": int(data.get("totalBudget", 0)),
        "purpose": data.get("purpose", ""),
        "tx_hash": tx_hash
    })

    add_activity("Policy Created", f"{policy_id} created for agent {data.get('agent')}")
    new_tx("Demo Vendor", policy_id, int(data.get("totalBudget", 0)) * 0.1, "Completed")

    return jsonify({"policyId": policy_id, "txHash": tx_hash})
