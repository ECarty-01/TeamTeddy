from flask import Blueprint, request, jsonify, render_template
import sys
import os
import tempfile
# import cv2
from werkzeug.utils import secure_filename

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import scanner
try:
    from musicScanner.main import process_image
except ImportError:
    def process_image(img_path):
        return []

# Import audio modules safely
try:
    from AudioAnalysizer import detect_one_note
except ImportError:
    def detect_one_note(timeout_seconds=5):
        return "C4"

try:
    from audip_app import grade_performance
except ImportError:
    def grade_performance(expected, played):
        return {"score": 0}

bp = Blueprint("api", __name__)

sessions = {}

@bp.route("/", methods=["GET"])
def home():
    return render_template("index")

@bp.route("/upload", methods=["GET"])
def upload_page():
    return render_template("upload.html")

@bp.route("/play", methods=["GET"])
def play_page():
    return render_template("play.html")

@bp.route("/results", methods=["GET"])
def results_page():
    return render_template("results.html")

@bp.route("/api/scan-pdf", methods=["POST"])
def scan_pdf():
    """Scan a PDF or image file and extract notes"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    try:
        # Save temporarily and scan
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
            # For PDF, you might need to convert to image first
            # For now, assume it's an image
            file.save(tmp.name)
            notes = process_image(tmp.name)
            os.unlink(tmp.name)
        
        if not notes:
            return jsonify({"error": "No notes detected in image", "notes": []}), 200
        
        return jsonify({"notes": notes}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
