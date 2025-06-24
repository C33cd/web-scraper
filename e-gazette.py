import os
import time

import requests
from playwright.sync_api import sync_playwright, Error, Page, Browser, BrowserContext
import re


def navigate_to_search(page: Page)->Page:
    page.goto('https://egazette.gov.in/', wait_until='domcontentloaded', timeout=90000)
    # Click the OK button if it appears
    time.sleep(1)
    page.wait_for_selector("#ImgMessage_OK", timeout=5000)
    page.click("#ImgMessage_OK")
    # Wait for the G20 popup close button and click it
    page.wait_for_selector("img.img-fluid", timeout=5000)
    page.click("img.img-fluid")
    # Click the 'Search' tab
    page.wait_for_selector("#sgzt", timeout=5000)
    page.click("#sgzt")    # Click 'Search by Ministry':
    page.wait_for_selector("#btnMinistry", timeout=5000)
    page.click("#btnMinistry")
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