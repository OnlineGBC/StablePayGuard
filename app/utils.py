from functools import wraps
from flask import session, jsonify
from pydantic import ValidationError


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("authenticated"):
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated


def validate_request(schema_class, data):
    """Validate request data against a Pydantic schema.

    Returns (parsed_obj, None) on success or (None, error_response) on failure.
    The error_response is a tuple (jsonify_dict, 400) ready to return from a route.
    """
    try:
        return schema_class(**data), None
    except ValidationError as e:
        errors = {err["loc"][0]: err["msg"] for err in e.errors()}
        return None, ({"error": "Validation failed", "fields": errors}, 400)
