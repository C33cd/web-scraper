import base64
import json
import os
import random
import time
from math import ceil

os.makedirs('downloads', exist_ok=True)
import requests
from playwright.sync_api import sync_playwright, Error, Page, Browser, BrowserContext
import re

def sanitize_filename(name, max_length=100):
    # name = name.replace('\t', '_')  # Replace tab characters explicitly
    # # Replace invalid Windows filename characters with underscore
    # name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # return name[:max_length]
    # Replace forbidden characters including control characters
    name = re.sub(r'[<>:"/\\|?*\n\r\t]', '_', name)
    # Replace any remaining non-printable control characters
    name = ''.join(c if c.isprintable() else '_' for c in name)
    return name.strip()[:max_length]


def backoff_retry(failure_count):
    delay = min(30, (2 ** failure_count) + random.uniform(0, 1))
    print(f"Backing off for {delay:.2f} seconds...")
    time.sleep(delay)



def download_as_pdf(pdf_url: str, download_dir: str, headers: dict[str, str], name: str = ''):
    # Pass the PDF URL as pdf_url and the directory where you want to store file as download_dir
    os.makedirs(download_dir, exist_ok=True)
    filename = name.removesuffix('\n') if name else os.path.basename(pdf_url.split("?")[0])
    save_path = os.path.join(download_dir, sanitize_filename(filename))
    """
    Fill in your headers and cookies here in the same format


    Steps to fill in:
    1. Go to https://www.mca.gov.in/bin/ebook/dms/getdocument?doc=Nzc5Mg==&docCategory=Circulars&type=open or any pdf link of the website
    2. Go to Devtools (ctrl+shift+i) and then to Network
    3. Reload the page, keeping Devtools open
    4. Right click on first request starting with 'getDocument?' and copy as curl (choose any of the options depending on your command prompt)
    5. Paste the CURL in a text editor
    6. All the text preceded by -H should be in header, -b should be in cookies.
        eg.
        curl 'https://example.com/file.pdf' \
        -H 'accept: application/pdf' \
        -H 'user-agent: Mozilla/5.0' \
        -H 'referer: https://example.com/' \
        -b 'sessionid=abc123; csrftoken=xyz456'

        gets converted as:

        url = "https://example.com/file.pdf"

        headers = {
            "accept": "application/pdf",
            "user-agent": "Mozilla/5.0",
            "referer": "https://example.com/"
        }

        cookies = {
            "sessionid": "abc123",
            "csrftoken": "xyz456"
        }

    """

    cookies = {
    }

    if not save_path.lower().endswith('.pdf'):
        save_path += '.pdf'
    retries = 4
    for attempt in range(retries):
        try:
            response = requests.get(pdf_url, headers=headers, cookies=cookies)
            if response and response.status_code != 200:
                print(f"Failed to load homepage: {response.status_code}")
                backoff_retry(attempt)
                continue
            with open(save_path, "wb") as f:
                f.write(response.content)
                print(f"Downloaded to: {save_path}")
                f.close()
            if "application/pdf" not in response.headers.get("content-type", ""):
                print("Did not receive a PDF. Response content-type:", response.headers.get("content-type"))
                print("Response text:", response.text[:500])  # Print first 500 chars for debugging
                break
            break
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            backoff_retry(attempt)

def build_download_url(link, docCategory="Circulars"):
    doc = encode_link(link)
    return f"https://www.mca.gov.in/bin/ebook/dms/getdocument?doc={doc}&docCategory={docCategory}&type=open"


def encode_link(link_value):
    # Ensure link_value is a string
    link_str = str(link_value)
    encoded = base64.b64encode(link_str.encode('utf-8')).decode('utf-8')
    return encoded


def save_documents(cat: str, d_dir: str, headers: dict[str, str]):
    with open(cat+'.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        f.close()
    # yrs = set(item['notificationdate'].strip()[-4:] for item in data['data'] if 'notificationdate' in item)
    links = []
    names = []
    years = []
    if cat == 'Forms':
        links = [item['link'] for item in data['data'] if 'link' in item]
        names = [item['shortDescription'] if 'shortDescription' in item else '' for item in data['data']]
        years = [item['notificationdate'].strip()[-4:] for item in data['data'] if 'notificationdate' in item]
    elif cat == 'Notifications':
        for item in data['data']:
            if item['docGroup'].strip() == 'The Companies Act, 2013':
                links.append(item['link'])
                names.append(item['shortDescription'] if 'shortDescription' in item else '')
                years.append(item['notificationdate'].strip()[-4:] if 'notificationdate' in item else 'Unknown')
    else:
        # links = [item['link'] for item in data['data'] if 'link' in item]
        # names = [item['shortDescription'] for item in data['data'] if 'shortDescription' in item]
        # years = [item['notificationdate'].strip()[-4:] for item in data['data'] if 'notificationdate' in item]
        for item in data['data']:
            links.append(item['link'])
            names.append(item['shortDescription'] if 'shortDescription' in item else '')
            years.append(item['notificationdate'].strip()[-4:] if 'notificationdate' in item else 'Unknown')

    print(links)
    yrs = set(years)
    for yr in yrs:
        os.makedirs(os.path.join(d_dir, sanitize_filename(yr)), exist_ok=True)
    for link, name, year in zip(links, names, years):
        url = build_download_url(link=link, docCategory=cat)
        print(d_dir)
        print(year)
        print(os.path.join(d_dir, sanitize_filename(year)))
        download_as_pdf(pdf_url=url, download_dir=os.path.join(d_dir, sanitize_filename(year)), name=name, headers=headers)
        time.sleep(1.5)


def mca_new_scr():
    d_dir = "MCA_Data"
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "max-age=0",
        "priority": "u=0, i",
        "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    }
    # names = ["Circulars", "Forms", "Notifications"]
    names = ["Notifications", "Circulars"]
    # TO DO: Add circular based filtering for forms in save_data function
    try:
        for cat in names:
            os.makedirs(sanitize_filename(cat), exist_ok=True)
            url = f"https://www.mca.gov.in/bin/ebook/service/documentMetadata?docCategory={cat}&flag=initial&status=Current"
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise exception for HTTP errors

            data = response.json()  # Parse JSON content
            # Save to local file
            with open(cat+".json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"JSON data saved to {cat}.json")
            save_documents(cat=cat, d_dir=os.path.join(d_dir, sanitize_filename(cat)), headers=headers)

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")



mca_new_scr()