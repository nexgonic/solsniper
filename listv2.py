# Set page config first
st.set_page_config(page_title="Soleth Ai Sniper v1 BETA", layout="wide")

import requests
import webbrowser
import streamlit as st
from PIL import Image
from io import BytesIO
import os

# Define the API URL and headers for the request
API_URL = "https://api.dexscreener.com/token-profiles/latest/v1"
FETCH_INTERVAL = 10  # Interval (in seconds) between consecutive fetches
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/58.0.3029.110 Safari/537.36"
    )
}

# Use Google Fonts to set a futuristic font
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
        body {
            font-family: 'Roboto', sans-serif;
        }
    </style>
""", unsafe_allow_html=True)

def get_token_data() -> list:
    try:
        response = requests.get(API_URL, headers=HEADERS)
        response.raise_for_status()

        data = response.json()
        if isinstance(data, dict) and "tokens" in data:
            tokens = data["tokens"]
        elif isinstance(data, list):
            tokens = data
        else:
            return []  # If the response isn't as expected

        return tokens  # Return all tokens, no limit
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []

def update_token_display(token_data):
    st.subheader(f"Displaying {len(token_data)} tokens...")

    total_tokens = len(token_data)
    progress_bar = st.progress(0)  # Initialize the progress bar

    for idx, token in enumerate(token_data):
        # Retrieve token name (check how it's structured in the response)
        token_name = token.get('name', 'No Name Available')

        # Construct the correct "More Info" URL based on the token's chain_id
        if token.get('chain_id') == 'solana':
            more_info_url = f"https://dexscreener.com/solana/{token.get('tokenAddress')}"
            chart_url = f"https://dexscreener.com/solana/{token.get('tokenAddress')}"
        elif token.get('chain_id') == 'ethereum':
            more_info_url = f"https://coinmarketcap.com/dexscan/ethereum/{token.get('tokenAddress')}"
            chart_url = f"https://dexscreener.com/ethereum/{token.get('tokenAddress')}"
        else:
            more_info_url = None  # Handle other chains if needed, set to None as fallback
            chart_url = None  # Fallback for unsupported chains

        # Show token details
        st.write(f"**{token_name}**")  # Display the token name
        st.write(f"Token Address: {token.get('tokenAddress', 'No Address Available')}")
        st.write(f"Liquidity: {token.get('liquidity', 'N/A')}")
        st.write(f"Volume: {token.get('volume', 'N/A')}")
        st.write(f"Holders: {token.get('holders', 'N/A')}")
        
        # Show icon if available
        icon_url = token.get('icon', '')
        if icon_url:
            response = requests.get(icon_url)
            img_data = Image.open(BytesIO(response.content))
            img_data = img_data.resize((50, 50))
            st.image(img_data)

        # Display token address
        token_address = token.get('tokenAddress', 'No Address Available')
        st.text_input("Token Address", value=token_address, key=f"token_address_{idx}")

        # Buttons for More Info and View Chart
        more_info_button = st.button("More Info", key=f"info_button_{idx}")
        view_chart_button = st.button("View Chart", key=f"chart_button_{idx}")

        if more_info_button and more_info_url:
            webbrowser.open(more_info_url)

        if view_chart_button and chart_url:
            webbrowser.open(chart_url)

        progress_bar.progress((idx + 1) / total_tokens)  # Update progress bar

def refresh_token_list(chain_filter=None):
    token_data = get_token_data()

    if not token_data:
        st.write("No token data found.")
    else:
        # Apply chain filter if specified
        if chain_filter:
            # Ensure that the filtering correctly matches chain_id values (case sensitive)
            token_data = [token for token in token_data if token.get('chain_id', '').lower() == chain_filter.lower()]
        
        update_token_display(token_data)

# Add logo above header (Centered) with new logo source URL
st.markdown("""
    <div style="text-align: center;">
        <img src="https://nextgenspeed.com/wp-content/uploads/2025/01/nexgonico_trans.png" width="200" height="200" alt="Soleth Ai Sniper Logo">
    </div>
""", unsafe_allow_html=True)

# Updated Title and Message
st.title("Soleth Ai Sniper v1 BETA")
st.write("Looking for the next 10x...")

# Filter option for selecting chain
chain_filter = st.sidebar.radio("Select Chain", ("All Chains", "Solana", "Ethereum"))

# Set the filter value based on the selection
if chain_filter == "Solana":
    chain_filter = "solana"
elif chain_filter == "Ethereum":
    chain_filter = "ethereum"
else:
    chain_filter = None  # No filter if "All Chains" is selected

# Add a refresh button
refresh_button_clicked = st.button("Refresh Tokens")
if refresh_button_clicked:
    refresh_token_list(chain_filter)

# Initially load the token list
if not refresh_button_clicked:
    refresh_token_list(chain_filter)

# Footer with copyright and social media links (Text color set to white, bold, and black background)
st.markdown("""
    <footer style="text-align:center; padding: 10px; font-size: 14px; font-weight: bold; color: white !important; background-color: black;">
        <p>&copy; 2025 NEXTGONIC. All rights reserved.</p>
        <a href="https://x.com/nexgonic" target="_blank">
            <img src="https://upload.wikimedia.org/wikipedia/commons/6/60/Twitter_Logo_2021.svg" width="30" height="30" alt="Twitter">
        </a>
        <a href="https://t.me/Nexgonic" target="_blank">
            <img src="https://upload.wikimedia.org/wikipedia/commons/8/83/Telegram_2015_logo.svg" width="30" height="30" alt="Telegram">
        </a>
    </footer>
""", unsafe_allow_html=True)

# Sticky bottom bar with black background and social media icons next to the text
st.markdown("""
    <div style="position: fixed; bottom: 0; left: 0; width: 100%; background-color: black; 
    text-align: center; padding: 10px; font-size: 14px; box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1); color: white;">
        <p style="margin: 0;">Let us know what you think and features you would like to see.
        <a href="https://x.com/nexgonic" target="_blank">
            <img src="https://upload.wikimedia.org/wikipedia/commons/6/60/Twitter_Logo_2021.svg" width="30" height="30" alt="Twitter">
        </a>
        <a href="https://t.me/Nexgonic" target="_blank">
            <img src="https://upload.wikimedia.org/wikipedia/commons/8/83/Telegram_2015_logo.svg" width="30" height="30" alt="Telegram">
        </a>
        </p>
    </div>
""", unsafe_allow_html=True)
