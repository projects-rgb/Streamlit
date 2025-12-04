import streamlit as st
import json
import time
import jwt
import os
import base64

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(page_title="Client Dashboard Portal", layout="wide")

SECRETS_FILE = "secrets.json"
DASHBOARDS_FILE = "dashboards.json"


# ---------------------------
# HELPERS
# ---------------------------
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------
# LOAD LOGIN + TABLEAU USER FROM JSON
# ---------------------------
secrets_cache = load_json(SECRETS_FILE)

STREAMLIT_USERNAME = secrets_cache.get("admin_user")
STREAMLIT_PASSWORD = secrets_cache.get("admin_password")
TABLEAU_USER = secrets_cache.get("tableau_user")


# ---------------------------
# JWT GENERATOR
# ---------------------------
def generate_tableau_jwt(secrets, tableau_user_email, expiry=300):
    now = int(time.time())

    payload = {
        "iss": secrets["client_id"],
        "sub": tableau_user_email,
        "aud": "tableau",
        "jti": str(now),
        "exp": now + expiry,
        "site": {"id": secrets["site_id"]},
        "scp": ["tableau:views:embed"]
    }

    headers = {"kid": secrets["secret_id"]}
    secret = secrets["secret_value"].strip()

    token = jwt.encode(payload, secret, algorithm="HS256", headers=headers)
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


# ---------------------------
# BUILD IFRAME URL
# ---------------------------
def build_iframe_url(view_url, token):
    delim = "&" if "?" in view_url else "?"
    return f"{view_url}{delim}:embed=y&:showVizHome=n&:toolbar=n&:api_token={token}"


# ---------------------------
# LOGIN SCREEN (unchanged except image fix)
# ---------------------------
def login_screen():

    bg_path = None
    for ext in ["png", "jpg", "jpeg"]:
        f = f"assets/landing_page.{ext}"
        if os.path.exists(f):
            bg_path = f
            break

    if bg_path:
        b64 = base64.b64encode(open(bg_path, "rb").read()).decode()
        st.markdown(
            f"""
            <style>
                html, body {{
                    margin:0; padding:0; height:100%;
                }}
                [data-testid="stAppViewContainer"] {{
                    background-image: url("data:image/jpg;base64,{b64}");
                    background-size: cover !important;
                    background-position: center !important;
                    background-repeat: no-repeat !important;
                }}
                input {{
                    background: rgba(0,0,0,0.45) !important;
                    color: white !important;
                }}
                ::placeholder {{
                    color: #eee !important;
                }}
            </style>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<div style='padding-top:200px;'></div>", unsafe_allow_html=True)

    email = st.text_input("", placeholder="Email", label_visibility="collapsed")
    password = st.text_input("", placeholder="Password", type="password", label_visibility="collapsed")

    if st.button("Login (Submit)"):
        if email == STREAMLIT_USERNAME and password == STREAMLIT_PASSWORD:
            st.session_state["logged_in"] = True
            st.session_state["username"] = email
            st.rerun()
        else:
            st.error("Invalid credentials")


# ---------------------------
# DASHBOARD SCREEN (ONLY FIT-TO-SCREEN CHANGED)
# ---------------------------
def dashboard_page():

    secrets = load_json(SECRETS_FILE)
    dashboards = load_json(DASHBOARDS_FILE)

    st.sidebar.title("Dashboards")
    names = [d["name"] for d in dashboards]
    selected = st.sidebar.radio("Select dashboard", names)

    st.sidebar.markdown("---")
    st.sidebar.write("Logged in as:")
    st.sidebar.write(f"**{st.session_state.get('username')}**")

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    tableau_user = TABLEAU_USER
    token = generate_tableau_jwt(secrets, tableau_user)

    view_url = next(d["url"] for d in dashboards if d["name"] == selected)
    iframe_url = build_iframe_url(view_url, token)

    st.header(selected)

    tableau_script = (
        '<script type="module" '
        'src="https://prod-in-a.online.tableau.com/javascripts/api/tableau.embedding.3.latest.min.js">'
        '</script>'
    )

    # ⭐ FINAL FIT-TO-SCREEN PATCH (SAFE)
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
            height: calc(100vh - 70px); /* perfect viewport fit */
            border: none;
        }}
    </style>

    <iframe id="vizframe" src="{iframe_url}" allowfullscreen></iframe>
    """

    # IMPORTANT: Must give fixed height > 0 or Streamlit hides iframe.
    st.components.v1.html(html_block, height=1200, scrolling=False)


# ---------------------------
# MAIN
# ---------------------------
def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login_screen()
    else:
        dashboard_page()


if __name__ == "__main__":
    main()
