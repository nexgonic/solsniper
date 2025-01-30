import requests
import webbrowser
import streamlit as st
from PIL import Image
from io import BytesIO
import base64

# Set page config first, before any other Streamlit commands
st.set_page_config(page_title="Soleth Ai Sniper v1 BETA", layout="wide")

# Password protection (User must enter "early" to access)
def check_password():
    """Function to handle password authentication."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        password = st.text_input("Enter Password", type="password")
        if password == "early":
            st.session_state.authenticated = True
            st.experimental_rerun()
        else:
            st.warning("Incorrect password. Try again.")
            st.stop()

check_password()  # Call the password check function

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
        token_name = token.get('name', 'No Name Available')

        if token.get('chain_id') == 'solana':
            more_info_url = f"https://dexscreener.com/solana/{token.get('tokenAddress')}"
            chart_url = f"https://dexscreener.com/solana/{token.get('tokenAddress')}"
        elif token.get('chain_id') == 'ethereum':
            more_info_url = f"https://coinmarketcap.com/dexscan/ethereum/{token.get('tokenAddress')}"
            chart_url = f"https://dexscreener.com/ethereum/{token.get('tokenAddress')}"
        else:
            more_info_url = None  
            chart_url = None  

        st.write(f"**{token_name}**")  
        st.write(f"Token Address: {token.get('tokenAddress', 'No Address Available')}")
        st.write(f"Liquidity: {token.get('liquidity', 'N/A')}")
        st.write(f"Volume: {token.get('volume', 'N/A')}")
        st.write(f"Holders: {token.get('holders', 'N/A')}")

        icon_url = token.get('icon', '')
        if icon_url:
            response = requests.get(icon_url)
            img_data = Image.open(BytesIO(response.content))
            img_data = img_data.resize((50, 50))
            st.image(img_data)

        token_address = token.get('tokenAddress', 'No Address Available')
        st.text_input("Token Address", value=token_address, key=f"token_address_{idx}")

        more_info_button = st.button("More Info", key=f"info_button_{idx}")
        view_chart_button = st.button("View Chart", key=f"chart_button_{idx}")

        if more_info_button and more_info_url:
            webbrowser.open(more_info_url)

        if view_chart_button and chart_url:
            webbrowser.open(chart_url)

        progress_bar.progress((idx + 1) / total_tokens) 

def refresh_token_list(chain_filter=None):
    token_data = get_token_data()

    if not token_data:
        st.write("No token data found.")
    else:
        if chain_filter:
            token_data = [token for token in token_data if token.get('chain_id', '').lower() == chain_filter.lower()]
        
        update_token_display(token_data)

if refresh_button_clicked:
    refresh_token_list(chain_filter)

if not refresh_button_clicked:
    refresh_token_list(chain_filter)

# Footer with copyright and social media links
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
