from flask import Blueprint, request, jsonify, render_template
from .scanner import run_scan

bp = Blueprint("api", __name__)

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
