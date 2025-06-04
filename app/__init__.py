import os
from flask import Flask
from flask_cors import CORS
from config import app_config
from flask_session import Session


def create_app():
    app = Flask(__name__)
    app.secret_key = app_config.SECRET_KEY
    CORS(app)
    app.config.from_object(app_config)
    app.config['SESSION_TYPE'] = 'filesystem'
    Session(app)
    
    # Register blueprints or routes
    from app.maildash import maildash_bp
    app.register_blueprint(maildash_bp)
    
    return app