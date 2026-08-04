from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service
import time
from colorama import Fore, Style
import re  # For regex matching
import discord  # For Discord bot
from discord import ui  # For Discord UI components
import asyncio  # For async operations
from datetime import datetime  # For timestamps
import os
import random  # For random delays and user agent rotation
from dotenv import load_dotenv
load_dotenv()

# 🔹 Website URL
URL = "https://trouverunlogement.lescrous.fr/"

# 🔹 City name from environment variable or user input
CITY_NAME = os.getenv("CITY_NAME") or input("Enter the city you want to search for: ")

# 🔹 Correct locators
SEARCH_BOX_SELECTOR = "input[class*='PlaceAutocomplete__input']"  # Search box
DROPDOWN_SELECTOR = "ul[role='listbox'] li"  # Dropdown options
SEARCH_BUTTON_SELECTOR = "button.fr-btn.svelte-w11odb"  # Search button
RESULTS_TITLE_SELECTOR = "h2.SearchResults-mobile.svelte-8mr8g"  # Results title

# 🔹 House listing locators
HOUSE_ITEM_SELECTOR = "li.fr-col-12.fr-col-sm-6.fr-col-md-4.svelte-11sc5my"  # House items
HOUSE_NAME_SELECTOR = "a[href^='/tools']"  # House name
HOUSE_ADDRESS_SELECTOR = "p.fr-card__desc"  # House address
HOUSE_SURFACE_SELECTOR = ".//p[contains(@class, 'fr-card__detail')]"  # House surface (relative XPath)
HOUSE_PRICE_SELECTOR = ".//p[contains(@class, 'fr-badge')]"  # House price (relative XPath)
HOUSE_IMAGE_SELECTOR = "img.fr-responsive-img"  # House image

# 🔹 Set up ChromeOptions for headless mode (anti-detection)
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")  # New headless mode (less detectable)
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")

# 🔹 Anti-detection options
options.add_argument("--disable-extensions")
options.add_argument("--disable-infobars")
options.add_argument("--disable-popup-blocking")
options.add_argument("--lang=fr-FR")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

# 🔹 Rotate user agents to look like a real browser
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

# 🔹 Auto-detect Chromium binary (for VPS/Raspberry Pi compatibility)
import shutil
chromium_path = shutil.which("chromium-browser") or shutil.which("chromium")
if chromium_path:
    options.binary_location = chromium_path

# 🔹 Discord Bot Configuration
DISCORD_TOKEN =  os.getenv("DISCORD_TOKEN")  # Replace with your bot token
CHANNEL_ID = 1333027105591660564  # Replace with your Discord channel ID

# Initialize Discord bot
intents = discord.Intents.default()
client = discord.Client(intents=intents)
def search_city(city):
    """Search for houses in the specified city and return results."""
    # Auto-detect chromedriver path
    chromedriver_path = shutil.which("chromedriver")
    service = Service(chromedriver_path) if chromedriver_path else Service()

    # Set a random user agent for each session
    options.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")
    driver = webdriver.Chrome(service=service, options=options)

    # 🔹 Inject stealth scripts to hide automation fingerprints
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['fr-FR', 'fr', 'en-US', 'en'] });
            window.chrome = { runtime: {} };
        """
    })

    try:
        print(Fore.YELLOW + "🌐 Opening the website..." + Style.RESET_ALL)
        driver.get(URL)
        time.sleep(random.uniform(1, 3))  # Random delay to mimic human behavior
        
        # Wait for search box and type city name
        search_box = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, SEARCH_BOX_SELECTOR))
        )
        search_box.clear()
        # Type city name character by character (human-like)
        for char in city:
            search_box.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
        time.sleep(random.uniform(2, 4))  # Allow dropdown to appear

        # Select city from dropdown
        dropdown_options = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, DROPDOWN_SELECTOR))
        )
        for option in dropdown_options:
            if city.lower() in option.text.lower():
                option.click()
                break
        time.sleep(random.uniform(1, 3))

        # Click search button
        search_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, SEARCH_BUTTON_SELECTOR))
        )
        time.sleep(random.uniform(0.5, 1.5))  # Small pause before clicking
        search_button.click()

        # Wait for search results to load
        print(Fore.YELLOW + "⏳ Waiting for search results..." + Style.RESET_ALL)
        try:
            # Wait for the results title to appear
            results_title = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, RESULTS_TITLE_SELECTOR))
            )
            title_text = results_title.text.strip()
            # Check if no houses were found
            if title_text == "Aucun logement trouvé":
                print(Fore.RED + f"🏠 I found 0 houses." + Style.RESET_ALL)
                return []  # No listings found

            print(Fore.GREEN + "✅ Search results loaded!" + Style.RESET_ALL)

            # Wait for the house listings to load
            print(Fore.YELLOW + "🔍 Waiting for house listings..." + Style.RESET_ALL)
            listings_elements = WebDriverWait(driver, 30).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, HOUSE_ITEM_SELECTOR))
            )
            print(Fore.GREEN + f"✅ Found {len(listings_elements)} house listings!" + Style.RESET_ALL)

            # Extract and collect house details
            houses = []
            for house in listings_elements:
                try:
                    # Extract house name and link
                    house_link_element = house.find_element(By.CSS_SELECTOR, HOUSE_NAME_SELECTOR)
                    house_name = house_link_element.text.strip()
                    house_href = house_link_element.get_attribute("href")
                    # Extract house address
                    house_address = house.find_element(By.CSS_SELECTOR, HOUSE_ADDRESS_SELECTOR).text.strip()
                    # Extract house surface
                    surface = house.find_element(By.XPATH, HOUSE_SURFACE_SELECTOR).text.strip()
                    range_match = re.search(r"(\d+(?:,\d+)?)\s*à\s*(\d+(?:,\d+)?)\s*m²", surface)
                    single_match = re.search(r"(\d+(?:,\d+)?)\s*m²", surface)
                    if range_match:
                        low = range_match.group(1).replace(",", ".")
                        high = range_match.group(2).replace(",", ".")
                        surface_formatted = f"{low}-{high}"  # e.g. "16-18"
                    elif single_match:
                        surface_formatted = single_match.group(1).replace(",", ".")
                    else:
                        surface_formatted = "N/A"  # Handle missing or unexpected surface format

                    # Extract house price
                    price = house.find_element(By.XPATH, HOUSE_PRICE_SELECTOR).text.strip()
                    price_match = re.search(r"(\d+,\d+)\s*€", price)
                    if price_match:
                        price_formatted = price_match.group(1).replace(",", ".")  # Format price
                    else:
                        price_match = re.search(r"(\d+)\s*€", price)
                        price_formatted = price_match.group(1) if price_match else "N/A"
                    
                    # Print house details
                    print(Fore.GREEN + f"🏠 House Name: {house_name}" + Style.RESET_ALL)
                    print(Fore.BLUE + f"📍 Address: {house_address}" + Style.RESET_ALL)
                    print(Fore.CYAN + f"📐 Surface: {surface_formatted} m² (Raw: {surface})" + Style.RESET_ALL)
                    print(Fore.MAGENTA + f"💰 Price: {price_formatted} € (Raw: {price})" + Style.RESET_ALL)
                    print("-" * 50)

                    # Extract house image
                    try:
                        house_image = house.find_element(By.CSS_SELECTOR, HOUSE_IMAGE_SELECTOR).get_attribute("src")
                    except NoSuchElementException:
                        house_image = None

                    houses.append({
                        "name": house_name,
                        "address": house_address,
                        "surface": surface_formatted,
                        "price": price_formatted,
                        "link": house_href if house_href else URL,
                        "image": house_image,
                    })
                except NoSuchElementException:
                    print(Fore.RED + "❌ Could not extract house details." + Style.RESET_ALL)
                    continue

            return houses
        except TimeoutException:
            print(Fore.RED + "❌ House listings did not load within the expected time." + Style.RESET_ALL)
            print(Fore.RED + f"🏠 I found 0 houses." + Style.RESET_ALL)
            return []  # No listings found

    except (NoSuchElementException, TimeoutException) as e:
        print(Fore.RED + f"❌ An error occurred: {e}" + Style.RESET_ALL)
        print(Fore.RED + f"🏠 I found 0 houses." + Style.RESET_ALL)
        return []
    finally:
        # Close the browser after each iteration
        driver.quit()

# Main loop to retry every 10 minutes

# Discord bot event
@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    channel = client.get_channel(CHANNEL_ID)

    while True:
        houses = search_city(CITY_NAME)
        if houses:
            print(f"� Found {len(houses)} house(s)!")

            # Send a summary notification
            await channel.send(f'@here 🏠 **{len(houses)} logement(s) trouvé(s) à {CITY_NAME} !**')

            # Send a beautiful embed for each house
            for house in houses:
                embed = discord.Embed(
                    title=f"🏠 {house['name']}",
                    description=f"Un logement est disponible à **{CITY_NAME}** !",
                    color=discord.Color.green(),
                    timestamp=datetime.now(),
                )
                embed.add_field(name="📍 Adresse", value=house["address"], inline=False)
                embed.add_field(name="💰 Loyer", value=f"{house['price']} €/mois", inline=True)
                embed.add_field(name="📐 Surface", value=f"{house['surface']} m²", inline=True)
                if house.get("image"):
                    embed.set_image(url=house["image"])
                embed.set_footer(text="CROUS Housing Scraper • Trouvé maintenant")

                # Create a button that links to the listing
                view = discord.ui.View()
                view.add_item(
                    discord.ui.Button(
                        label="🔗 Voir sur le site",
                        style=discord.ButtonStyle.link,
                        url=house["link"],
                    )
                )

                await channel.send(embed=embed, view=view)
        else:
            print(Fore.BLUE + "No houses found. Checking again in 5 minutes ..." + Style.RESET_ALL)

        # Random wait between 4-6 minutes (less predictable)
        wait_time = random.randint(240, 360)
        print(f"⏳ Next check in {wait_time // 60} min {wait_time % 60} sec...")
        await asyncio.sleep(wait_time)
# Run the bot
client.run(DISCORD_TOKEN)