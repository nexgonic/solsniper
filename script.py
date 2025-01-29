import sys
import webbrowser
import requests
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from io import BytesIO
import ttkbootstrap as ttkb

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

# Global variables for hyperlink handling
hyperlinks_map = {}
hyperlink_id = 0

# Global variable to store filtered tokens
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

        # Enable the "Show More" button if there are more tokens left
        if len(filtered_tokens) > 5:
            show_more_button.config(state=tk.NORMAL)

    else:
        print("No tokens found this round.")

    # Re-enable the fetch button after processing
    fetch_button.config(state=tk.NORMAL)


def refresh_token_list():
    """
    Refreshes the token list by calling the background search and updating the display.
    """
    fetch_process()


def fetch_process():
    print("Fetching new token data...")
    background_search()


def start_process():
    fetch_button.config(state=tk.DISABLED)  # Disable the Fetch button while processing
    fetch_process()


def show_more_tokens():
    """
    Displays the next batch of filtered tokens (after the first 5).
    """
    global tokens_displayed
    remaining_tokens = filtered_tokens[tokens_displayed:tokens_displayed + 5]

    for i, token in enumerate(remaining_tokens, start=tokens_displayed + 1):
        display_token(token, i)

    tokens_displayed += len(remaining_tokens)

    # Disable the "Show More" button if there are no more tokens to show
    if tokens_displayed >= len(filtered_tokens):
        show_more_button.config(state=tk.DISABLED)


################################################################################
# DISPLAYING TOKEN INFO
################################################################################

def display_token(token: dict, index: int):
    """
    Inserts token info into a card layout within the scrolledtext widget in the order:
      1) token name (bold)
      2) tokenAddress
      3) icon (image)
      4) links (clickable)
    """
    card_frame = ttkb.Frame(results_frame, bootstyle="dark", padding=20, borderwidth=2, relief="solid", width=700)
    card_frame.pack(pady=20, fill=tk.X, anchor="center")  # Ensure it fills the width of the window

    # Token name (bold)
    token_name_label = ttkb.Label(card_frame, text=f"Token #{index}: {token.get('tokenAddress', 'N/A')}",
                                  font=("Helvetica", 16, "bold"), foreground="lightblue", background="")
    token_name_label.pack(pady=(0, 15))

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
                img_tk = ImageTk.PhotoImage(img)

                # Display the image in the Tkinter window
                label_img = ttkb.Label(card_frame, image=img_tk)
                label_img.image = img_tk  # Keep a reference to the image
                label_img.pack(pady=(0, 15))
            else:
                print(f"Error loading icon: {icon_url} - Not a valid image")
        except Exception as e:
            print(f"Error loading icon: {e}")

    # Token Address
    token_address_label = ttkb.Label(card_frame, text=f"Address: {token.get('tokenAddress', 'N/A')}",
                                     font=("Helvetica", 12), foreground="lightgreen", background="")
    token_address_label.pack(pady=(0, 15))

    # URL as clickable link
    url_label = ttkb.Label(card_frame, text="URL:", font=("Helvetica", 12, "bold"), foreground="cyan", background="")
    url_label.pack(pady=(0, 5))
    if token["url"] and token["url"] != "N/A":
        add_hyperlink(token["url"], token["url"], parent=card_frame)
    else:
        no_url_label = ttkb.Label(card_frame, text="N/A", font=("Helvetica", 12), foreground="gray", background="")
        no_url_label.pack(pady=(0, 5))

    # Links section - clickable
    links_list = token.get("links", [])
    if links_list:
        links_label = ttkb.Label(card_frame, text="Links:", font=("Helvetica", 12, "bold"), foreground="magenta", background="")
        links_label.pack(pady=(0, 5))
        for link in links_list:
            add_hyperlink(link, link, parent=card_frame)
    else:
        no_links_label = ttkb.Label(card_frame, text="None", font=("Helvetica", 12), foreground="gray", background="")
        no_links_label.pack(pady=(0, 5))


################################################################################
# ADD HYPERLINK FUNCTION
################################################################################

def add_hyperlink(url: str, display_text: str, parent: ttkb.Frame) -> None:
    """
    Inserts 'display_text' as a clickable link in the given parent frame
    which, when clicked, opens 'url' in the default web browser.
    """
    global hyperlink_id

    tag_name = f"hyper-{hyperlink_id}"
    hyperlink_id += 1

    # Create a label with custom styling to look like a link
    link_label = ttkb.Label(parent, text=display_text, font=("Helvetica", 12, "underline"), foreground="#1E90FF", background="")
    link_label.pack(pady=(0, 5))

    # Store the URL for the link
    hyperlinks_map[tag_name] = url

    def click_callback(event, tag=tag_name):
        link_url = hyperlinks_map[tag]
        webbrowser.open(link_url)

    # Bind the click event to the label
    link_label.bind("<Button-1>", click_callback)


################################################################################
# MAIN UI SETUP
################################################################################

root = ttkb.Window(themename="darkly")  # Set dark theme using ttkbootstrap

root.title("Web 3.0 Dexscreener Tokens")
root.geometry("950x1250")  # Change window size to 950x1250

# Create a container frame with a sleek shadow effect and rounded corners
frame = ttkb.Frame(root, bootstyle="dark", padding=20)
frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

# Fetch the logo image from URL and resize it to 250px width
logo_url = "https://nextgenspeed.com/wa/uilogo.png"
response = requests.get(logo_url)
logo_image = Image.open(BytesIO(response.content))

# Resize the image to a width of 250px while maintaining the aspect ratio
width = 250
height = int((width / logo_image.width) * logo_image.height)
logo_image = logo_image.resize((width, height), Image.Resampling.LANCZOS)

# Convert the image to a Tkinter-compatible format
logo_tk = ImageTk.PhotoImage(logo_image)

# Add the logo image in the header and center it with no background or border
header_logo_label = ttkb.Label(frame, image=logo_tk, relief="flat", borderwidth=0)  # No border or relief
header_logo_label.image = logo_tk  # Keep a reference to the image
header_logo_label.pack(pady=30)  # Adjust the padding as needed

# Header Section (added)
header_frame = ttkb.Frame(frame, bootstyle="dark")
header_frame.pack(pady=20)

# Title Label: Proliv Token Tracker
title_label = ttkb.Label(header_frame, text="Proliv Token Tracker", font=("Helvetica", 20, "bold"), foreground="white", background="")
title_label.pack()

# Slogan Label: Ai Tracked Newest SOL/ETH Pairs
slogan_label = ttkb.Label(header_frame, text="Ai Tracked Newest SOL/ETH Pairs", font=("Helvetica", 12), foreground="white", background="")
slogan_label.pack()

# Button Frame for controls
button_frame = ttkb.Frame(frame, bootstyle="dark")
button_frame.pack(pady=20)

# Use grid layout to space buttons evenly
button_frame.grid_columnconfigure(0, weight=1)
button_frame.grid_columnconfigure(1, weight=1)
button_frame.grid_columnconfigure(2, weight=1)

# Updated button styles with neon colors
fetch_button = ttkb.Button(button_frame, text="Fetch Tokens", command=start_process, bootstyle="primary",
                           padding=(12, 5), width=20, style="success")  # Neon blue for "Fetch Tokens"
fetch_button.grid(row=0, column=0, padx=10)

show_more_button = ttkb.Button(button_frame, text="Show More", command=show_more_tokens, bootstyle="info",
                               padding=(12, 5), width=20, style="info")  # Neon purple for "Show More"
show_more_button.grid(row=0, column=1, padx=10)
show_more_button.config(state=tk.DISABLED)

# Change Refresh button to purple/pink color
refresh_button = ttkb.Button(button_frame, text="Refresh", command=refresh_token_list, bootstyle="secondary",
                             padding=(12, 5), width=20, style="")  # Purple/Pink for "Refresh"
refresh_button.grid(row=0, column=2, padx=10)

# Create a canvas to hold the scrollable frame for token results
canvas = tk.Canvas(frame)
scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
scrollable_frame = ttkb.Frame(canvas)

# Configure the scrollbar and canvas
canvas.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")
canvas.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

# Make the results frame scrollable
scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

# Bind the mouse wheel scroll to the canvas
def on_canvas_scroll(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

# Bind the mouse wheel event to the entire window
canvas.bind_all("<MouseWheel>", on_canvas_scroll)

results_frame = scrollable_frame  # This frame will hold the tokens

# Footer with copyright and social links
footer_frame = ttkb.Frame(root, bootstyle="dark", padding=10)
footer_frame.pack(fill=tk.X, side=tk.BOTTOM)

# Copyright text
copyright_label = ttkb.Label(footer_frame, text="© Nexgonic", font=("Helvetica", 12), bootstyle="light", background="")
copyright_label.pack(pady=(5, 0))

# Social Media Links (Twitter (X), Telegram, Website)
social_frame = ttkb.Frame(footer_frame)
social_frame.pack(pady=(5, 0))

# Twitter (X), Telegram, Website Icons
twitter_icon = ttkb.Label(social_frame, text="🐦", font=("Helvetica", 16, "bold"), bootstyle="light", background="")
twitter_icon.pack(side=tk.LEFT, padx=10)
telegram_icon = ttkb.Label(social_frame, text="📱", font=("Helvetica", 16, "bold"), bootstyle="light", background="")
telegram_icon.pack(side=tk.LEFT, padx=10)
website_icon = ttkb.Label(social_frame, text="🌐", font=("Helvetica", 16, "bold"), bootstyle="light", background="")
website_icon.pack(side=tk.LEFT, padx=10)

# Links
twitter_icon.bind("<Button-1>", lambda e: webbrowser.open("https://x.com/nexgonic"))
telegram_icon.bind("<Button-1>", lambda e: webbrowser.open("https://telegram.com/nexgonicai"))
website_icon.bind("<Button-1>", lambda e: webbrowser.open("https://nexgonic.com"))

# Create a frame to center the whitelist banner
whitelist_frame = ttkb.Frame(footer_frame)
whitelist_frame.pack(fill=tk.X, pady=(5, 0))

# Whitelist Sign-Up Banner centered in the frame
whitelist_banner = ttkb.Label(whitelist_frame, text="White List Sign Up For Upcoming Releases", font=("Helvetica", 12), bootstyle="info", background="")
whitelist_banner.pack(pady=(5, 0), ipadx=20, ipady=5, anchor="center")


running = False


# Start the Tkinter event loop
def main():
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Script interrupted by user (KeyboardInterrupt). Exiting gracefully...")
        sys.exit(0)


if __name__ == "__main__":
    main()
