import logging
from flask import Blueprint, request, jsonify
from services.agent_service import generate_payment_intent
from schemas import PaymentIntentRequest
from utils import login_required, validate_request
from extensions import limiter

logger = logging.getLogger(__name__)
payments_bp = Blueprint("payments", __name__)


@payments_bp.route("/api/payment-intent", methods=["POST"])
@login_required
@limiter.limit("10/minute")
def payment_intent():
    data = request.get_json(silent=True) or {}
    parsed, err = validate_request(PaymentIntentRequest, data)
    if err:
        return jsonify(err[0]), err[1]

    intent = generate_payment_intent(parsed.task)
    return jsonify(intent)
