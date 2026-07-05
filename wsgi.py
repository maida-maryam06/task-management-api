"""
wsgi.py — WSGI entry point for PythonAnywhere deployment.

PythonAnywhere's WSGI configuration file should import `application` from
this file. Set the FLASK_ENV environment variable to "production" in the
PythonAnywhere web app configuration panel.
"""

import os
from app import create_app

application = create_app(os.environ.get("FLASK_ENV", "production"))
