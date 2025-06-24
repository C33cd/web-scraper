import os
import random
import time

import requests
from playwright.sync_api import sync_playwright, Error, Page, Browser, BrowserContext
import re


def navigate_to_search(page: Page)->Page:
    page.goto('https://egazette.gov.in/', wait_until='domcontentloaded', timeout=90000)
    # Click the OK button if it appears
    time.sleep(random.uniform(1,3))
    page.wait_for_selector("#ImgMessage_OK", timeout=5000)
    page.click("#ImgMessage_OK")
    # Wait for the G20 popup close button and click it
    page.wait_for_load_state('domcontentloaded')
    page.wait_for_selector("img.img-fluid", timeout=5000)
    page.click("img.img-fluid")
    time.sleep(random.uniform(1, 3))
    page.wait_for_load_state('domcontentloaded')
    # Click the 'Search' tab
    max_retries = 3;
    for attempt in range(max_retries):
        page.wait_for_selector("#sgzt", timeout=5000)
        page.click("#sgzt")
        if "This site can’t be reached" not in page.content() and "site can't be reached" not in page.content().lower():
            break  # Page loaded successfully
        print(f"Site can't be reached, retrying... ({attempt + 1}/{max_retries})")
        page.reload()
        time.sleep(2)
    else:
        raise Exception("Failed to load the page after several retries.")

    page.wait_for_load_state('domcontentloaded')
    # Click 'Search by Ministry':
    time.sleep(random.uniform(1,3))
    page.wait_for_selector("#btnMinistry", timeout=5000)
    page.click("#btnMinistry")
    time.sleep(random.uniform(1,10))
    return page

def scraper():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            accept_downloads=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page = navigate_to_search(page)
        # Continue here:


# Run the code
scraper()