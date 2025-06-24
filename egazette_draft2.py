import os
import random
import time
os.makedirs('downloads', exist_ok=True)
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
    # max_retries = 3;
    # for attempt in range(max_retries):
    page.wait_for_selector("#sgzt", timeout=5000)
    page.click("#sgzt")
    page.wait_for_load_state('domcontentloaded')
    if "This site can’t be reached" not in page.content() and "site can't be reached" not in page.content().lower():
        pass  # Page loaded successfully
    else:
        # print(f"Site can't be reached, retrying... ({attempt + 1}/{max_retries})")
        page.reload()
        # page.wait_for_selector("#sgzt", timeout=5000)
        # page.click("#sgzt")
        time.sleep(2)
    # else:
    #     raise Exception("Failed to load the page after several retries.")

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
        # After the form loads:
        ministry_dropdown = page.locator("select#ddlMinistry").first
        ministry_dropdown.click()
        # page.evaluate("el => el.scrollTop = el.scrollHeight", ministry_dropdown)
        ministry_dropdown.wait_for(state="visible")
        # Select SEBI
        ministry_dropdown.select_option("21")
        print('Successfully selected SEBI')
        # print('Successfully selected SEBI')

        # Click the "Date Wise" radio button
        page.click('input#rdb_Option_1')
        print("Selected Date Wise option")

        # Fill the 'From' and 'To' date fields
        # page.fill('input#fromdt', '01-Jan-2020')
        # page.fill('input#todt', '24-Jun-2025')
        # print("Filled date range")
        # Fill in the date range
        page.fill('input#txtDateFrom', '01-Jan-2020')
        page.fill('input#txtDateTo', '24-Jun-2025')
        print("Dates filled")

        # Click somewhere neutral to close calendar
        page.click("td[align='center']")
        time.sleep(3)

        # Click the Submit button
        page.click('input#ImgSubmitDetails')
        print("Submit clicked")

        # Download Standard Report
        with page.expect_download() as download_info:
            page.click('input#imgPrintS')
        download = download_info.value
        download.save_as('downloads/standard report.pdf')
        print("Standard Report downloaded")


        time.sleep(10)


# Run the code
scraper()
