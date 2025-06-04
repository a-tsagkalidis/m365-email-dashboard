from flask import Flask
from flask_cors import CORS

app = Flask(__name__)

# Allow frontend to call the API
CORS(app)

# Load the configuration file
app.config.from_pyfile('../config.py')

# Import the mail handling routes
from app import maildash