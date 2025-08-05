import os
import requests
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect, CSRFError

# Baris ini untuk development di laptop, agar bisa membaca file .env
load_dotenv()
app = Flask(__name__)

# Flask-WTF memerlukan SECRET_KEY untuk CSRF
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "2131985d51dee7d432212146c15983f1b28686c47a286cc9")

# Inisialisasi proteksi CSRF
csrf = CSRFProtect(app) 

CORS(app)

# === AMBIL KONFIGURASI DARI ENVIRONMENT VARIABLES ===
# Ini cara aman dan standar untuk deployment
SUPERSET_URL = os.getenv("SUPERSET_URL")
SUPERSET_USERNAME = os.getenv("SUPERSET_USERNAME")
SUPERSET_PASSWORD = os.getenv("SUPERSET_PASSWORD")
DASHBOARD_ID = os.getenv("DASHBOARD_ID")

def get_guest_token_from_superset():
    # ... kode dari sebelumnya ...
    if not all([os.getenv("SUPERSET_URL"), os.getenv("SUPERSET_USERNAME"), os.getenv("SUPERSET_PASSWORD"), os.getenv("DASHBOARD_ID")]):
        raise Exception("Satu atau lebih Environment Variable belum di-set!")
    # ... sisa fungsi ...
    login_payload = {
        "username": os.getenv("SUPERSET_USERNAME"),
        "password": os.getenv("SUPERSET_PASSWORD"),
        "provider": "db"
    }
    r = requests.post(f"{os.getenv('SUPERSET_URL')}/api/v1/security/login", json=login_payload, timeout=30)
    r.raise_for_status()
    access_token = r.json()["access_token"]
    guest_token_payload = {
        "user": {
            "username": "guest-embed",
            "first_name": "Guest",
            "last_name": "User"
        },
        "resources": [{"type": "dashboard", "id": os.getenv("DASHBOARD_ID")}]
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.post(f"{os.getenv('SUPERSET_URL')}/api/v1/security/guest_token/", headers=headers, json=guest_token_payload, timeout=30)
    r.raise_for_status()
    return r.json()["token"]

# --- Endpoint API yang diperbarui ---
@app.route("/api/get-guest-token")
@csrf.exempt  # <-- DEKORATOR INI ADALAH KUNCINYA!
def get_token_for_frontend():
    """
    Endpoint ini dikecualikan dari pemeriksaan CSRF karena ini adalah API stateless.
    """
    try:
        guest_token = get_guest_token_from_superset()
        return jsonify(guest_token=guest_token)
    except Exception as e:
        return jsonify(error=str(e)), 500

# ... (sisa kode seperti @app.route("/") tetap sama) ...
@app.route("/")
def health_check():
    return "Backend server is running."