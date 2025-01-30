import requests
import tkinter as tk
from tkinter import messagebox
from tkinter.ttk import Progressbar
from PIL import Image, ImageTk
import io
import pyperclip
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import webbrowser
import concurrent.futures

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

    # Setting up Selenium WebDriver with Chrome options for headless mode
    options = Options()
    options.add_argument("--headless")  # Run in headless mode (no UI)
    options.add_argument("--disable-gpu")  # Disable GPU hardware acceleration
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(snifscore_url)
        time.sleep(3)  # Wait for the page to load

        # Get the page content
        page_content = driver.page_source

        # For Ethereum, check if the page contains "LOW RISK OF HONEYPOT"
        if chain == 'ethereum' and "LOW RISK OF HONEYPOT" not in page_content:
            print(f"Skipping Ethereum token due to high risk of honeypot.")
            driver.quit()
            return True  # Token is risky, skip it

        # For Solana (SolSniffer), check for significant private wallet supply or unlocked LP
        if chain == 'solana':
            if "Private wallet holds significant supply." in page_content:
                print(f"Skipping Solana token due to significant supply held by private wallet.")
                driver.quit()
                return True

            if "Large portion of LP is unlocked." in page_content:
                print(f"Skipping Solana token due to unlocked LP.")
                driver.quit()
                return True

        driver.quit()
        return False  # If the token passes the checks, return False (allow it)

    except Exception as e:
        print(f"Error checking {snifscore_url} for {token_address}: {e}")
        driver.quit()
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

def refresh_token_list():
    print("Refreshing token list...")
    token_data = get_token_data()

    if not token_data:
        print("No token data found.")
    else:
        print(f"Found {len(token_data)} tokens.")

    if token_data:
        update_token_display(token_data)

def update_token_display(token_data):
    print(f"Displaying {len(token_data)} tokens...")

    total_tokens = len(token_data)
    progress_bar["maximum"] = total_tokens  # Set the maximum value of the progress bar

    # Collect token addresses and chains to check LP status in parallel
    token_addresses = [token.get('tokenAddress', 'No Address Available') for token in token_data]
    token_chains = [token.get('chain', 'solana') for token in token_data]  # Default to Solana if not specified

    # Use ThreadPoolExecutor to check LP status concurrently
    with concurrent.futures.ThreadPoolExecutor() as executor:
        lp_results = list(executor.map(lambda addr, chain: check_lp_unlocked(addr, chain), token_addresses, token_chains))

    for idx, (token, lp_status) in enumerate(zip(token_data, lp_results)):
        if lp_status:
            progress_bar["value"] = idx + 1  # Update progress bar
            continue  # Skip this token if its LP is unlocked or it has the specified phrase

        frame = tk.Frame(token_frame, bg='#364f6b', bd=0, relief="flat", highlightthickness=0)
        frame.grid(row=idx, column=0, sticky="ew", pady=5, padx=10)

        icon_label = tk.Label(frame, bg="#364f6b")
        token_address_label = tk.Label(frame, text=token.get('tokenAddress', 'No Address Available'),
                                       font=("Helvetica", 12, "bold"), fg="#f1f1f1", bg="#364f6b")

        # Update the Copy button command to copy token's Dexscreener API token address
        copy_button = tk.Button(frame, text="Copy", command=lambda token_address=token.get('tokenAddress'): pyperclip.copy(token_address),
                                font=("Helvetica", 10), bg="#fca311", fg="#ffffff")

        # Info button to open Solsniffer URL
        info_button = tk.Button(frame, text="Info", command=lambda token_address=token.get('tokenAddress'): open_url(f"https://www.solsniffer.com/scanner/{token_address}"),
                                font=("Helvetica", 10), bg="#fca311", fg="#ffffff")

        # Chart button to open the Dexscreener token URL
        chart_button = tk.Button(frame, text="Chart", command=lambda url=token.get('url'): open_url(url),
                                 font=("Helvetica", 10), bg="#fca311", fg="#ffffff")

        icon_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        token_address_label.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        copy_button.grid(row=0, column=2, padx=10, pady=5, sticky="w")
        info_button.grid(row=0, column=3, padx=10, pady=5, sticky="w")
        chart_button.grid(row=0, column=4, padx=10, pady=5, sticky="w")

        icon_url = token.get('icon', '')
        icon_img = None
        if icon_url:
            response = requests.get(icon_url)
            img_data = Image.open(io.BytesIO(response.content))
            img_data = img_data.resize((50, 50))
            icon_img = ImageTk.PhotoImage(img_data)
            icon_label.config(image=icon_img)
            icon_label.image = icon_img  # Keep a reference

        token_address_label.bind("<Button-1>", lambda e, url=token.get('url'): open_screener_url(url))

        def show_more_info():
            more_info_window = tk.Toplevel(root)
            more_info_window.title(f"Token Info - {token_address_label.cget('text')}")
            more_info_window.geometry("400x300")
            more_info_window.configure(bg="#2d3e50")

            label = tk.Label(more_info_window, text=f"Token Address: {token.get('tokenAddress', 'N/A')}",
                             font=("Helvetica", 12), fg="#ffffff", bg="#2d3e50")
            label.pack(pady=10)

            liquidity_label = tk.Label(more_info_window, text=f"Liquidity: {token.get('liquidity', 'N/A')}",
                                       font=("Helvetica", 12), fg="#ffffff", bg="#2d3e50")
            liquidity_label.pack(pady=5)

            volume_label = tk.Label(more_info_window, text=f"Volume: {token.get('volume', 'N/A')}", font=("Helvetica", 12),
                                    fg="#ffffff", bg="#2d3e50")
            volume_label.pack(pady=5)

            holders_label = tk.Label(more_info_window, text=f"Holders: {token.get('holders', 'N/A')}",
                                     font=("Helvetica", 12), fg="#ffffff", bg="#2d3e50")
            holders_label.pack(pady=5)

        frame.bind("<Button-1>", lambda e, frame=frame: show_more_info())
        progress_bar["value"] = idx + 1  # Update progress bar

def refresh_token_list_thread():
    threading.Thread(target=refresh_token_list).start()

def open_url(url):
    webbrowser.open(url)

# Create the main GUI window
root = tk.Tk()
root.title("Newest Tokens on Solana and Ethereum")
root.geometry("1250x950")
root.configure(bg='#1e213a')

# Add a label for the title
title_label = tk.Label(root, text="Top Tokens", font=("Helvetica", 28, "bold"), fg="#f1f1f1", bg="#1e213a")
title_label.pack(pady=30)

# Create a frame to hold the tokens list
token_frame = tk.Frame(root, bg="#2a2f46", bd=0)
token_frame.pack(fill="both", expand=True, pady=20)

# Make sure all columns in token_frame are of equal width
token_frame.grid_columnconfigure(0, weight=1)
token_frame.grid_columnconfigure(1, weight=1)
token_frame.grid_columnconfigure(2, weight=1)
token_frame.grid_columnconfigure(3, weight=1)
token_frame.grid_columnconfigure(4, weight=1)

# Add a progress bar
progress_bar = Progressbar(root, orient="horizontal", length=500, mode="determinate")
progress_bar.pack(pady=20)

# Add a refresh button
refresh_button = tk.Button(root, text="Refresh Tokens", font=("Helvetica", 16), bg="#fca311", fg="#ffffff",
                           command=refresh_token_list_thread)
refresh_button.pack(pady=20)

# Initially load the token list
refresh_token_list_thread()

# Run the GUI main loop
root.mainloop()
