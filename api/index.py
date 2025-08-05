import os
import requests
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect

# Untuk development lokal, Vercel CLI akan otomatis memuat .env
load_dotenv()

# Aplikasi Flask harus diekspos sebagai variabel bernama 'app'
app = Flask(__name__)

# Konfigurasi SECRET_KEY untuk CSRF
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
if not app.config['SECRET_KEY']:
    raise ValueError("SECRET_KEY tidak ditemukan. Mohon di-set.")

# Inisialisasi proteksi CSRF & CORS
CORS(app) 
csrf = CSRFProtect(app)

# Definisi fungsi untuk mengambil token dari Superset
def get_guest_token_from_superset():
    SUPERSET_URL = os.getenv("SUPERSET_URL")
    SUPERSET_USERNAME = os.getenv("SUPERSET_USERNAME")
    SUPERSET_PASSWORD = os.getenv("SUPERSET_PASSWORD")
    DASHBOARD_ID = os.getenv("DASHBOARD_ID")

    if not all([SUPERSET_URL, SUPERSET_USERNAME, SUPERSET_PASSWORD, DASHBOARD_ID]):
        raise Exception("Satu atau lebih Environment Variable Superset belum di-set!")

    # Login ke API Superset
    login_payload = {"username": SUPERSET_USERNAME, "password": SUPERSET_PASSWORD, "provider": "db"}
    r_login = requests.post(f"{SUPERSET_URL}/api/v1/security/login", json=login_payload, timeout=30)
    r_login.raise_for_status()
    access_token = r_login.json()["access_token"]
    
    # Minta guest_token
    guest_token_payload = {
        "user": {"username": "guest-embed", "first_name": "Guest", "last_name": "User"},
        "resources": [{"type": "dashboard", "id": DASHBOARD_ID}]
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    r_token = requests.post(f"{SUPERSET_URL}/api/v1/security/guest_token/", headers=headers, json=guest_token_payload, timeout=30)
    r_token.raise_for_status()
    return r_token.json()["token"]

# Endpoint API utama
@app.route("/api/get-guest-token")
@csrf.exempt
def get_token_for_frontend():
    try:
        guest_token = get_guest_token_from_superset()
        return jsonify(guest_token=guest_token)
    except Exception as e:
        return jsonify(error=f"Error di backend: {str(e)}"), 500

# Endpoint untuk cek kesehatan server
@app.route("/")
def health_check():
    return "Backend server (Flask on Vercel) is running."