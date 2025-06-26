# Web Scraper for NPCI, IRDAI, SEBI, MCA, and Bank Circulars

This repository contains Python scripts to scrape regulatory circulars, public notices, and disclosures from major Indian financial institutions and regulatory bodies including:

- **NPCI (National Payments Corporation of India)**
- **IRDAI (Insurance Regulatory and Development Authority of India)**
- **SEBI (Securities and Exchange Board of India)**
- **MCA (Ministry of Corporate Affairs)**
- **Axis Bank**
- **Kotak Mutual Fund**
- **HDFC Mutual Fund**

## 📁 Repository Structure

| Filename                    | Description |
|----------------------------|-------------|
| `axis_bank_scrapper.py`    | Scrapes circulars and announcements from the Axis Bank disclosure page. |
| `kotak_nippon_scraper.py`  | Extracts scheme-related documents from Kotak Mutual Fund's website. |
| `hdfc_scraper.py`          | (To be added) Scrapes public disclosures or scheme documents from HDFC Mutual Fund. |
| `egazette_irdai_final.py`  | Scrapes e-gazette publications and circulars from the IRDAI website. |
| `egazette_sebi_final.py`   | Retrieves SEBI circulars from their e-gazette or circular publication pages. |
| `mca.py`                   | Downloads all circulars from MCA and organizes them by year. |
| `npci_final.py`            | Fetches and filters NPCI circulars with a year-wise option. |
| `urls.json`                | Stores the base URLs and metadata used across scrapers. |

## 🛠️ Requirements

- Python 3.7+
- Recommended: Use a virtual environment
- Install dependencies (if any are added)
- 
```bash
pip install -r requirements.txt
](https://github.com/C33cd/web-scraper/blob/main/README.md)
