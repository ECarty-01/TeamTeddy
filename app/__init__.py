# app/__init__.py
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/play')
def play():
    return render_template('play.html')

@app.route('/results')
def results():
    return render_template('results.html')
