from flask import Blueprint, request, jsonify
from services.agent_service import generate_payment_intent

payments_bp = Blueprint("payments", __name__)

@payments_bp.route("/api/payment-intent", methods=["POST"])
def payment_intent():

    data = request.json
    intent = generate_payment_intent(data["task"])

    return jsonify(intent)
