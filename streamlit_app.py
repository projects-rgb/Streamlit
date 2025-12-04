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

STREAMLIT_USERNAME = "projects@amigoserp.org"
STREAMLIT_PASSWORD = "Riddhika@2025"

SECRETS_FILE = "secrets.json"
DASHBOARDS_FILE = "dashboards.json"


# ---------------------------
# HELPERS
# ---------------------------
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_tableau_jwt(secrets, tableau_user_email, expiry=300):
    now = int(time.time())

    payload = {
        "iss": secrets["client_id"],
        "sub": tableau_user_email,
        "aud": "tableau",
        "jti": str(now),
        "exp": now + expiry,

        # ❗ FIXED — MUST be nested object
        "site": { "id": secrets["site_id"] },

        "scp": ["tableau:views:embed"]
    }

    headers = {"kid": secrets["secret_id"]}
    secret = secrets["secret_value"].strip()

    token = jwt.encode(payload, secret, algorithm="HS256", headers=headers)
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def build_iframe_url(view_url, token):
    delim = "&" if "?" in view_url else "?"
    return (
        f"{view_url}{delim}:embed=y&:showVizHome=n&:toolbar=n&:api_token={token}"
    )


# ---------------------------
# LOGIN SCREEN
# ---------------------------
def login_screen():

    # background image
    bg_path = None
    for ext in ["png", "jpg", "jpeg"]:
        file = f"assets/landing_page.{ext}"
        if os.path.exists(file):
            bg_path = file
            break

    if bg_path:
        bg = base64.b64encode(open(bg_path, "rb").read()).decode()
        st.markdown(
            f"""
            <style>
                [data-testid="stAppViewContainer"] {{
                    background-image: url("data:image/jpg;base64,{bg}");
                    background-size: cover;
                    background-position: center;
                }}
                .whitepatch {{
                    display: none !important;
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
# DASHBOARD SCREEN
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

    tableau_user = "laxmipathi@teramor.in"  # fixed user

    token = generate_tableau_jwt(secrets, tableau_user)

    view_url = next(d["url"] for d in dashboards if d["name"] == selected)
    iframe_url = build_iframe_url(view_url, token)

    st.header(selected)
    tableau_script = '<script type="module" src="https://prod-in-a.online.tableau.com/javascripts/api/tableau.embedding.3.latest.min.js"></script>'

    html_block = f"""
    {tableau_script}
    <iframe 
        src="{iframe_url}"
        width="100%"
        height="900"
        frameborder="0"
        allowfullscreen>
    </iframe>
    """

    st.components.v1.html(html_block, height=930, scrolling=True)


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
