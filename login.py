# frontend/login.py — FIXED (NO % formatting errors)

import streamlit as st
import base64
import os


def auto_find_bg():
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    if not os.path.isdir(assets_dir):
        return None
    for f in os.listdir(assets_dir):
        if f.startswith("landing_page") and f.split(".")[-1].lower() in ["png", "jpg", "jpeg", "webp"]:
            return os.path.join(assets_dir, f)
    return None


def get_base64_image(path):
    if not path or not os.path.isfile(path):
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def login_page():
    bg_path = auto_find_bg()
    bg_b64 = get_base64_image(bg_path)

    # ----------------------------------------
    # FIXED: use f-string (NO % formatting)
    # ----------------------------------------
    st.markdown(f"""
    <style>
        #MainMenu, header, footer {{visibility: hidden !important;}}

        [data-testid="stStatusWidget"] {{display: none !important;}}
        [data-testid="stNotification"] {{display: none !important;}}
        [data-testid="stDecoration"] {{display: none !important;}}
        [data-testid="stToolbar"] {{display: none !important;}}
        [data-testid="stHeader"] {{display: none !important;}}

        html, body {{
            margin:0 !important;
            padding:0 !important;
            height:100%;
            overflow:hidden !important;
        }}

        [data-testid="stAppViewContainer"] {{
            background: url("data:image/png;base64,{bg_b64}") no-repeat center center fixed;
            background-size: cover;
        }}

        .login-card {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 360px;
            padding: 28px;
            background: rgba(255,255,255,0.94);
            border-radius: 12px;
            box-shadow: 0 10px 35px rgba(0,0,0,0.30);
            font-family: "Segoe UI", sans-serif;
            z-index: 9999;
        }}

        .login-title {{
            font-size: 22px;
            font-weight: 700;
            text-align: center;
            margin-bottom: 18px;
            color: #222;
        }}

        .stTextInput > div > div > input {{
            height: 38px !important;
            padding: 6px 10px !important;
            font-size: 14px !important;
            border-radius: 6px !important;
            border: 1px solid #d0d0d0 !important;
            background: #fff !important;
            color: #000 !important;
        }}

        .login-btn > button {{
            width: 100% !important;
            padding: 8px 0;
            background: #0b4f77 !important;
            color: #fff !important;
            border-radius: 6px !important;
            font-weight: 600;
            font-size: 15px !important;
            border: none;
            margin-top: 10px;
        }}
    </style>
    """, unsafe_allow_html=True)

    # ----------------------------------------
    # LOGIN UI
    # ----------------------------------------
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">Sign In</div>', unsafe_allow_html=True)

    email = st.text_input("Email", placeholder="projects@amigoserp.org",
                          label_visibility="collapsed", key="email_box")

    password = st.text_input("Password", placeholder="Password",
                             type="password", label_visibility="collapsed", key="password_box")

    st.markdown('</div>', unsafe_allow_html=True)

    return email, password
