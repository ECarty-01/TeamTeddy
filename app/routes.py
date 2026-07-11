from flask import Blueprint, request, jsonify, render_template
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from AudioAnalysizer import detect_one_note
from audip_app import grade_performance

bp = Blueprint("api", __name__)

sessions = {}

@bp.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@bp.route("/upload", methods=["GET"])
def upload_page():
    return render_template("upload.html")

@bp.route("/play", methods=["GET"])
def play_page():
    return render_template("play.html")

@bp.route("/results", methods=["GET"])
def results_page():
    return render_template("results.html")

@bp.route("/api/start-session", methods=["POST"])
def start_session():
    data = request.json or {}
    session_id = "session_1"
    sessions[session_id] = {
        "notes": data.get("notes", ["C4", "E4", "G4", "C4"]),
        "bpm": data.get("bpm", 120),
        "played": []
    }
    return jsonify({"session_id": session_id, "notes": sessions[session_id]["notes"]})

@bp.route("/api/listen-one-note", methods=["POST"])
def listen_one_note():
    data = request.json or {}
    timeout = data.get("timeout", 5)
    note = detect_one_note(timeout_seconds=timeout)
    return jsonify({"note": note})

@bp.route("/api/grade", methods=["POST"])
def grade():
    data = request.json or {}
    expected = data.get("expected", [])
    played = data.get("played", [])
    result = grade_performance(expected, played)
    return jsonify(result)
