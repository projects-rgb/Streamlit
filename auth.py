# ================================
# frontend/auth.py  (FINAL VERSION)
# ================================

import json
import os
import time
import jwt  # PyJWT
from typing import Dict, Optional

# -----------------------------------
# Path for secrets.json
# -----------------------------------
SECRETS_PATH = os.path.join(os.path.dirname(__file__), "secrets.json")


# -----------------------------------
# Load tableau + login credentials
# -----------------------------------
def load_secrets() -> Dict:
    if not os.path.isfile(SECRETS_PATH):
        raise FileNotFoundError(f"secrets.json not found at {SECRETS_PATH}")

    with open(SECRETS_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Handle nested structure
    cfg = raw.get("tableau", raw)

    return {
        "client_id": cfg.get("client_id"),
        "secret_id": cfg.get("secret_id"),
        "secret_value": cfg.get("secret_value"),
        "site_id": cfg.get("site_guid") or cfg.get("site_id"),
        "host": cfg.get("host") or cfg.get("tableau_host"),
        "admin_user": cfg.get("admin_user"),
        "admin_password": cfg.get("admin_password")
    }


# -----------------------------------
# Local login authentication
# -----------------------------------
def load_users() -> Dict[str, str]:
    """Fetch username/password from secrets.json"""
    s = load_secrets()
    admin_email = s.get("admin_user")
    admin_pass = s.get("admin_password")

    return {admin_email: admin_pass}


def authenticate_user(email: str, password: str) -> bool:
    """Validate login"""
    users = load_users()

    if email not in users:
        return False
    
    correct = users[email]
    if correct is None:
        return False

    return password == correct


# -----------------------------------
# Tableau JWT generator
# -----------------------------------
def generate_tableau_jwt(user_email: Optional[str] = None, ttl_seconds: int = 300) -> str:
    """
    Generate a JWT suitable for Tableau Connected App (HS256).
    site_id MUST be GUID.
    """
    secrets = load_secrets()

    CLIENT_ID = secrets["client_id"]
    SECRET_VALUE = secrets["secret_value"]
    SECRET_ID = secrets["secret_id"]
    SITE_GUID = secrets["site_id"]
    admin = user_email or secrets.get("admin_user")

    if not all([CLIENT_ID, SECRET_VALUE, SITE_GUID]):
        raise ValueError("Missing required fields in secrets.json")

    now = int(time.time())
    payload = {
        "iss": CLIENT_ID,
        "sub": admin,
        "aud": "tableau",
        "jti": str(now),
        "exp": now + ttl_seconds,
        "scp": ["tableau:views:embed"],
        "site": {"id": SITE_GUID}
    }

    headers = {"kid": SECRET_ID} if SECRET_ID else {}

    token = jwt.encode(payload, SECRET_VALUE, algorithm="HS256", headers=headers)

    return token.decode("utf-8") if isinstance(token, bytes) else token


# -----------------------------------
# Local test
# -----------------------------------
if __name__ == "__main__":
    try:
        print("Testing JWT...")
        print(generate_tableau_jwt())
    except Exception as e:
        print("Error:", e)
