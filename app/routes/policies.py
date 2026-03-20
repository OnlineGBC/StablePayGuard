import logging
from flask import Blueprint, request, jsonify
from services.policy_service import create_policy
from schemas import PolicyCreate
from utils import login_required, validate_request
import store

logger = logging.getLogger(__name__)
policies_bp = Blueprint("policies", __name__)


@policies_bp.route("/api/policies", methods=["GET"])
def list_policies():
    return jsonify(store.get_policies())


@policies_bp.route("/api/policies/<policy_id>", methods=["GET"])
def get_policy(policy_id):
    from services.policy_service import get_policy_on_chain
    result = get_policy_on_chain(policy_id)
    return jsonify(result)


@policies_bp.route("/api/policies", methods=["POST"])
@login_required
def create():
    data = request.get_json(silent=True) or {}
    parsed, err = validate_request(PolicyCreate, data)
    if err:
        return jsonify(err[0]), err[1]

    policy_id, tx_hash = create_policy(
        agent=parsed.agent,
        token=parsed.token,
        total_budget=parsed.totalBudget,
        per_tx_limit=parsed.perTxLimit,
        valid_from=parsed.validFrom,
        valid_until=parsed.validUntil,
        purpose=parsed.purpose,
    )

    store.add_policy(
        id=policy_id,
        agent=parsed.agent,
        token=parsed.token,
        budget=parsed.totalBudget,
        purpose=parsed.purpose,
        tx_hash=tx_hash,
    )
    store.add_activity("Policy Created", f"{policy_id} created for agent {parsed.agent}")
    store.new_tx("Demo Vendor", policy_id, parsed.totalBudget * 0.1, "Completed")

    logger.info("Policy created: %s tx=%s", policy_id, tx_hash)
    return jsonify({"policyId": policy_id, "txHash": tx_hash})
