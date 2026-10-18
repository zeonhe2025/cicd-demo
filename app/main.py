"""Minimal Flask backend used for the GitHub Actions CI/CD demo.

Endpoints:
    GET /        -> basic service info (reads APP_ENV / APP_VERSION env vars)
    GET /health  -> health-check endpoint
"""
import os
from datetime import datetime, timezone

from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    """Return a small JSON payload describing the running instance."""
    return jsonify(
        {
            "service": "cicd-demo",
            "message": "Hello from the CI/CD demo backend!",
            "environment": os.getenv("APP_ENV", "unknown"),
            "version": os.getenv("APP_VERSION", "dev"),
        }
    )


@app.route("/health")
def health():
    """Simple liveness/health-check endpoint."""
    return jsonify(
        {
            "status": "ok",
            "time": datetime.now(timezone.utc).isoformat(),
        }
    )


if __name__ == "__main__":
    # Bind to 0.0.0.0 so the app is reachable from outside the container.
    app.run(host="0.0.0.0", port=8000)
