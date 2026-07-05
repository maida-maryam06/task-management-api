"""
app/__init__.py — Application factory for the Task Management API.

Usage:
    from app import create_app
    app = create_app()          # defaults to DevelopmentConfig
    app = create_app("testing") # uses TestingConfig (in-memory SQLite)
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow

db = SQLAlchemy()
jwt = JWTManager()
ma = Marshmallow()


def create_app(config_name: str = "development") -> Flask:
    """Application factory.

    Creates and configures a Flask application instance. Initialises all
    extensions (SQLAlchemy, JWT, Marshmallow), registers all route
    blueprints, and creates the database tables.

    Args:
        config_name: One of "development", "testing", or "production".
                     Defaults to "development".

    Returns:
        A fully configured Flask application instance.
    """
    app = Flask(__name__)

    from config import config_map
    app.config.from_object(config_map[config_name])

    # Initialise extensions
    db.init_app(app)
    jwt.init_app(app)
    ma.init_app(app)

    # Register blueprints
    from app.routes.auth     import auth_bp
    from app.routes.projects import projects_bp
    from app.routes.tasks    import tasks_bp

    app.register_blueprint(auth_bp,     url_prefix="/auth")
    app.register_blueprint(projects_bp, url_prefix="/projects")
    app.register_blueprint(tasks_bp,    url_prefix="/projects")

    # Create all tables
    with app.app_context():
        db.create_all()

    return app
