# This is a sample Python script.
import json
import os
import random
import time
from multiprocessing import Pool

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Error, Page
from playwright_stealth import stealth_sync
import re

"""
def get_driver(headless=True):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=chrome_options)
"""


def process_fund_wrapper(args):
    return process_fund(*args)


def download_as_pdf(pdf_url: str, download_dir: str):
    filename = os.path.basename(pdf_url.split("?")[0])
    save_path = os.path.join(download_dir, filename)
    response = requests.get(pdf_url)
    with open(save_path, "wb") as f:
        f.write(response.content)
    print(f"Downloaded to: {save_path}")


def captcha_check(page: Page):
    while "captcha" in page.content().lower():
        print("Captcha detected. Please solve it in the browser window. Checking again in 60 seconds...")
        page.wait_for_timeout(60 * 1000)  # Wait 60 seconds (milliseconds)
    page.wait_for_timeout(3000)  # wait 3 seconds


def sanitize_filename(name):
    # Replace invalid Windows filename characters with underscore
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def process_fund(link, name, download_dir, user_agent):
    # Sanitise name
    safe_name = sanitize_filename(name)
    # make name directory
    os.makedirs(os.path.join(download_dir, safe_name), exist_ok=True)
    download_dir = os.path.join(download_dir, safe_name)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                accept_downloads=True,
                user_agent=user_agent
            )
            page = context.new_page()
            try:
                # prevent window from taking focus
                page.evaluate("window.blur();")
                response = page.goto(link, wait_until="domcontentloaded", timeout=90000)
                if response and response.status != 200:
                    print(f"Failed to load {link}: {response.status}")
                    return
            except Exception as e:
                print(f"Error visiting {link}: {e}")
                return

            page.wait_for_load_state('domcontentloaded', timeout=90000)
            # Captcha check
            captcha_check(page)
            docs_section_id = 'pd_documents'
            portfolio_section_id = 'pd_portfolio'
            performance_section_id = 'pd_performance'

            # Get the <head> HTML (with CSS/JS)
            head_html = page.evaluate("() => document.head.outerHTML")

            # Data extraction
            portfolio_section = page.locator(f'section#{portfolio_section_id}')
            performance_section = page.locator(f'section#{performance_section_id}')
            portfolio_stocks_html = ""
            performance_html = ""

            stocks_link = portfolio_section.locator("a#stk")
            if stocks_link.count() > 0 and stocks_link.is_visible():
                stocks_link.click()

            detail_link = portfolio_section.locator("a:has-text('Detail Holdings'):visible")
            if detail_link.count() > 0 and detail_link.is_visible():
                detail_link.click()

            if portfolio_section.count() != 0:
                portfolio_stocks_html = portfolio_section.evaluate("el => el.outerHTML")
            if performance_section.count() != 0:
                performance_html = performance_section.evaluate("el => el.outerHTML")

            final_html = f"""
            <html>
            {head_html}
            <body>
            <b>Portfolio</b>
            <br>
            {portfolio_stocks_html}
            <style>
            /* Disable scroll and JS effects for #pd_portfolio */
            #pd_portfolio, #pd_portfolio * {{
                max-height: none !important;
                overflow: visible !important;
                pointer-events: none;
            }}
            </style>            
            <br>
            <br>
            <b>Performance of stocks:</b>
            <br>
            {performance_html}
            </body>
            </html>
            """

            # Save HTML to file
            with open(os.path.join(download_dir, f"pdf_final_{name}.html"), 'w', encoding='utf-8') as f:
                f.write(final_html)

            # Save as PDF
            new_page = context.new_page()
            new_page.set_content(final_html)
            new_page.pdf(
                path=os.path.join(download_dir, safe_name + ".pdf"),
                format="A4",
                print_background=True
            )
            print('PDF saved at: ' + os.path.join(download_dir, safe_name + ".pdf"))
            new_page.close()

            # Download docs
            section = page.locator(f"section#{docs_section_id}")
            download_links = section.locator("a:has-text('Download'):visible")
            count = download_links.count()
            for i in range(count):
                d_link = download_links.nth(i)
                with context.expect_page() as new_page_info:
                    d_link.click(force=True)
                    time.sleep(0.2)
                new_tab = new_page_info.value
                new_tab.wait_for_load_state("domcontentloaded")
                pdf_url = new_tab.url
                print(f"PDF opened at URL: {pdf_url}")
                download_as_pdf(pdf_url, download_dir)
                new_tab.close()

            page.close()
            context.close()
            browser.close()
    except Exception as e:
        print(f"Exception in process_fund for {name}: {e}")


def kotak_scraper(reuse: bool):
    first_time = time.time()
    html_text = ""
    if not reuse:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.goto("https://www.kotakmf.com/mutual-funds")
            captcha_check(page)
            while True:
                try:
                    load_more = page.locator('a.loadMoreTextSize.loadMoreTextMob')
                    if load_more.count() > 0 and load_more.is_visible():
                        print("Clicking Load More...")
                        load_more.click()
                        page.wait_for_timeout(1500)  # Wait for new items to load
                    else:
                        print("No more Load More button found.")
                        break
                except Exception as e:
                    print(f"Error clicking Load More: {e}")
                    break
            html_text = page.content()
            with open("kotak_source.html", 'w', encoding='utf-8') as f:
                f.write(html_text)
            page.close()
            context.close()
            browser.close()


    # Load cached HTML to avoid repeated captcha
    with open("kotak_source.html", 'r', encoding='utf-8') as f:
        html_text = f.read()

    soup = BeautifulSoup(html_text, 'lxml')

    jobs = soup.find_all('a', class_='fundName')
    links = []
    names = []
    for job in jobs:
        links.append(job.get('href'))
        names.append(job.get_text(strip=True))

    # Remove irrelevant links/names
    links = links[:len(links)//2]
    names = names[:len(names)//2]

    download_dir = "Downloads"
    os.makedirs(download_dir, exist_ok=True)
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"

    # Use multiprocessing for parallelism
    max_workers = 3  # Adjust as needed
    args_list = [(link, name, download_dir, user_agent) for link, name in zip(links, names)]
    with Pool(processes=max_workers) as pool:
        pool.map(process_fund_wrapper, args_list)

    last_time = time.time()
    print('Successfully executed')
    print('Time taken: ' + str(last_time - first_time) + ' seconds')


def nippon_scraper(reuse_previous_version: bool):
    # Evaluation metrics:
    # Time taken to grab all links: 3 min
    first_time = time.time()
    fund_type_links = ['https://mf.nipponindiaim.com/our-products/by-asset-class/equity-funds',
                       'https://mf.nipponindiaim.com/our-products/by-asset-class/debt-funds',
                       'https://mf.nipponindiaim.com/our-products/by-asset-class/index-funds',
                       'https://mf.nipponindiaim.com/our-products/by-asset-class/hybrid-funds',
                       'https://mf.nipponindiaim.com/our-products/by-asset-class/gold-funds',
                       'https://mf.nipponindiaim.com/our-products/by-asset-class/liquid-funds']
    links = []
    names = []

    if not reuse_previous_version:
        with sync_playwright() as p:
            # Try with headless browser
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
                accept_downloads=False)
            page = context.new_page()
            stealth_sync(page)
            for fund_link in fund_type_links:
                for attempt in range(3):
                    try:
                        page.goto(fund_link)
                        break
                    except Error as e:
                        print(f'Got error: {e}. Trying again...')
                page.wait_for_load_state('domcontentloaded')
                chkr = page.locator('a[style*="text-decoration: underline"]').count()
                # 6 in card style + 9 in list style = 15
                num_valid_links = 6 if chkr > 12 else chkr // 2
                while True:
                    try:
                        captcha_check(page)
                        l1 = page.locator('a[style*="text-decoration: underline"]')
                        for i in range(num_valid_links):
                            names.append(l1.nth(i).inner_text())
                            links.append(l1.nth(i).get_attribute('href'))
                        next_btn = page.locator('a[title*="Next to Page"]')
                        if next_btn.count() == 0 or next_btn.count() == 1:
                            print("No 'Next' button found.")
                            break
                        print(next_btn.first.inner_text() + " " + next_btn.first.get_attribute('title'))
                        next_btn.first.scroll_into_view_if_needed()
                        if next_btn.first.is_visible():
                            next_btn.first.click()
                            page.wait_for_load_state("domcontentloaded")
                        else:
                            break
                        # wait - to mimic human behaviour
                        time.sleep(random.uniform(1, 3))
                    except Error as e:
                        print(f'Error occurred: {e} ')
                        break

                # wait - to mimic human behaviour
                time.sleep(random.uniform(1, 3))

        # write links and names to a file (caching)
        with open("links.txt", 'w', encoding='utf-8') as f:
            for link in links:
                f.write(link+"\n")
        with open("names.txt", 'w', encoding='utf-8') as f:
            for name in names:
                f.write(name+"\n")
    else:
        with open("links.txt", 'r', encoding='utf-8') as f:
            links = [l.rstrip('\n') for l in f.readlines()]
        with open("names.txt", 'r', encoding='utf-8') as f:
            names = [n.rstrip('\n') for n in f.readlines()]

    download_dir = 'Downloads'
    os.makedirs(download_dir, exist_ok=True)
    section_selector = "div.accordDivDetail"  # Replace with your section's selector

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
            accept_downloads=False)
        page = context.new_page()
        # sector_allocation_url = "https://mf.nipponindiaim.com/_vti_bin/RMF.Services/MobileAppService.svc/GetSectorAllocationData?schemecode="
        # top_10_holdings_url = "https://mf.nipponindiaim.com/_vti_bin/RMF.Services/MobileAppService.svc/GetTopTenholding?schemecode="
        for link, name in zip(links, names):
            # link = 'https://mf.nipponindiaim.com/FundsAndPerformance/Pages/NipponIndia-us-equity-opportunities-fund.aspx'
            # name = 'Nippon India US Equity Opportunities Fund'
            safe_name = sanitize_filename(name)
            save_dir = os.path.join(download_dir, safe_name)
            os.makedirs(save_dir, exist_ok=True)
            try:
                # prevent window from taking focus
                # page.evaluate("window.blur();")
                response = page.goto(link, wait_until="domcontentloaded", timeout=90000)
                if response and response.status != 200:
                    print(f"Failed to load {link}: {response.status}")
                    return
            except Exception as e:
                print(f"Error visiting {link}: {e}")
                return
            """
            # Follow this path only if the portfolio doc is not present. Then we query API. 
            # Use this pdf to get scheme codes: https://mf.nipponindiaim.com/WaysToTransact/Documents/SMS_Code-Details_Final.pdf
            # Saving portfolio :
            # Write program to get scheme code
            scheme_code = 'EA'
            headers = {
                "User-Agent": "Mozilla/5.0",
                # Add other headers if needed (e.g., Authorization, Cookie)
            }
    
            params = {
                # Add query parameters if needed, e.g. "id": "123"
            }
    
            response = requests.get(sector_allocation_url+scheme_code, headers=headers, params=params)
            sector_alloc_data = response.json()
            response = requests.get(top_10_holdings_url, headers=headers, params=params)
            top_10_holdings_data = response.json()
            time.sleep(random.uniform(1, 5))
    
            combined = {**sector_alloc_data, **top_10_holdings_data}
    
            with open(sanitize_filename(os.path.join(save_dir,name+" portfolio.json")), "w", encoding="utf-8") as f:
                json.dump(combined, f, ensure_ascii=False, indent=4)
            """
            # Saving performance :
            # page.wait_for_selector("css=selector-for-main-content")  # Replace with a real selector
            # page.pdf(path=os.path.join(save_dir, sanitize_filename(name+" performance.pdf")), format='A4')

            # Extract the section's HTML and CSS
            section_html = page.eval_on_selector(section_selector, "el => el.outerHTML")
            styles = page.evaluate("""
                () => {
                    let css = "";
                    for (let sheet of document.styleSheets) {
                        try {
                            for (let rule of sheet.cssRules) {
                                css += rule.cssText;
                            }
                        } catch(e) {}
                    }
                    return css;
                }
            """)

            # Create a new page with the section and styles
            section_page = context.new_page()
            section_page.set_content(f"<style>{styles}</style>{section_html}")

            # Wait for rendering
            section_page.wait_for_selector(section_selector)

            # Save as PDF
            section_page.pdf(path=os.path.join(save_dir, sanitize_filename(name+" performance.pdf")), format="A4")

            #Close:
            section_page.close()

            # Downloading documents(includes portfolio in one of the docs):
            # Open downloads section:

            pdf_links = page.query_selector_all("a:has-text('Scheme Information Document'), a:has-text('Product Note')")
            download_links = [l for l in pdf_links if l.get_attribute("href").lower().endswith(".pdf")]
            count = len(download_links)
            for i in range(count):
                d_link = download_links[i]
                href = d_link.get_attribute('href')
                if not href.startswith('http'):
                    href = 'https://mf.nipponindiaim.com/'+href
                print('Link: '+href)
                with context.expect_page(timeout=90000) as new_page_info:
                    page.evaluate(f"window.open('{href}', '_blank')")
                    time.sleep(1)
                new_tab = new_page_info.value
                new_tab.wait_for_load_state("domcontentloaded")
                pdf_url = new_tab.url
                print(f"PDF opened at URL: {pdf_url}")
                download_as_pdf(pdf_url, save_dir)
                new_tab.close()
            time.sleep(random.uniform(1,3))
            # end of link, name loop

    last_time = time.time()
    print('Successfully executed with time: '+str(last_time-first_time)+' seconds.')


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # kotak_scraper(reuse=True)
    nippon_scraper(reuse_previous_version=True)

