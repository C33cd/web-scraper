import os
import random
import time

import playwright_stealth
import requests
from playwright.sync_api import sync_playwright, Error, Page
import re

from playwright_stealth.stealth import Stealth


def sanitize_filename(name):
    # Replace invalid Windows filename characters with underscore
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def download_as_pdf(pdf_url: str, download_dir: str):
    # Pass the PDF URL as pdf_url and the directory where you want to store file as download_dir
    download_dir = sanitize_filename(download_dir)
    os.makedirs(download_dir, exist_ok=True)
    filename = os.path.basename(pdf_url.split("?")[0])
    save_path = os.path.join(download_dir, sanitize_filename(filename))
    response = requests.get(pdf_url)
    with open(save_path, "wb") as f:
        f.write(response.content)
    print(f"Downloaded to: {save_path}")


def mca_scraper(year='-1'):
    # Resources:
    mca_main_link = 'https://www.mca.gov.in/content/mca/global/en/acts-rules/ebooks/circulars.html'
    d_dir = 'MCA_Circulars'
    os.makedirs(d_dir, exist_ok=True)
    s1 = Stealth()
    # print(type(Stealth))
    # return

    # Collect documents:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            accept_downloads=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
        )
        page = context.new_page()
        s1.apply_stealth_sync(page)
        """
        response = page.goto('https://www.mca.gov.in/content/mca/global/en/home.html', wait_until="domcontentloaded", timeout=90000)
        if response and response.status != 200:
            print(f"Failed to load homepage: {response.status}")
            return
        time.sleep(3)
        # close the popup
        page.click('button#btnClosePopup')
        # Click Acts and Rules
        page.click("a:has-text('Acts & Rules'), button:has-text('Acts & Rules')")
        page.wait_for_load_state('domcontentloaded', timeout=90000)
        time.sleep(5)
        page.click("a:has-text('Circulars'), button:has-text('Acts & Rules')")
        time.sleep(random.uniform(1,5))
        """

        response = page.goto(mca_main_link, wait_until="domcontentloaded", timeout=90000)
        if response and response.status != 200:
            print(f"Failed to load {mca_main_link}: {response.status}")
            return
        # Select 'All' in dropdown box to show all results in one page
        page.wait_for_selector('select[name="notificationCircularTable_length"] option[value="-1"]')
        page.select_option('select[name="notificationCircularTable_length"]', value='-1')
        # Select Years in dropdown box
        if year != '-1' and int(year) < 1999:
            year = 1999
        page.wait_for_selector('#yearsBtn')
        page.select_option('#yearsBtn', value=year)
        # Add functionality of acts if necessary
        # Click 'Go' button to apply filters
        page.wait_for_selector('#clickGo:enabled')
        page.click('#clickGo')
        # Get links
        links = page.evaluate("""
        () => {
            // DataTables stores its instance on the table element
            let table = $('#notificationCircularTable').DataTable();
            return table.rows().data().toArray();
        }
        """)
        print(links)
        # Write HTML to file (for debugging)
        html_text = page.content()
        with open('mca_html', 'w', encoding='utf-8') as f:
            f.write(html_text)
            f.close()
        # links = page.locator()
        page.close()
        context.close()
        browser.close()


mca_scraper()