import os
import requests


def download_as_pdf(pdf_url: str, download_dir: str):
    # Pass the PDF URL as pdf_url and the directpry where you want to store file as download_dir
    os.makedirs(download_dir, exist_ok=True)
    filename = os.path.basename(pdf_url.split("?")[0])
    save_path = os.path.join(download_dir, filename)
    response = requests.get(pdf_url)
    with open(save_path, "wb") as f:
        f.write(response.content)
    print(f"Downloaded to: {save_path}")

def npci_scraper():
