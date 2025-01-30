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

    # Centered image at the top of the authentication page
    st.markdown(f"""
        <style>
            .auth-logo-container {{
                text-align: center;
                margin-bottom: 20px;
            }}
            .auth-logo {{
                width: 300px;
                height: auto;
                display: inline-block;
            }}
        </style>
        <div class="auth-logo-container">
            <img class="auth-logo" src="data:image/png;base64,{img_base64}" alt="Soleth Ai Sniper Logo">
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

# Full-width image in main app
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

# ✅ Sidebar Filter option for selecting chain
chain_filter = st.sidebar.radio("Select Chain", ("All Chains", "Solana", "Ethereum"))

# Convert filter value to match API
if chain_filter == "Solana":
    chain_filter = "solana"
elif chain_filter == "Ethereum":
    chain_filter = "ethereum"
else:
    chain_filter = None  # No filter if "All Chains" is selected

# ✅ Refresh button
refresh_button_clicked = st.button("Refresh Tokens")

if refresh_button_clicked:
    refresh_token_list = get_token_data(chain_filter)
    update_token_display(refresh_token_list)
else:
    refresh_token_list = get_token_data(chain_filter)
    update_token_display(refresh_token_list)  # Load tokens initially

# ✅ Feedback Button (Opens Twitter with pre-filled tweet)
tweet_text = "I'm using Soleth Ai Sniper and have feedback! 🚀 @nexgonic"
tweet_url = f"https://twitter.com/intent/tweet?text={tweet_text}"

st.markdown("""
    <style>
        .feedback-button-container {
            text-align: center;
            margin-top: 20px;
        }
        .feedback-button {
            background-color: #1DA1F2;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            display: inline-block;
            text-decoration: none;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown(f"""
    <div class="feedback-button-container">
        <a href="{tweet_url}" target="_blank" class="feedback-button">📝 Give Feedback on Twitter</a>
    </div>
""", unsafe_allow_html=True)

# ✅ Footer with social media links
st.markdown("""
    <footer style="text-align:center; padding: 10px; font-size: 14px; font-weight: bold; color: white !important; background-color: black;">
        <p>&copy; 2025 NEXTGONIC. All rights reserved.</p>
        <a href="https://x.com/nexgonic" target="_blank">
            <i class="fab fa-twitter" style="font-size: 30px; color: white;"></i>
        </a>
        <a href="https://t.me/Nexgonic" target="_blank">
            <i class="fab fa-telegram" style="font-size: 30px; color: white;"></i>
        </a>
    </footer>
""", unsafe_allow_html=True)
