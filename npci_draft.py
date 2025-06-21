import os
import requests
from playwright.sync_api import sync_playwright, Error
import re
from urllib.parse import urlparse

# Clean up filenames/folder names so Windows doesn't get mad
def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*\n\r\t]', '_', name).strip()

# Download a PDF file and save it safely in the right folder
def download_as_pdf(pdf_url: str, download_dir: str, file_name: str = None, dedupe_counter=0):
    os.makedirs(download_dir, exist_ok=True)

    # Fallback if no name provided
    if not file_name:
        file_name = os.path.basename(pdf_url.split("?")[0])

    file_name = sanitize_filename(file_name.strip())
    if not file_name:
        file_name = "document"

    if not file_name.lower().endswith(".pdf"):
        file_name += ".pdf"

    # Handle duplicate names by adding _1, _2, etc.
    base_name, ext = os.path.splitext(file_name)
    final_name = f"{base_name}_{dedupe_counter}{ext}" if dedupe_counter > 0 else file_name
    save_path = os.path.join(download_dir, final_name)

    try:
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(response.content)
        print(f"✅ Downloaded: {save_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to download {pdf_url}: {e}")
        return False

# Extract folder-friendly section name like "upi" or "nfs"
def extract_section_name(url):
    parsed = urlparse(url)
    parts = parsed.path.strip('/').split('/')
    return sanitize_filename(parts[-2] if len(parts) >= 2 else parts[-1])

# The boss function that does everything
def npci_scraper(user_agent='', year=''):
    npci_main_link = 'https://www.npci.org.in/'

    with sync_playwright() as p:
        print("🚀 Launching browser and opening NPCI...")
        browser = p.chromium.launch(headless=False)  # Set to True to run in background
        context = browser.new_context(
            accept_downloads=True,
            user_agent=user_agent
        )
        page = context.new_page()

        # Step 1: Go to NPCI homepage and collect circular links
        response = page.goto(npci_main_link, wait_until="domcontentloaded", timeout=90000)
        if response and response.status != 200:
            print(f"⚠️ Failed to load homepage: {response.status}")
            return

        l1 = page.query_selector_all("a[aria-label='Circulars']")
        circular_links = [l.get_attribute('href') for l in l1 if l.get_attribute('href')]
        
        
        browser.close()

        # Step 2: Visit each circular page and download PDFs
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(user_agent=user_agent)
        page = context.new_page()

        for link in circular_links:
            if not link.startswith("http"):
                link = npci_main_link.rstrip('/') + '/' + link.lstrip('/')
            section_name = extract_section_name(link)
            save_folder = os.path.join("circulars", section_name)

            print(f"\n📂 Visiting: {link}")
            print(f"📁 Will save PDFs to: {save_folder}")

            try:
                response = page.goto(link, wait_until="domcontentloaded", timeout=60000)
                if response and response.status != 200:
                    print(f"⚠️ Failed to load {link}: {response.status}")
                    continue

                pdf_anchors = [
                    a for a in page.query_selector_all("a[href$='.pdf']")
                    if 'download' in (a.inner_text() or '').lower()
                ]
                seen_names = set()

                for i, anchor in enumerate(pdf_anchors):
                    pdf_url = anchor.get_attribute("href")
                    link_text = anchor.inner_text().strip() or "document"

                    if not pdf_url:
                        continue
                    if not pdf_url.startswith("http"):
                        pdf_url = npci_main_link.rstrip('/') + '/' + pdf_url.lstrip('/')

                    # Clean name and deduplicate if needed
                    clean_name = sanitize_filename(link_text)
                    if not clean_name:
                        clean_name = "document"

                    original_name = clean_name
                    dedupe_count = 1
                    while clean_name in seen_names:
                        clean_name = f"{original_name}_{dedupe_count}"
                        dedupe_count += 1

                    seen_names.add(clean_name)
                    download_as_pdf(pdf_url, save_folder, clean_name)

            except Error as e:
                print(f"❌ Error visiting {link}: {e}")

        browser.close()

# 🎬 Let's go!
npci_scraper()
