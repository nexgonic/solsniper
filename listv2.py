import requests
import tkinter as tk
from tkinter import messagebox
from tkinter.ttk import Progressbar
from PIL import Image, ImageTk
import io
import pyperclip
import threading
import asyncio
import aiohttp
import random

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

# Flag to control pause and resume
is_paused = False

# Asynchronous function to check the LP unlocked status
async def check_lp_unlocked(session, token_address: str, chain: str) -> bool:
    if chain == 'solana':
        snifscore_url = f"https://www.solsniffer.com/scanner/{token_address}"
    elif chain == 'ethereum':
        snifscore_url = f"https://honeypot.is/ethereum?address={token_address}"
    else:
        return False

    retries = 3
    for attempt in range(retries):
        try:
            async with session.get(snifscore_url) as response:
                page_content = await response.text()

                if chain == 'ethereum' and "LOW RISK OF HONEYPOT" not in page_content:
                    return True

                if chain == 'solana':
                    if "Private wallet holds significant supply." in page_content:
                        return True
                    if "Large portion of LP is unlocked." in page_content:
                        return True

                return False
        except Exception as e:
            print(f"Error checking {snifscore_url} for {token_address}: {e}")
            if attempt < retries - 1:
                delay = random.uniform(2, 5)
                await asyncio.sleep(delay)
            else:
                return False

# Function to fetch token data
async def get_token_data(session) -> list:
    try:
        response = await session.get(API_URL, headers=HEADERS)
        response.raise_for_status()

        data = await response.json()
        if isinstance(data, dict) and "tokens" in data:
            tokens = data["tokens"]
        elif isinstance(data, list):
            tokens = data
        else:
            return []
        print(f"Fetched {len(tokens)} tokens.")
        return tokens
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []

# Function to refresh token list
async def refresh_token_list():
    print("Refreshing token list...")
    output_label.config(text="Refreshing token list...")  # Update output label
    
    async with aiohttp.ClientSession() as session:
        token_data = await get_token_data(session)

        if not token_data:
            print("No token data found.")
            output_label.config(text="No token data found.")
        else:
            print(f"Found {len(token_data)} tokens.")
            output_label.config(text=f"Found {len(token_data)} tokens.")

        if token_data:
            await update_token_display(session, token_data)

# Function to update token display
async def update_token_display(session, token_data):
    print(f"Displaying {len(token_data)} tokens...")
    output_label.config(text=f"Displaying {len(token_data)} tokens...")  # Update output label
    if not token_data:
        print("No tokens to display.")
        return

    total_tokens = len(token_data)
    progress_bar["maximum"] = total_tokens

    token_addresses = [token.get('tokenAddress', 'No Address Available') for token in token_data]
    token_chains = [token.get('chain', 'solana') for token in token_data]

    # Run the LP check concurrently for all tokens
    lp_results = await asyncio.gather(
        *[check_lp_unlocked(session, addr, chain) for addr, chain in zip(token_addresses, token_chains)]
    )

    for idx, (token, lp_status) in enumerate(zip(token_data, lp_results)):
        if is_paused:  # Check if pause button has been clicked
            return
        if lp_status:
            progress_bar["value"] = idx + 1
            continue

        frame = tk.Frame(token_frame, bg='#364f6b', bd=0, relief="flat", highlightthickness=0)
        frame.grid(row=idx, column=0, sticky="ew", pady=5, padx=10)

        icon_label = tk.Label(frame, bg="#364f6b")
        token_address_label = tk.Label(frame, text=token.get('tokenAddress', 'No Address Available'),
                                       font=("Helvetica", 12, "bold"), fg="#f1f1f1", bg="#364f6b")

        copy_button = tk.Button(frame, text="Copy", command=lambda token_address=token.get('tokenAddress'): pyperclip.copy(token_address),
                                font=("Helvetica", 10), bg="#fca311", fg="#ffffff")

        info_button = tk.Button(frame, text="Info", command=lambda token_address=token.get('tokenAddress'): open_url(f"https://www.solsniffer.com/scanner/{token_address}"),
                                font=("Helvetica", 10), bg="#fca311", fg="#ffffff")

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
            icon_label.image = icon_img

        progress_bar["value"] = idx + 1

# Refresh token list in a background thread
def refresh_token_list_thread():
    threading.Thread(target=lambda: asyncio.run(refresh_token_list()), daemon=True).start()

def open_url(url):
    webbrowser.open(url)

def toggle_pause():
    global is_paused
    is_paused = not is_paused
    if is_paused:
        pause_button.config(text="Resume")
    else:
        pause_button.config(text="Pause")
        refresh_token_list_thread()  # Continue fetching if resumed

# Create the main GUI window
root = tk.Tk()
root.title("Newest Tokens on Solana and Ethereum")
root.geometry("1250x950")
root.configure(bg='#1e213a')

# Add a label for the title
title_label = tk.Label(root, text="Top Tokens", font=("Helvetica", 28, "bold"), fg="#f1f1f1", bg="#1e213a")
title_label.pack(pady=30)

# Create a label for console output above the progress bar
output_label = tk.Label(root, text="Initializing...", font=("Helvetica", 12), fg="#f1f1f1", bg="#1e213a")
output_label.pack(pady=10)

# Create a frame to hold the tokens list
token_frame = tk.Frame(root, bg="#2a2f46", bd=0)
token_frame.pack(fill="both", expand=True, pady=20)

# Add a styled progress bar
progress_bar = Progressbar(root, orient="horizontal", length=800, mode="determinate", style="TProgressbar")
progress_bar.pack(pady=20)

# Create buttons for Refresh and Pause
button_frame = tk.Frame(root, bg="#1e213a")
button_frame.pack(pady=10)

refresh_button = tk.Button(button_frame, text="Refresh Tokens", font=("Helvetica", 16), bg="#fca311", fg="#ffffff", command=refresh_token_list_thread)
refresh_button.grid(row=0, column=0, padx=10)

pause_button = tk.Button(button_frame, text="Pause", font=("Helvetica", 16), bg="#fca311", fg="#ffffff", command=toggle_pause)
pause_button.grid(row=0, column=1, padx=10)

# Initially load the token list in a background thread
refresh_token_list_thread()

# Run the GUI main loop
root.mainloop()
