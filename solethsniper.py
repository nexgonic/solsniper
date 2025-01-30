import sys
import requests
import streamlit as st
from PIL import Image
from io import BytesIO
import webbrowser

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

# Global variables for filtered tokens
filtered_tokens = []
tokens_displayed = 0  # Keep track of how many tokens have been displayed

################################################################################
# FETCHING TOKEN DATA
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
      chainId
    """
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

        return tokens[:30] if tokens else []  # Return the first 30 tokens

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []


################################################################################
# BACKGROUND & UI CONTROL
################################################################################

def background_search():
    print("Starting token search...")

    tokens = get_token_data()

    # Log the number of fetched tokens but not their raw data
    print(f"Fetched {len(tokens)} tokens.")
    if tokens:
        # Filter tokens based on market cap, holders, age, and chainId being 'solana' or 'ethereum'
        global filtered_tokens
        filtered_tokens = [
            token for token in tokens
            if token.get("marketCap", 0) < 10000000 and  # Relaxed filter
               token.get("holders", 0) < 5000 and  # Relaxed filter
               token.get("age", 0) < 2 and
               token.get("chainId", "") in ["solana", "ethereum"]  # Filter for Solana or Ethereum chainId
        ]

        print(f"After filtering, {len(filtered_tokens)} tokens found.")

        # Display the top 5 tokens
        if filtered_tokens:
            print(f"Displaying top 5 filtered tokens...")
            global tokens_displayed
            tokens_displayed = 5
            for i, token in enumerate(filtered_tokens[:5], start=1):  # Display top 5 filtered tokens
                display_token(token, i)
        else:
            print("No tokens found after filtering.")

        # Show more button becomes visible if there are more than 5 tokens
        if len(filtered_tokens) > 5:
            st.button("Show More", on_click=show_more_tokens)

    else:
        print("No tokens found this round.")


def show_more_tokens():
    """
    Displays the next batch of filtered tokens (after the first 5).
    """
    global tokens_displayed
    remaining_tokens = filtered_tokens[tokens_displayed:tokens_displayed + 5]

    for i, token in enumerate(remaining_tokens, start=tokens_displayed + 1):
        display_token(token, i)

    tokens_displayed += len(remaining_tokens)


################################################################################
# DISPLAYING TOKEN INFO
################################################################################

def display_token(token: dict, index: int):
    """
    Inserts token info into a card layout.
    """
    st.markdown(f"### Token #{index}: {token.get('tokenAddress', 'N/A')}")
    st.markdown(f"**Address:** {token.get('tokenAddress', 'N/A')}")

    # Displaying the icon as an image
    icon_url = token.get("icon", "")
    if icon_url:
        try:
            # Fetch the icon image
            response = requests.get(icon_url)
            if response.status_code == 200 and 'image' in response.headers['Content-Type']:
                img_data = response.content
                img = Image.open(BytesIO(img_data))
                img.thumbnail((100, 100))  # Resize the image to fit within a smaller space
                st.image(img, width=100)
            else:
                print(f"Error loading icon: {icon_url} - Not a valid image")
        except Exception as e:
            print(f"Error loading icon: {e}")

    # URL as clickable link
    url = token.get("url", "")
    if url:
        st.markdown(f"[Visit Token URL]({url})")

    # Links section - clickable
    links_list = token.get("links", [])
    if links_list:
        st.markdown("**Links:**")
        for link in links_list:
            st.markdown(f"[{link}]({link})")
    else:
        st.markdown("**Links:** None")


################################################################################
# MAIN UI SETUP
################################################################################

def main():
    st.set_page_config(page_title="Web 3.0 Dexscreener Tokens", layout="wide")

    st.title("Web 3.0 Dexscreener Tokens")
    st.subheader("Ai Tracked Newest SOL/ETH Pairs")

    st.markdown("### Controls")
    st.button("Fetch Tokens", on_click=background_search)
    st.button("Refresh", on_click=background_search)

    st.markdown("### Token Results")
    # Initial empty placeholder to render the results dynamically
    if not filtered_tokens:
        st.write("No tokens available. Click 'Fetch Tokens' to get started.")

    if filtered_tokens:
        for i, token in enumerate(filtered_tokens[:5], start=1):  # Display top 5 filtered tokens
            display_token(token, i)

    st.markdown("### Footer")
    st.markdown("© Nexgonic")
    st.markdown("[Twitter](https://x.com/nexgonic) | [Telegram](https://telegram.com/nexgonicai) | [Website](https://nexgonic.com)")

if __name__ == "__main__":
    main()
