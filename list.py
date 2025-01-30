import sys
import webbrowser
import requests
import tkinter as tk
from tkinter import scrolledtext
from PIL import Image, ImageTk  # Import Pillow for image handling
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

def append_to_log(message: str, extra_newline: bool = True) -> None:
    """
    Appends plain text to the end of the scrolledtext widget with optional extra spacing.
    For normal status messages or token output.
    """
    text = f"{message}\n\n" if extra_newline else f"{message}\n"
    log_text.insert(tk.END, text)
    log_text.see(tk.END)


################################################################################
# HYPERLINK HANDLING
################################################################################

hyperlinks_map = {}
hyperlink_id = 0


def add_hyperlink(url: str, display_text: str) -> None:
    """
    Inserts 'display_text' as a clickable link in the scrolledtext widget
    which, when clicked, opens 'url' in the default web browser.
    """
    global hyperlink_id

    tag_name = f"hyper-{hyperlink_id}"
    hyperlink_id += 1

    log_text.insert(tk.END, display_text, (tag_name,))
    log_text.insert(tk.END, "\n")  # new line after link

    hyperlinks_map[tag_name] = url

    def click_callback(event, tag=tag_name):
        link_url = hyperlinks_map[tag]
        webbrowser.open(link_url)

    log_text.tag_bind(tag_name, "<Button-1>", click_callback)
    log_text.tag_config(tag_name, foreground="#1E90FF", underline=True)


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
    Inserts token info into the scrolledtext widget in the order:
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
    log_text.insert(tk.END, f"Token #{index}\n", "bold_title")

    # Displaying the icon as an image
    icon_url = token.get("icon", "")
    if icon_url:
        try:
            # Fetch the icon image
            response = requests.get(icon_url)
            img_data = response.content
            img = Image.open(BytesIO(img_data))
            img.thumbnail((100, 100))  # Resize the image to fit within a smaller space
            img_tk = ImageTk.PhotoImage(img)

            # Display the image in the Tkinter window
            label_img = tk.Label(log_text, image=img_tk)
            label_img.image = img_tk  # Keep a reference to the image
            log_text.window_create(tk.END, window=label_img)  # Add the image to the text widget
            log_text.insert(tk.END, "\n\n")
        except Exception as e:
            append_to_log(f"Error loading icon: {e}")

    # Price (above market cap)
    price = token.get("price", "N/A")
    log_text.insert(tk.END, f"Price: {price}\n", "bold_label")

    # Token Metrics (Market Cap, Liquidity, 24 Hour Volume, and Holders)
    market_cap = token.get("marketCap", "N/A")
    liquidity = token.get("liquidity", "N/A")
    volume = token.get("volume", "N/A")
    holders = token.get("holders", "N/A")

    log_text.insert(tk.END,
                    f"Market Cap: {market_cap}\nLiquidity: {liquidity}\n24h Volume: {volume}\nHolders: {holders}\n\n",
                    "bold_label")

    # Age (below holders)
    age = token.get("age", "N/A")
    log_text.insert(tk.END, f"Age: {age}\n\n", "bold_label")

    # tokenAddress
    log_text.insert(tk.END, f"tokenAddress:\n  {token['tokenAddress']}\n\n")

    # URL as clickable link
    log_text.insert(tk.END, "URL:\n", "bold_label")
    if token["url"] and token["url"] != "N/A":
        add_hyperlink(token["url"], token["url"])
    else:
        log_text.insert(tk.END, "N/A\n\n")

    # links - Safely check if the key 'links' exists in the token
    links_list = token.get("links", [])
    if links_list:
        log_text.insert(tk.END, "links:\n", "bold_label")
        for link in links_list:
            # Display only the URL and make it clickable
            add_hyperlink(link, link)
            log_text.insert(tk.END, "\n")
    else:
        log_text.insert(tk.END, "links:\n  None\n\n")

    log_text.see(tk.END)


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
    log_text.delete("1.0", tk.END)  # Clear the previous log text
    log_text.yview_moveto(0)  # Ensure view starts from the top
    append_to_log("Fetching new token data...")
    background_search()


def start_process():
    fetch_button.config(state=tk.DISABLED)  # Disable the Fetch button while processing
    fetch_process()
    fetch_button.config(state=tk.NORMAL)  # Re-enable the Fetch button after processing


def main():
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Script interrupted by user (KeyboardInterrupt). Exiting gracefully...")
        sys.exit(0)


################################################################################
# MAIN UI SETUP
################################################################################

root = tk.Tk()
root.title("Web 3.0 Dexscreener Tokens")

# Set window size and position
root.geometry("950x700")
root.config(bg="#1f1f1f")

# Create a container frame with a sleek shadow effect and rounded corners
frame = tk.Frame(root, bg="#2b2b2b", bd=15, relief="solid", borderwidth=2, highlightthickness=0)
frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

# Add a top header label
header_label = tk.Label(frame, text="Prolif SOL Sniper v1", font=("Helvetica", 18, "bold"), fg="#1E90FF", bg="#2b2b2b")
header_label.pack(pady=20)

# Button Frame for controls
button_frame = tk.Frame(frame, bg="#2b2b2b")
button_frame.pack(pady=20)

fetch_button = tk.Button(button_frame, text="Fetch", width=15, height=2, command=start_process,
                         bg="#1E90FF", fg="white", font=("Arial", 12, "bold"), relief="raised", bd=2)
fetch_button.pack(side=tk.LEFT, padx=(0, 20))

# Create a ScrolledText widget with a modern dark theme
log_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, bg="#1e1e1e", fg="white", font=("Arial", 12),
                                     insertbackground="white", height=15, bd=0, highlightthickness=0)
log_text.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

# Configure text tags for bold
log_text.tag_config("bold_title", font=("Arial", 12, "bold", "underline"), foreground="#1E90FF")
log_text.tag_config("bold_label", font=("Arial", 12, "bold"), foreground="#66c2ff")
log_text.tag_config("bold_desc", font=("Arial", 12, "bold"))

# Create a Frame to hold the filter header and description text
filter_frame = tk.Frame(frame, bg="#2b2b2b")
filter_frame.pack(pady=(0, 20))

# Label to display the current filter settings
filter_label = tk.Label(filter_frame, text="Current Filters: Market Cap < 5M, Holders < 2000, Age < 2 hours",
                        font=("Arial", 12), fg="white", bg="#2b2b2b")
filter_label.pack()

# Small text for the recommended settings note
recommendation_label = tk.Label(filter_frame, text="Recommended Settings. Ability to change settings coming in v2.",
                                font=("Arial", 10), fg="grey", bg="#2b2b2b")
recommendation_label.pack(pady=(5, 0))

# Adjusting the button frame positioning to ensure it's below the filter frame
button_frame.pack(pady=20)

running = False

if __name__ == "__main__":
    main()
