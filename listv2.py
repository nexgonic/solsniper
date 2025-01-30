import requests
from bs4 import BeautifulSoup
import streamlit as st
import webbrowser
from PIL import Image
from io import BytesIO
import os

# Define the CoinMarketCap DexScan URL
ETHEREUM_DEXSCAN_URL = "https://coinmarketcap.com/dexscan/ethereum"
SOLANA_DEXSCAN_URL = "https://coinmarketcap.com/dexscan/solana"

# Function to scrape data for top gaining tokens
def scrape_top_gaining_tokens():
    # Fetch the CoinMarketCap DexScan page (Ethereum and Solana)
    response = requests.get(ETHEREUM_DEXSCAN_URL)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the table that contains the token data
    table = soup.find('table', {'class': 'cmc-table'})
    rows = table.find_all('tr')[1:]  # Skip header row

    tokens = []
    for row in rows:
        columns = row.find_all('td')
        if len(columns) > 3:
            token_name = columns[1].get_text(strip=True)
            percentage_change_1h = columns[3].get_text(strip=True)
            
            # Extract percentage change and ignore empty values
            try:
                percentage_change_1h = float(percentage_change_1h.replace('%', '').strip())
                tokens.append((token_name, percentage_change_1h))
            except ValueError:
                continue

    # Sort by percentage change and return the top 5
    tokens_sorted = sorted(tokens, key=lambda x: x[1], reverse=True)[:5]
    return tokens_sorted

def get_view_count():
    if os.path.exists("view_count.txt"):
        with open("view_count.txt", "r") as f:
            count = int(f.read())
    else:
        count = 0
    return count

def increment_view_count():
    count = get_view_count() + 1
    with open("view_count.txt", "w") as f:
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

def update_token_display():
    # Get the top gaining tokens
    top_gaining_tokens = scrape_top_gaining_tokens()
    
    # Display the top gaining tokens
    st.sidebar.subheader("Top 5 Gaining Tokens (Last 1 Hour)")
    for idx, (token_name, percentage_change) in enumerate(top_gaining_tokens):
        st.sidebar.write(f"{idx + 1}. {token_name} - {percentage_change:.2f}%")

# Streamlit App Layout
st.set_page_config(page_title="Top Gaining Tokens - CoinMarketCap DexScan", layout="wide")
st.title("Live Top Gaining Tokens (Last 1 Hour)")

# Show live user count and visit count
st.sidebar.markdown("### Live Metrics")
st.sidebar.write(f"**Live Users**: {st.session_state.get('user_count', 1)}")

# Track active users using session_state
if "user_count" not in st.session_state:
    st.session_state["user_count"] = 1
else:
    st.session_state["user_count"] += 1

# Display the top gaining tokens
update_token_display()

# Add a refresh button
if st.button("Refresh Tokens"):
    update_token_display()
