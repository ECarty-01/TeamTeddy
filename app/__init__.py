from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static", static_url_path="/static")
    CORS(app)
    
    from .routes import bp
    app.register_blueprint(bp)
    
    return app
