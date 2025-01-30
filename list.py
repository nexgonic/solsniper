import sys
import webbrowser
import requests
import streamlit as st
from PIL import Image
import threading
import time
from io import BytesIO

################################################################################
# GLOBAL CONSTANTS & CONFIG
################################################################################

API_URL = "https://api.dexscreener.com/token-profiles/latest/v1"
FETCH_INTERVAL = 10  # Interval (in seconds) between consecutive fetches

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/58.0.3029.110 Safari/537.36"
    )
}

# Adjusted for a futuristic full-width solid line
SOLID_LINE = "█" * 150


################################################################################
# UI & LOGGING
################################################################################

def initialize_log_area():
    """ Initialize log area in session state if it doesn't exist. """
    if "log_area" not in st.session_state:
        st.session_state.log_area = ""  # Initialize log_area if not yet set

def append_to_log(message: str, extra_newline: bool = True) -> None:
    """
    Appends plain text to the log with optional extra spacing.
    """
    initialize_log_area()  # Ensure the log_area is initialized

    # Add a newline if specified
    new_message = f"{message}\n\n" if extra_newline else f"{message}\n"

    # Add new message to the log
    st.session_state.log_area += new_message


def display_logs():
    """ Render logs using Streamlit once the session state is updated. """
    if "log_area" in st.session_state:
        st.text_area("Logs", value=st.session_state.log_area, height=300, max_chars=None, key="log_area", disabled=True)


################################################################################
# HYPERLINK HANDLING
################################################################################

hyperlinks_map = {}
hyperlink_id = 0


def add_hyperlink(url: str, display_text: str) -> None:
    """
    Inserts 'display_text' as a clickable link in the log which, when clicked, opens 'url' in the default web browser.
    """
    global hyperlink_id

    tag_name = f"hyper-{hyperlink_id}"
    hyperlink_id += 1

    st.markdown(f"[{display_text}]({url})")


################################################################################
# FETCHING & DISPLAYING TOKENS
################################################################################

def get_token_data() -> list:
    """
    Fetches token data from Dexscreener, returns a list of token dictionaries.
    Only extracts these fields:
      url (clickable link)
      tokenAddress
      icon (image)
      links
      price
      marketCap
      liquidity
      volume
      holders
      age
    """
    try:
        response = requests.get(API_URL, headers=HEADERS)
        response.raise_for_status()

        data = response.json()

        if isinstance(data, dict) and "tokens" in data:
            tokens = data["tokens"]  # Adjust this line according to actual response structure
        elif isinstance(data, list):
            tokens = data
        else:
            return []  # If the response isn't as expected

        # Return the first 30 tokens
        return tokens[:30] if tokens else []

    except requests.exceptions.RequestException as e:
        append_to_log(f"Error fetching data: {e}")  # Log any errors that occur
        return []


def display_token(token: dict, index: int):
    """
    Inserts token info into the display area in the order:
      1) token name (bold)
      2) price (above market cap)
      3) market cap
      4) liquidity
      5) 24-hour volume
      6) holders
      7) age (below holders)
      8) tokenAddress
      9) icon (image)
      10) links (clickable)
    Then inserts the black line.
    """
    # Number the tokens in order
    st.markdown(f"### Token #{index}")

    # Displaying the icon as an image
    icon_url = token.get("icon", "")
    if icon_url:
        try:
            # Fetch the icon image
            response = requests.get(icon_url)
            img_data = response.content
            img = Image.open(BytesIO(img_data))

            # Display the image in the Streamlit app
            st.image(img, caption="Token Icon", use_container_width=True)
        except Exception as e:
            append_to_log(f"Error loading icon: {e}")

    # Price (above market cap)
    price = token.get("price", "N/A")
    st.markdown(f"**Price**: {price}")

    # Token Metrics (Market Cap, Liquidity, 24 Hour Volume, and Holders)
    market_cap = token.get("marketCap", "N/A")
    liquidity = token.get("liquidity", "N/A")
    volume = token.get("volume", "N/A")
    holders = token.get("holders", "N/A")

    st.markdown(f"**Market Cap**: {market_cap}")
    st.markdown(f"**Liquidity**: {liquidity}")
    st.markdown(f"**24h Volume**: {volume}")
    st.markdown(f"**Holders**: {holders}")

    # Age (below holders)
    age = token.get("age", "N/A")
    st.markdown(f"**Age**: {age}")

    # tokenAddress
    st.markdown(f"**tokenAddress**:\n  {token['tokenAddress']}")

    # URL as clickable link
    if token["url"] and token["url"] != "N/A":
        add_hyperlink(token["url"], token["url"])
    else:
        st.markdown("**URL**: N/A")

    # links - Safely check if the key 'links' exists in the token
    links_list = token.get("links", [])
    if links_list:
        st.markdown("**Links**:")
        for link in links_list:
            add_hyperlink(link, link)
    else:
        st.markdown("**Links**: None")


################################################################################
# BACKGROUND & UI CONTROL
################################################################################

def background_search():
    append_to_log("Starting token search...")

    tokens = get_token_data()
    if tokens:
        # Filter tokens based on market cap, holders, and age
        filtered_tokens = [
            token for token in tokens
            if token.get("marketCap", 0) < 5000000 and token.get("holders", 0) < 2000 and token.get("age", 0) < 2
        ]

        append_to_log(f"Found {len(filtered_tokens)} tokens that meet the criteria.")

        for i, token in enumerate(filtered_tokens[:5], start=1):  # Display top 5 filtered tokens
            display_token(token, i)
    else:
        append_to_log("No tokens found this round.")


def fetch_process():
    append_to_log("Fetching new token data...")
    background_search()


def main():
    st.title("Web 3.0 Dexscreener Tokens")
    st.subheader("Prolif SOL Sniper v1")

    st.sidebar.header("Controls")
    fetch_button = st.sidebar.button("Fetch Tokens")

    if fetch_button:
        fetch_process()

    display_logs()


if __name__ == "__main__":
    main()
