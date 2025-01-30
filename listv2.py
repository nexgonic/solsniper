import requests
import webbrowser
import streamlit as st
from PIL import Image
from io import BytesIO
import base64

# Set page config first, before any other Streamlit commands
st.set_page_config(page_title="Soleth Ai Sniper v1 BETA", layout="wide")

# 🔒 Password protection using session state
PASSWORD = "early"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Fetch image dynamically for authentication page
logo_url = "https://nextgenspeed.com/wp-content/uploads/2025/01/bannerlogo.png"
response = requests.get(logo_url)

if response.status_code == 200:
    img = Image.open(BytesIO(response.content))
    img_buffer = BytesIO()
    img.save(img_buffer, format="PNG")
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()

    # Centered image at the top of the authentication page with a title below
    st.markdown(f"""
        <style>
            .auth-logo-container {{
                text-align: center;
                margin-bottom: 10px;
            }}
            .auth-logo {{
                width: 300px;
                height: auto;
                display: inline-block;
            }}
            .title-text {{
                text-align: center;
                font-size: 15px;
                font-weight: bold;
                margin-top: 5px;
            }}
        </style>
        <div class="auth-logo-container">
            <img class="auth-logo" src="data:image/png;base64,{img_base64}" alt="Soleth Ai Sniper Logo">
            <p class="title-text">Soleth Ai Sniper v1 BETA</p>
        </div>
    """, unsafe_allow_html=True)

if not st.session_state.authenticated:
    st.title("🔒 Access Restricted")
    password = st.text_input("Enter Password", type="password")
    
    if st.button("Login"):
        if password == PASSWORD:
            st.session_state.authenticated = True  # Store authentication status
            st.success("✅ Access granted! Welcome to Soleth Ai Sniper v1 BETA")
            st.rerun()  # 🔄 Reload the app UI to show tokens
        else:
            st.warning("❌ Incorrect password. Try again.")

    st.stop()  # Prevents the rest of the app from running until authenticated

# ✅ If the password is correct, continue to fetch & display tokens
st.success("✅ Access granted! Welcome to Soleth Ai Sniper v1 BETA")

# Full-width image in main app with title
st.markdown(f"""
    <style>
        .full-width-img {{
            width: 100%;
            height: auto;
            display: block;
            margin: 0 auto;
            max-width: 100%;
        }}
        .main-title {{
            text-align: center;
            font-size: 15px;
            font-weight: bold;
            margin-top: 5px;
        }}
    </style>
    <div style="text-align: center;">
        <img class="full-width-img" src="data:image/png;base64,{img_base64}" alt="Soleth Ai Sniper Logo">
        <p class="main-title">Soleth Ai Sniper v1 BETA</p>
    </div>
""", unsafe_allow_html=True)
