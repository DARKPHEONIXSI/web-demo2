"""Vercel serverless entry point for Flask app."""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wsgi import app

# Vercel expects the Flask app to be available as `app`
# This file is the entry point for the serverless function