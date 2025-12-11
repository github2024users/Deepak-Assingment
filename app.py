from flask import Flask, jsonify, request, session
from flask_cors import CORS
from google.oauth2 import id_token
from google.auth.transport import requests as grequests

from scraper import scrape_url

app = Flask(__name__)
CORS(app)
app.secret_key = 'your-secret-key-change-this'

GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID_HERE"


@app.route("/health", methods=["GET"])
def health():
    """
    Simple health check endpoint
    Returns 200 OK if server is running
    Used by frontend to check if backend is alive
    """
    return jsonify({"status": "ok", "message": "Server is running"}), 200


@app.route("/verify-token", methods=["POST"])
def verify_token():
    """
    Verifies Google OAuth token
    Used for authentication when user logs in
    """
    data = request.json
    token = data.get("token")

    try:
        id_info = id_token.verify_oauth2_token(
            token,
            grequests.Request(),
            GOOGLE_CLIENT_ID
        )
        return jsonify({"success": True, "user": id_info})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/scrape", methods=["GET"])
def scrape():
    """
    Scrapes a URL provided as query parameter
    Returns categorized data with website summary
    """
    url = request.args.get('url')
    
    if not url:
        return jsonify({"error": "URL parameter is required"}), 400
    
    try:
        result = scrape_url(url)
        
        # Check if login is required
        if isinstance(result, dict) and result.get('login_required'):
            return jsonify(result), 200
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=5000, debug=True)