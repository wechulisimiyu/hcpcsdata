import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from urllib.parse import urljoin

def scrape_pharmacists(url):
    """
    Scrapes all pages for the pharmacists register.
    Returns a list of rows (each row is a list of cell values).
    Handles pagination if a "Next" link is found.
    """
    all_data = []
    current_url = url
    while current_url:
        print(f"[SCRAPE] Scraping page: {current_url}")
        headers = {"User-Agent": "Mozilla/5.0 (compatible; Scraper/1.0)"}
        response = requests.get(current_url, headers=headers)
        if response.status_code != 200:
            print(f"[SCRAPE] Error fetching {current_url}: Status code {response.status_code}")
            break
        
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table")
        if not table:
            print("[SCRAPE] No table found on this page.")
            break
        
        rows = table.find_all("tr")
        # Assume first row is header; extract data rows.
        for row in rows[1:]:
            cols = row.find_all("td")
            if not cols:
                continue
            row_data = [col.get_text(strip=True) for col in cols]
            all_data.append(row_data)
        # Check for a pagination "Next" link.
        next_link = None
        paginate = soup.find("div", class_="dataTables_paginate")
        if paginate:
            next_anchor = paginate.find("a", string=lambda text: text and "next" in text.lower())
            if next_anchor and "disabled" not in next_anchor.get("class", []):
                href = next_anchor.get("href")
                if href:
                    next_link = urljoin(current_url, href)
        if not next_link:
            next_anchor = soup.find("a", rel="next")
            if next_anchor:
                href = next_anchor.get("href")
                if href:
                    next_link = urljoin(current_url, href)
        if next_link and next_link != current_url:
            current_url = next_link
            time.sleep(1)  # Respectful delay
        else:
            break
    return all_data

def get_table_header(url):
    """
    Retrieves the header row from the table on the given URL.
    Returns a list of column names.
    """
    headers_req = {"User-Agent": "Mozilla/5.0 (compatible; Scraper/1.0)"}
    response = requests.get(url, headers=headers_req)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    if table:
        header_row = table.find("tr")
        if header_row:
            header_cells = header_row.find_all(["th", "td"])
            header = [cell.get_text(strip=True) for cell in header_cells]
            return header
    return None

def main():
    url = "https://practice.pharmacyboardkenya.org/LicenseStatus?register=pharmacists"
    print(f"[MAIN] Starting scraping for pharmacists register from {url}")
    
    # Scrape all pages for the register.
    data = scrape_pharmacists(url)
    print(f"[MAIN] Total rows scraped (excluding header): {len(data)}")
    
    # Retrieve table header.
    header = get_table_header(url)
    if header and data:
        try:
            df = pd.DataFrame(data, columns=header)
        except Exception as e:
            print(f"[MAIN] Error creating DataFrame with header: {e}")
            df = pd.DataFrame(data)
    elif data:
        df = pd.DataFrame(data)
    else:
        df = pd.DataFrame()
        print("[MAIN] No data found!")
    
    output_file = "Pharmacists_Register.xlsx"
    df.to_excel(output_file, index=False)
    print(f"[MAIN] Data saved to {output_file}")

if __name__ == "__main__":
    main()
