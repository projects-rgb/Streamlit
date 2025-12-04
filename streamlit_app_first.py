# frontend/streamlit_app.py
import streamlit as st
import json
import time
import jwt  # PyJWT
import os
import base64

st.set_page_config(page_title="Client Dashboard Portal", layout="wide", page_icon="📊")

# ---------- CONFIG ----------
STREAMLIT_USERNAME = "projects@amigoserp.org"
STREAMLIT_PASSWORD = "Riddhika@2025"

SECRETS_FILE = "secrets.json"
DASHBOARDS_FILE = "dashboards.json"

# ---------- HELPERS ----------
def load_json_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_tableau_jwt(secrets, tableau_user_email, expiry_seconds=300):
    """
    Generate a JWT for Tableau Connected App (Direct Trust).
    This uses HMAC-SHA256 (HS256) with the secret value.
    Headers include 'kid' = secret_id, algorithm HS256.
    Payload fields follow typical Tableau requirements:
      - iss: client_id
      - sub: tableau user (the account you're impersonating)
      - aud: tableau
      - jti: unique id
      - exp: expiration epoch
      - site: site id
      - scp: requested scopes (array)
    """
    now = int(time.time())
    payload = {
        "iss": secrets["client_id"],
        "sub": tableau_user_email,
        "aud": "tableau",
        "jti": f"{now}",
        "exp": now + expiry_seconds,
        "site": secrets["site_id"],
        "scp": ["tableau:views:embed"]
    }

    headers = {"kid": secrets["secret_id"]}

    # secret_value must be bytes. Tableau secret shown in UI is base64-like; use as-is.
    secret_value = secrets["secret_value"]
    # If secret_value contains spaces or newlines, strip them
    secret_value = secret_value.strip()

    token = jwt.encode(
        payload,
        key=secret_value,
        algorithm="HS256",
        headers=headers
    )

    # PyJWT returns a str in recent versions
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token

def build_embed_iframe_url(view_url, token):
    """
    Returns an embed URL with common parameters and an api token.
    We append:
      &:embed=y (or &:showVizHome=false)
      &:toolbar=n
      &:showVizHome=n
      &:api_token=JWT
    NOTE: This approach works when Tableau Connected App and embedding accepts
    JWT token as 'api_token' query parameter based on embedding flow.
    """
    delim = "&" if "?" in view_url else "?"
    # hide toolbar and viz home; embed param to true; add token.
    url = f"{view_url}{delim}:embed=y&:showVizHome=false&:toolbar=n&:api_token={token}"
    return url

# ---------- UI: Login ----------
def login_screen():
    st.title("🔐 Client Login")
    st.markdown("Enter your username & password to access dashboards.")

    col1, col2 = st.columns([3, 2])
    with col1:
        username = st.text_input("Username", value="")
    with col2:
        password = st.text_input("Password", type="password", value="")

    if st.button("Login", use_container_width=True):
        if username == STREAMLIT_USERNAME and password == STREAMLIT_PASSWORD:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")

# ---------- UI: Dashboard page ----------
def dashboard_page():
    secrets = load_json_file(SECRETS_FILE)
    dashboards = load_json_file(DASHBOARDS_FILE)

    # Left sidebar
    st.sidebar.title("📊 Dashboards")
    st.sidebar.markdown(f"Logged in as **{st.session_state.get('username', '')}**")
    logout = st.sidebar.button("Logout")
    if logout:
        st.session_state.clear()
        st.experimental_rerun()

    # Build the list of names
    dash_names = [d["name"] for d in dashboards]
    selected = st.sidebar.radio("Select Dashboard", dash_names)

    # Allow user to enter the tableau user to impersonate (optional)
    st.sidebar.markdown("---")
    st.sidebar.info("Tableau user used for JWT impersonation (admin account).")
    tableau_user = st.sidebar.text_input("Tableau user email", value="laxmipathi@teramor.in")

    # Generate token
    try:
        jwt_token = generate_tableau_jwt(secrets, tableau_user_email=tableau_user, expiry_seconds=300)
    except Exception as e:
        st.error(f"Failed to generate JWT: {e}")
        return

    # Find the selected dashboard url
    view_url = None
    for d in dashboards:
        if d["name"] == selected:
            view_url = d["url"]
            break

    if view_url is None:
        st.error("Selected dashboard URL not found.")
        return

    embed_url = build_embed_iframe_url(view_url, jwt_token)

    # Add tableau embedding script once (for tableau-viz element usage, optional)
    tableau_script = '<script type="module" src="https://prod-in-a.online.tableau.com/javascripts/api/tableau.embedding.3.latest.min.js"></script>'

    st.markdown(f"### {selected}")
    # Using an iframe for the view (this avoids showing the login screen if JWT accepted)
    html = f"""
    {tableau_script}
    <div style="width:100%;height:900px;">
      <iframe src="{embed_url}" width="100%" height="900" frameborder="0" allowfullscreen></iframe>
    </div>
    """
    st.components.v1.html(html, height=920, scrolling=True)

# ---------- MAIN ----------
def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login_screen()
    else:
        dashboard_page()

if __name__ == "__main__":
    main()
