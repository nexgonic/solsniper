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

if not st.session_state.authenticated:
    st.title("🔒 Access Restricted")
    password = st.text_input("Enter Password", type="password")
    if st.button("Login"):
        if password == PASSWORD:
            st.session_state.authenticated = True  # Store authentication status
            st.success("✅ Access granted! Welcome to Soleth Ai Sniper v1 BETA")
            st.query_params["authenticated"] = "true"  # ✅ Updated to new query_params method
        else:
            st.warning("❌ Incorrect password. Try again.")

    st.stop()  # Prevents the rest of the app from running until authenticated

# ✅ If the password is correct, the app UI is displayed
st.success("✅ Access granted! Welcome to Soleth Ai Sniper v1 BETA")

# Fetch image dynamically and make it full-width
logo_url = "https://nextgenspeed.com/wp-content/uploads/2025/01/bannerlogo.png"
response = requests.get(logo_url)

if response.status_code == 200:
    img = Image.open(BytesIO(response.content))
    img_buffer = BytesIO()
    img.save(img_buffer, format="PNG")
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()

    # Display full-width responsive image
    st.markdown(f"""
        <style>
            .full-width-img {{
                width: 100%;
                height: auto;
                display: block;
                margin: 0 auto;
                max-width: 100%;
            }}
        </style>
        <div style="text-align: center;">
            <img class="full-width-img" src="data:image/png;base64,{img_base64}" alt="Soleth Ai Sniper Logo">
        </div>
    """, unsafe_allow_html=True)

# App UI continues...
st.title("Soleth Ai Sniper v1 BETA")
st.write("Looking for the next 10x...")
