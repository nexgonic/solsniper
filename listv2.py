import requests
import threading
import time
import webbrowser
import concurrent.futures
import streamlit as st
from PIL import Image
from io import BytesIO

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

def check_lp_unlocked(token_address: str, chain: str) -> bool:
    """
    Checks if the token has unlocked LP or meets certain criteria for Solana or Ethereum.
    For Ethereum tokens, it uses Honeypot.is for filtering with a "LOW RISK OF HONEYPOT" check.
    """
    if chain == 'solana':
        snifscore_url = f"https://www.solsniffer.com/scanner/{token_address}"
    elif chain == 'ethereum':
        snifscore_url = f"https://honeypot.is/ethereum?address={token_address}"
    else:
        return False  # If it's neither Solana nor Ethereum, return False

    try:
        response = requests.get(snifscore_url)
        page_content = response.text

        # For Ethereum, check if the page contains "LOW RISK OF HONEYPOT"
        if chain == 'ethereum' and "LOW RISK OF HONEYPOT" not in page_content:
            print(f"Skipping Ethereum token due to high risk of honeypot.")
            return True  # Token is risky, skip it

        # For Solana (SolSniffer), check for significant private wallet supply or unlocked LP
        if chain == 'solana':
            if "Private wallet holds significant supply." in page_content:
                print(f"Skipping Solana token due to significant supply held by private wallet.")
                return True

            if "Large portion of LP is unlocked." in page_content:
                print(f"Skipping Solana token due to unlocked LP.")
                return True

        return False  # If the token passes the checks, return False (allow it)

    except Exception as e:
        print(f"Error checking {snifscore_url} for {token_address}: {e}")
        return False

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

    # Collect token addresses and chains to check LP status in parallel
    token_addresses = [token.get('tokenAddress', 'No Address Available') for token in token_data]
    token_chains = [token.get('chain', 'solana') for token in token_data]  # Default to Solana if not specified

    # Use ThreadPoolExecutor to check LP status concurrently
    with concurrent.futures.ThreadPoolExecutor() as executor:
        lp_results = list(executor.map(lambda addr, chain: check_lp_unlocked(addr, chain), token_addresses, token_chains))

    for idx, (token, lp_status) in enumerate(zip(token_data, lp_results)):
        if lp_status:
            progress_bar.progress((idx + 1) / total_tokens)  # Update progress bar
            continue  # Skip this token if its LP is unlocked or it has the specified phrase

        # Display the token info in the app
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

        # Instead of copying to clipboard, use a text input for the token address
        token_address = token.get('tokenAddress', 'No Address Available')
        st.text_input("Token Address", value=token_address, key=f"token_address_{idx}")

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

        # Track button state with session_state
        if f"clicked_info_{idx}" not in st.session_state:
            st.session_state[f"clicked_info_{idx}"] = False
        if f"clicked_chart_{idx}" not in st.session_state:
            st.session_state[f"clicked_chart_{idx}"] = False

        # Create unique button keys for each token
        info_button_key = f"info_button_{idx}"
        chart_button_key = f"chart_button_{idx}"

        # Buttons for More Info and View Chart
        if st.button("More Info", key=info_button_key) and not st.session_state[f"clicked_info_{idx}"]:
            st.session_state[f"clicked_info_{idx}"] = True
            if more_info_url:
                webbrowser.open(more_info_url)

        if st.button("View Chart", key=chart_button_key) and not st.session_state[f"clicked_chart_{idx}"]:
            st.session_state[f"clicked_chart_{idx}"] = True
            if chart_url:
                webbrowser.open(chart_url)

        progress_bar.progress((idx + 1) / total_tokens)  # Update progress bar

def refresh_token_list():
    token_data = get_token_data()

    if not token_data:
        st.write("No token data found.")
    else:
        update_token_display(token_data)

# Create the Streamlit app layout
st.set_page_config(page_title="Newest Tokens on Solana and Ethereum", layout="wide")

st.title("Top Tokens on Solana and Ethereum")
st.write("Refreshing token list...")

# Add a refresh button
if st.button("Refresh Tokens"):
    refresh_token_list()

# Initially load the token list
refresh_token_list()
