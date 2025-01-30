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

# File for storing the view count
VIEW_COUNT_FILE = "view_count.txt"

def get_view_count():
    if os.path.exists(VIEW_COUNT_FILE):
        with open(VIEW_COUNT_FILE, "r") as f:
            count = int(f.read())
    else:
        count = 21  # Start total visits at 21 if the file doesn't exist
    return count

def increment_view_count():
    count = get_view_count() + 1
    with open(VIEW_COUNT_FILE, "w") as f:
        f.write(str(count))

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
        # Construct the correct "More Info" URL based on the token's chain
        if token.get('chain') == 'solana':
            more_info_url = f"https://dexscreener.com/solana/{token.get('tokenAddress')}"
            chart_url = f"https://dexscreener.com/solana/{token.get('tokenAddress')}"
        elif token.get('chain') == 'ethereum':
            more_info_url = f"https://coinmarketcap.com/dexscan/ethereum/{token.get('tokenAddress')}"
            chart_url = f"https://dexscreener.com/ethereum/{token.get('tokenAddress')}"
        else:
            more_info_url = None  # Handle other chains if needed, set to None as fallback
            chart_url = None  # Fallback for unsupported chains

        # Show token details
        st.write(f"**{token.get('name', 'No Name Available')}**")
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
            token_data = [token for token in token_data if token.get('chain') == chain_filter]
        
        update_token_display(token_data)

# Track active users using session_state
if "user_ips" not in st.session_state:
    st.session_state["user_ips"] = set()  # Store unique IPs
if "user_count" not in st.session_state:
    st.session_state["user_count"] = 1  # Start user count at 1 (for the first user)
else:
    # Get the user's IP and track unique users
    user_ip = st.request.remote_addr  # Fetch user IP
    if user_ip not in st.session_state["user_ips"]:
        st.session_state["user_ips"].add(user_ip)
        st.session_state["user_count"] += 1

# Create the Streamlit app layout
st.set_page_config(page_title="Newest Tokens on Solana and Ethereum", layout="wide")

st.title("Top Tokens on Solana and Ethereum")
st.write("Refreshing token list...")

# Show live user count and visit count
st.sidebar.markdown("### Live Metrics")
st.sidebar.write(f"**Live Users**: {st.session_state['user_count']}")
st.sidebar.write(f"**Total Visits**: {get_view_count()}")

# Filter option for selecting chain
chain_filter = st.sidebar.radio("Select Chain", ("All Chains", "Solana", "Ethereum"))

# Set the filter value based on the selection
if chain_filter == "Solana":
    chain_filter = "solana"
elif chain_filter == "Ethereum":
    chain_filter = "ethereum"
else:
    chain_filter = None  # No filter if "All Chains" is selected

# Increment view count each time a user visits
increment_view_count()

# Add a refresh button
refresh_button_clicked = st.button("Refresh Tokens")
if refresh_button_clicked:
    refresh_token_list(chain_filter)

# Initially load the token list
if not refresh_button_clicked:
    refresh_token_list(chain_filter)

# Footer with copyright and social media links
st.markdown("""
    <footer style="text-align:center; padding: 10px; font-size: 12px;">
        <p>&copy; 2025 NEXTGONIC. All rights reserved.</p>
        <a href="https://twitter.com/nexgonic" target="_blank">
            <img src="https://upload.wikimedia.org/wikipedia/commons/6/60/Twitter_Logo_2021.svg" width="30" height="30" alt="Twitter">
        </a>
        <a href="https://t.me/nexgonic" target="_blank">
            <img src="https://upload.wikimedia.org/wikipedia/commons/8/83/Telegram_2015_logo.svg" width="30" height="30" alt="Telegram">
        </a>
    </footer>
""", unsafe_allow_html=True)
