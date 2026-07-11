from flask import Blueprint, request, jsonify
from .scanner import run_scan

bp = Blueprint("main", __name__)

@bp.route("/scan", methods=["POST"])
def scan():
    file = request.files.get("file")

    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    notes = run_scan(file)
    return jsonify(notes)
