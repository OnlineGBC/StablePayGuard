import logging
from flask import Blueprint, request, jsonify
from services.agent_service import generate_payment_intent
from schemas import PaymentIntentRequest, PaymentExecuteRequest
from utils import login_required, validate_request
from extensions import limiter
import store

logger = logging.getLogger(__name__)
payments_bp = Blueprint("payments", __name__)


@payments_bp.route("/api/transactions", methods=["GET"])
def list_transactions():
    status = request.args.get("status")
    policy = request.args.get("policy")
    try:
        limit = min(int(request.args.get("limit", 50)), 200)
        offset = int(request.args.get("offset", 0))
    except ValueError:
        return jsonify({"error": "limit and offset must be integers"}), 400

    from models import Transaction
    q = Transaction.query.order_by(Transaction.created_at.desc())
    if status:
        q = q.filter(Transaction.status == status)
    if policy:
        q = q.filter(Transaction.policy == policy)
    total = q.count()
    txs = [t.to_dict() for t in q.offset(offset).limit(limit).all()]
    return jsonify({"total": total, "limit": limit, "offset": offset, "transactions": txs})


@payments_bp.route("/api/payment-intent", methods=["POST"])
@login_required
@limiter.limit("10/minute")
def payment_intent():
    data = request.get_json(silent=True) or {}
    parsed, err = validate_request(PaymentIntentRequest, data)
    if err:
        return jsonify(err[0]), err[1]

    intent = generate_payment_intent(parsed.task)

    # Warn if the parsed amount exceeds every policy's remaining budget
    amount = intent.get("amount", 0)
    if amount and not intent.get("error"):
        transactions = store.get_transactions()
        policies = store.get_policies()
        affordable = False
        for p in policies:
            spent = sum(
                t["amount"] for t in transactions
                if t["policy"] == p["id"] and t["status"] == "Completed"
            )
            if amount <= (p["budget"] - spent):
                affordable = True
                break
        if not affordable and policies:
            intent["budget_warning"] = (
                f"No active policy has sufficient remaining budget for ${amount}"
            )

    store.save_intent(parsed.task, intent)
    logger.info("Payment intent generated and persisted for task: %s", parsed.task[:60])
    return jsonify(intent)


@payments_bp.route("/api/payment", methods=["POST"])
@login_required
@limiter.limit("20/minute")
def execute_payment():
    data = request.get_json(silent=True) or {}
    parsed, err = validate_request(PaymentExecuteRequest, data)
    if err:
        return jsonify(err[0]), err[1]

    # Validate policy exists
    policies = {p["id"]: p for p in store.get_policies()}
    policy = policies.get(parsed.policy_id)
    if not policy:
        return jsonify({"error": f"Policy {parsed.policy_id} not found"}), 404

    # Check remaining budget
    transactions = store.get_transactions()
    spent = sum(
        t["amount"] for t in transactions
        if t["policy"] == parsed.policy_id and t["status"] == "Completed"
    )
    remaining = policy["budget"] - spent
    if parsed.amount > remaining:
        store.add_activity(
            "Payment Rejected",
            f"${parsed.amount} to {parsed.recipient} declined — exceeds remaining budget ${remaining:.2f} on {parsed.policy_id}",
        )
        logger.warning("Payment rejected: amount %.2f exceeds remaining budget %.2f", parsed.amount, remaining)
        return jsonify({"error": "Amount exceeds remaining policy budget", "remaining": remaining}), 422

    # Attempt on-chain approval; fall back to demo
    tx_hash = None
    mode = "demo"
    try:
        from services.web3_service import approve_payment, w3, contract
        if w3 and contract:
            tx_hash = approve_payment(parsed.policy_id, int(parsed.amount))
            mode = "live"
    except Exception as e:
        logger.warning("On-chain approval failed, falling back to demo: %s", e)

    tx = store.new_tx(parsed.recipient, parsed.policy_id, parsed.amount, "Completed")
    if tx_hash:
        # Overwrite the demo hash with the real on-chain hash
        from models import db, Transaction
        record = db.session.get(Transaction, tx["id"])
        if record:
            record.hash = tx_hash
            db.session.commit()
        tx["hash"] = tx_hash

    store.add_activity(
        "Payment Executed",
        f"{tx['id']} sent ${parsed.amount} to {parsed.recipient} via {parsed.policy_id}",
    )
    logger.info("Payment executed: %s %.2f to %s [%s]", tx["id"], parsed.amount, parsed.recipient, mode)
    return jsonify({**tx, "mode": mode}), 201
