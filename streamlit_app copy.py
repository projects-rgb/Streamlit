# frontend/streamlit_app.py
import os
import threading
import time
import json
import html
from typing import Dict

import streamlit as st
from auth import generate_tableau_jwt, load_secrets, authenticate_user
# load_dashboards helper will read dashboards.json
BASE = os.path.dirname(__file__)
DASH_FILE = os.path.join(BASE, "dashboards.json")


# --------------------------
# Small Flask token provider
# --------------------------
def start_token_server(host="127.0.0.1", port=5001):
    """
    Start a tiny Flask server that returns a fresh JWT at /new_jwt.
    Runs in background thread.
    """
    try:
        from flask import Flask, jsonify, make_response
        from flask_cors import CORS
    except Exception as e:
        raise RuntimeError("Flask and flask-cors are required. pip install flask flask-cors") from e

    app = Flask("token_provider")
    CORS(app, resources={r"/new_jwt": {"origins": "*"}})

    @app.route("/new_jwt")
    def new_jwt():
        """
        Returns JSON: { "token": "<jwt>" }
        """
        try:
            token = generate_tableau_jwt()
            resp = make_response(jsonify({"token": token}), 200)
            # allow local fetch from streamlit UI
            resp.headers["Cache-Control"] = "no-store"
            return resp
        except Exception as exc:
            resp = make_response(jsonify({"error": str(exc)}), 500)
            return resp

    # Run Flask in a background thread (daemon)
    def run():
        # suppress flask startup messages if you want
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        app.run(host=host, port=port, threaded=True)

    t = threading.Thread(target=run, daemon=True)
    t.start()
    # give server a moment
    time.sleep(0.6)
    return f"http://{host}:{port}"


# --------------------------
# Dashboard loader
# --------------------------
def load_dashboards():
    if not os.path.isfile(DASH_FILE):
        return []
    with open(DASH_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        # support mapping form: { "Executive Summary": "url", ... }
        return [{"name": n, "url": u} for n, u in data.items()]
    if isinstance(data, list):
        return data
    return []


# --------------------------
# Embedding with auto-refresh token
# --------------------------
def embed_tableau_auto_refresh(view_url: str, token_server_url: str, height: int = 900):
    secrets = load_secrets()
    host = secrets.get("host")
    module = f"{host}/javascripts/api/tableau.embedding.3.latest.min.js"

    html_code = f"""
    <!-- Load Tableau embedding v3 library -->
    <script type="module" src="{module}"></script>

    <div id="viz_container" style="width:100%; height:{height}px;"></div>

    <script type="module">
        // When using tableau-viz, we dynamically attach a token provider
        async function attachViz() {{

            console.log("Loading viz with auto-refresh token...");

            const container = document.getElementById("viz_container");
            container.innerHTML = "";

            const viz = document.createElement("tableau-viz");

            // dashboard URL
            viz.src = "{html.escape(view_url)}";

            // sizing
            viz.width = "100%";
            viz.height = "{height}px";
            viz.toolbar = "bottom";

            // token provider function
            viz.token = async () => {{
                console.log("Fetching new JWT token...");
                const res = await fetch("{token_server_url}/new_jwt", {{ cache: "no-store" }});
                const data = await res.json();
                return data.token;
            }};

            container.appendChild(viz);
        }}

        attachViz();
    </script>
    """

    st.components.v1.html(html_code, height=height + 100, scrolling=True)


# --------------------------
# UI Layout
# --------------------------
def sidebar_ui(dashboards):
    st.sidebar.title("Dashboards")

    names = [d["name"] for d in dashboards]
    if "selected_dashboard_name" not in st.session_state:
        st.session_state["selected_dashboard_name"] = names[0] if names else ""

    try:
        default_index = names.index(st.session_state["selected_dashboard_name"]) if st.session_state["selected_dashboard_name"] in names else 0
    except Exception:
        default_index = 0

    selected = st.sidebar.radio("Select dashboard", names, index=default_index)
    st.session_state["selected_dashboard_name"] = selected

    sel = next((d for d in dashboards if d["name"] == selected), None)
    st.session_state["selected_dashboard_url"] = sel["url"] if sel else ""

    st.sidebar.markdown("---")
    st.sidebar.write("Logged in as:")
    st.sidebar.write(f"**{st.session_state.get('username','-')}**")
    if st.sidebar.button("Logout"):
        # clear session
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


def login_page():
    # CSS FIXES EVERYTHING
    st.markdown("""
    <style>

    /* Remove Streamlit default padding */
    .block-container {
        padding: 0 !important;
        margin: 0 !important;
    }
    [data-testid="stAppViewContainer"] {
        padding: 0 !important;
        margin: 0 !important;
        background-size: cover !important;
        background-repeat: no-repeat !important;
        background-attachment: fixed !important;
        background-position: center center !important;
    }

    /* Remove menu, header, footer */
    #MainMenu, header, footer {
        visibility: hidden !important;
        height: 0 !important;
    }

    /* Center login card */
    .login-center {
        position: absolute;
        top: 45%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 420px;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }

    /* Transparent inputs with white text */
    input {
        background: rgba(0,0,0,0.40) !important;
        border: 1px solid rgba(255,255,255,0.4) !important;
        color: white !important;
        height: 42px !important;
        border-radius: 8px !important;
        font-size: 16px !important;
        padding: 6px 10px !important;
    }

    ::placeholder {
        color: rgba(255,255,255,0.7) !important;
        font-size: 16px;
    }

    /* Button styling */
    .stButton>button {
        width: 100%;
        background-color: #0b4f77 !important;
        color: white !important;
        border-radius: 8px;
        height: 40px;
        font-weight: 600;
        margin-top: 10px;
    }

    </style>
    """, unsafe_allow_html=True)

    # BACKGROUND IMAGE FIX
    # auto-detect landing_page.*
    import os, base64
    for ext in ["png", "jpg", "jpeg", "webp"]:
        path = f"assets/landing_page.{ext}"
        if os.path.exists(path):
            bg = base64.b64encode(open(path, "rb").read()).decode()
            st.markdown(
                f"""
                <style>
                [data-testid="stAppViewContainer"] {{
                    background-image: url("data:image/{ext};base64,{bg}");
                }}
                </style>
                """,
                unsafe_allow_html=True,
            )
            break

    # LOGIN CARD UI
    st.markdown("<div class='login-center'>", unsafe_allow_html=True)

    email = st.text_input("Email", placeholder="you@company.com", label_visibility="collapsed")
    pwd = st.text_input("Password", placeholder="Password", type="password", label_visibility="collapsed")

    st.markdown("</div>", unsafe_allow_html=True)

    return email.strip(), pwd


def main():
    st.set_page_config(page_title="Client Portal", layout="wide", page_icon="📊")
    # start token server (only once)
    if "token_server_url" not in st.session_state:
        try:
            token_server_url = start_token_server(host="127.0.0.1", port=5001)
            st.session_state["token_server_url"] = token_server_url
        except Exception as e:
            st.error("Failed to start token server. Please install flask and flask-cors.")
            st.error(str(e))
            return

    dashboards = load_dashboards()
    if not dashboards:
        st.warning("No dashboards configured in dashboards.json.")
        return

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        # show login UI and validate against secrets.json admin credentials
        email, pwd = login_page()
        # we also allow manual login button so no experimental_rerun usage
        if st.button("Login (Submit)"):
            # check admin user from secrets.json
            try:
                secrets = load_secrets()
            except Exception as e:
                st.error("secrets.json missing or invalid")
                st.error(str(e))
                return

            admin_user = secrets.get("admin_user")
            admin_pass = secrets.get("admin_password")

            # if admin credentials exist in secrets.json, allow those
            if admin_user and admin_pass and email == admin_user and pwd == admin_pass:
                st.session_state["logged_in"] = True
                st.session_state["username"] = email
                st.rerun()
            else:
                # fallback: if auth.authenticate_user is implemented, use it
                try:
                    if authenticate_user(email, pwd):
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = email
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
                except Exception:
                    st.error("Invalid credentials")

        return

    # logged in — show dashboard
    sidebar_ui(dashboards)
    st.header(st.session_state.get("selected_dashboard_name", ""))

    url = st.session_state.get("selected_dashboard_url", "")
    if not url:
        st.warning("No URL set for selected dashboard.")
        return

    # embed with token provider
    token_server_url = st.session_state.get("token_server_url")
    embed_tableau_auto_refresh(url, token_server_url, height=900)


if __name__ == "__main__":
    main()
