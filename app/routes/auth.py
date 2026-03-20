import os
import logging
from flask import Blueprint, request, jsonify, session

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    password = data.get("password", "")
    admin_password = os.environ.get("ADMIN_PASSWORD", "demo")

    if password == admin_password:
        session["authenticated"] = True
        logger.info("Admin login successful")
        return jsonify({"success": True})

    logger.warning("Failed login attempt")
    return jsonify({"error": "Invalid password"}), 401


@auth_bp.route("/api/auth/logout", methods=["POST"])
def logout():
    session.pop("authenticated", None)
    return jsonify({"success": True})


@auth_bp.route("/api/auth/status", methods=["GET"])
def status():
    return jsonify({"authenticated": bool(session.get("authenticated"))})
