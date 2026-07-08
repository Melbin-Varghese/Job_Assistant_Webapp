"""
app.py
The entry point. Creates the Flask app, registers the route groups
(blueprints), and runs the server. All the actual page/route logic
lives in routes/pages.py, routes/ai_assistant.py, routes/ats_checker.py,
and (going forward) one file per feature.
"""

from flask import Flask

from routes.pages import pages_bp
from routes.ai_assistant import ai_assistant_bp

from routes.cover_letter import cover_letter_bp
from routes.recommendation import recommendation_bp
from routes.ats_checker import ats_checker_bp
app = Flask(__name__)


app.register_blueprint(ats_checker_bp)
app.register_blueprint(recommendation_bp)
app.register_blueprint(cover_letter_bp)
app.register_blueprint(pages_bp)
app.register_blueprint(ai_assistant_bp)


if __name__ == "__main__":
    app.run(debug=True)