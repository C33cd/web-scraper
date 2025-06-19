import os
import requests
from playwright.sync_api import sync_playwright, Error, Page
import re


def sanitize_filename(name):
    # Replace invalid Windows filename characters with underscore
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def download_as_pdf(pdf_url: str, download_dir: str):
    # Pass the PDF URL as pdf_url and the directpry where you want to store file as download_dir
    os.makedirs(download_dir, exist_ok=True)
    filename = os.path.basename(pdf_url.split("?")[0])
    save_path = os.path.join(download_dir, filename)
    response = requests.get(pdf_url)
    with open(save_path, "wb") as f:
        f.write(response.content)
    print(f"Downloaded to: {save_path}")


def npci_scraper(user_agent=''):
    # Make this the default user agent if necessary:
    # user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
    # Resources:
    npci_main_link = 'https://www.npci.org.in/'

    # Collect links for all the circulars webpages
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            accept_downloads=True,
            user_agent=user_agent
        )
        page = context.new_page()
        response = page.goto(npci_main_link, wait_until="domcontentloaded", timeout=90000)
        if response and response.status != 200:
            print(f"Failed to load {npci_main_link}: {response.status}")
            return
        l1 = page.query_selector_all("a[aria-label='Circulars']")
        circular_links = [l.get_attribute('href') for l in l1]
        browser.close()


    # the links to the circular's webpages are stored in circular_links

    #Continue here:




