from flask import render_template
from src import app

@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html') 