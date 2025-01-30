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
        count = 0
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

def calculate_percentage_change(current_price, price_1_hour_ago):
    if price_1_hour_ago == 0:
        return 0
    return ((current_price - price_1_hour_ago) / price_1_hour_ago) * 100

def update_token_display(token_data):
    st.subheader(f"Displaying {len(token_data)} tokens...")

    total_tokens = len(token_data)
    progress_bar = st.progress(0)  # Initialize the progress bar

    for idx, token in enumerate(token_data):
        # Assuming the data includes price and price_1_hour_ago
        current_price = token.get('price', 0)
        price_1_hour_ago = token.get('price_1_hour_ago', 0)

        # Calculate the percentage change
        if current_price and price_1_hour_ago:
            percentage_change = calculate_percentage_change(current_price, price_1_hour_ago)
            token['percentage_change'] = percentage_change
        else:
            token['percentage_change'] = 0  # If we don't have price data, set change to 0

        # Show token details
        st.write(f"**{token.get('name', 'No Name Available')}**")
        st.write(f"Token Address: {token.get('tokenAddress', 'No Address Available')}")
        st.write(f"Liquidity: {token.get('liquidity', 'N/A')}")
        st.write(f"Volume: {token.get('volume', 'N/A')}")
        st.write(f"Holders: {token.get('holders', 'N/A')}")
        st.write(f"**1 Hour Change**: {token['percentage_change']:.2f}%")
        
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

def show_top_gaining_tokens(token_data):
    # Sort the tokens by percentage change in descending order
    top_tokens = sorted(token_data, key=lambda x: x.get('percentage_change', 0), reverse=True)[:5]
    
    # Display the top 5 gaining tokens
    st.sidebar.subheader("Top 5 Gaining Tokens (Last 1 Hour)")
    for idx, token in enumerate(top_tokens):
        st.sidebar.write(f"{idx + 1}. {token['name']} - {token['percentage_change']:.2f}%")

def refresh_token_list():
    token_data = get_token_data()

    if not token_data:
        st.write("No token data found.")
    else:
        update_token_display(token_data)
        show_top_gaining_tokens(token_data)

# Track active users using session_state
if "user_count" not in st.session_state:
    st.session_state["user_count"] = 1
else:
    st.session_state["user_count"] += 1

# Create the Streamlit app layout
st.set_page_config(page_title="Newest Tokens on Solana and Ethereum", layout="wide")

st.title("Top Tokens on Solana and Ethereum")
st.write("Refreshing token list...")

# Show live user count and visit count
st.sidebar.markdown("### Live Metrics")
st.sidebar.write(f"**Live Users**: {st.session_state['user_count']}")
st.sidebar.write(f"**Total Visits**: {get_view_count()}")

# Increment view count each time a user visits
increment_view_count()

# Add a refresh button
refresh_button_clicked = st.button("Refresh Tokens")
if refresh_button_clicked:
    refresh_token_list()

# Initially load the token list
if not refresh_button_clicked:
    refresh_token_list()
