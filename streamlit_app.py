import streamlit as st
import json
import time
import jwt
import os
import base64

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(page_title="Client Dashboard Portal", layout="wide")

SECRETS_FILE = "secrets.json"
DASHBOARDS_FILE = "dashboards.json"


# ======================================================
# HELPERS
# ======================================================
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_b64(path):
    if not os.path.exists(path):
        return ""
    return base64.b64encode(open(path, "rb").read()).decode()


# ======================================================
# LOAD LOGIN + TABLEAU USER
# ======================================================
secrets_cache = load_json(SECRETS_FILE)

STREAMLIT_USERNAME = secrets_cache.get("admin_user")
STREAMLIT_PASSWORD = secrets_cache.get("admin_password")
TABLEAU_USER = secrets_cache.get("tableau_user")


# ======================================================
# JWT GENERATOR
# ======================================================
def generate_tableau_jwt(secrets, tableau_user_email, expiry=None):
    now = int(time.time())

    if expiry is None:
        expiry = 7200  # 2 hours

    payload = {
        "iss": secrets["client_id"],
        "sub": tableau_user_email,
        "aud": "tableau",
        "jti": str(now),
        "exp": now + expiry,
        "site": {"id": secrets["site_id"]},
        "scp": ["tableau:views:embed"],
    }

    headers = {"kid": secrets["secret_id"]}
    secret = secrets["secret_value"].strip()

    token = jwt.encode(payload, secret, algorithm="HS256", headers=headers)
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


# ======================================================
# KEEP EXACT SAME OLD IFRAME LOGIC (NO CHANGE)
# ======================================================
def build_iframe_url(view_url, token):
    delim = "&" if "?" in view_url else "?"
    return f"{view_url}{delim}:embed=y&:showVizHome=n&:toolbar=n&:api_token={token}"


# ======================================================
# LOGIN SCREEN
# ======================================================
def login_screen():

    bg = None
    for ext in ["png", "jpg", "jpeg"]:
        path = f"landing_page.{ext}"
        if os.path.exists(path):
            bg = path
            break

    if bg:
        b64 = safe_b64(bg)
        st.markdown(
            f"""
            <style>
                [data-testid="stAppViewContainer"] {{
                    background-image: url("data:image/jpg;base64,{b64}");
                    background-size: cover;
                    background-position: center;
                }}
                input {{
                    background: rgba(0,0,0,0.45) !important;
                    color: white !important;
                }}
            </style>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='padding-top:200px'></div>", unsafe_allow_html=True)

    email = st.text_input("", placeholder="Email", label_visibility="collapsed")
    password = st.text_input("", placeholder="Password", type="password", label_visibility="collapsed")

    if st.button("Login (Submit)", key="login_submit"):
        if email == STREAMLIT_USERNAME and password == STREAMLIT_PASSWORD:
            st.session_state["logged_in"] = True
            st.session_state["username"] = email
            st.rerun()
        else:
            st.error("Invalid credentials")


# ======================================================
# DASHBOARD PAGE (OLD FUNCTIONALITY PRESERVED 100%)
# ======================================================
def dashboard_page():

    # Light UI only (does NOT change layout height)
    st.markdown(
        """
        <style>
            [data-testid="stAppViewContainer"] {
                background: #f5f6fa !important;
            }

            [data-testid="stSidebar"] {
                background: #ffffffee !important;
                border-right: 1px solid #e0e0e0 !important;
                backdrop-filter: blur(6px);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    secrets = load_json(SECRETS_FILE)
    dashboards = load_json(DASHBOARDS_FILE)

    # ---- SIDEBAR ----
    st.sidebar.title("Dashboards")
    names = [d["name"] for d in dashboards]

    selected = st.sidebar.radio("Select dashboard", names, key="dashboard_selector")

    st.sidebar.markdown("---")
    st.sidebar.write("Logged in as:")
    st.sidebar.write(f"**{st.session_state.get('username')}**")

    if st.sidebar.button("Logout", key="logout_btn"):
        st.session_state.clear()
        st.rerun()

    # ---- JWT + URL ----
    token = generate_tableau_jwt(secrets, TABLEAU_USER)
    view_url = next(d["url"] for d in dashboards if d["name"] == selected)
    iframe_url = build_iframe_url(view_url, token)

    # ---- TITLE + REFRESH ----
    col1, col2 = st.columns([8, 2])
    with col1:
        st.header(selected)
    with col2:
        if st.button("🔄 Refresh", key="refresh_btn", use_container_width=True):
            st.rerun()

    # ---- EXACT OLD WORKING IFRAME LOGIC ----
    tableau_script = (
        '<script type="module" '
        'src="https://prod-in-a.online.tableau.com/javascripts/api/tableau.embedding.3.latest.min.js">'
        "</script>"
    )

    html_block = f"""
        {tableau_script}
        <style>
            html, body {{
                margin: 0;
                padding: 0;
                height: 100%;
                overflow: hidden;
            }}
            #vizframe {{
                width: 100%;
                height: calc(100vh - 70px); /* EXACT SAME AS OLD CODE */
                border: none;
            }}
        </style>

        <iframe id="vizframe" src="{iframe_url}" allowfullscreen></iframe>
    """

    # Old stable component height
    st.components.v1.html(html_block, height=1200, scrolling=False)

    # ---- FOOTER ----
    st.markdown(
        """
        <style>
            .app-footer {
                margin-top: 40px;
                padding: 25px 0;
                border-top: 1px solid #d4d7dd;
                font-size: 18px;      /* increased from 14px → 18px */
                font-weight: 600;     /* bolder for premium feel */
                color: #475569;
                text-align: center;
            }
        </style>

        <div class="app-footer">
            © 2025 <strong>Amigos Consultants</strong> — Confidential Analytics Portal | All Rights Reserved
        </div>
        """,
        unsafe_allow_html=True,
    )


# ======================================================
# MAIN
# ======================================================
def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login_screen()
    else:
        dashboard_page()


if __name__ == "__main__":
    main()
