from flask import Blueprint, jsonify
api_bp = Blueprint("api", __name__)

@api_bp.route("/status")
def status():
    return jsonify({"status": "RF Agent running", "version": "1.0"})
