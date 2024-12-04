from flask import render_template
from src.app_instance import app

@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html') 