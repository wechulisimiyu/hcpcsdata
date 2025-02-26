import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

def get_total_entries(soup):
    """Extracts total number of entries from the DataTables info element."""
    info_div = soup.find("div", class_="dataTables_info")
    total = None
    if info_div:
        text = info_div.get_text(strip=True)
        # Look for pattern like "of 8,640 entries"
        match = re.search(r'of\s+([\d,]+)\s+entries', text)
        if match:
            total_str = match.group(1).replace(",", "")
            try:
                total = int(total_str)
            except Exception as e:
                print(f"[INFO] Error parsing total: {e}")
    return total

def scrape_page(start, length=100):
    """
    Fetches one page of the pharmacists register using query parameters.
    Returns:
      - header: list of column names (from the table header)
      - data: list of rows (each row is a list of cell texts)
      - total_entries: total number of entries (only determined on the first page)
    """
    base_url = "https://practice.pharmacyboardkenya.org/LicenseStatus"
    params = {
        "register": "pharmacists",
        "start": start,
        "length": length
    }
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Scraper/1.0)"}
    print(f"[SCRAPE] Fetching page with start={start} and length={length}")
    response = requests.get(base_url, params=params, headers=headers)
    if response.status_code != 200:
        print(f"[SCRAPE] Error fetching page (start={start}): Status code {response.status_code}")
        return None, None, None
    soup = BeautifulSoup(response.text, "html.parser")
    total_entries = None
    if start == 0:
        total_entries = get_total_entries(soup)
        if total_entries is not None:
            print(f"[SCRAPE] Total entries found: {total_entries}")
        else:
            print("[SCRAPE] Could not parse total entries; defaulting to current page only.")
    
    # Extract table header and rows
    table = soup.find("table")
    if not table:
        print("[SCRAPE] No table found on this page.")
        return None, None, total_entries

    header_row = table.find("tr")
    if not header_row:
        print("[SCRAPE] No header row found.")
        return None, None, total_entries
    header = [cell.get_text(strip=True) for cell in header_row.find_all(["th", "td"])]

    # Extract data rows (skip header)
    data = []
    for row in table.find_all("tr")[1:]:
        cells = row.find_all("td")
        if not cells:
            continue
        row_data = [cell.get_text(strip=True) for cell in cells]
        data.append(row_data)
    print(f"[SCRAPE] Fetched {len(data)} rows from page starting at {start}")
    return header, data, total_entries

def main():
    # First, fetch the first page to get header and total entries.
    header, data, total_entries = scrape_page(0, 100)
    if header is None or data is None:
        print("[MAIN] Failed to fetch initial page.")
        return

    if total_entries is None:
        print("[MAIN] Total entries not parsed; using only first page.")
        total_entries = len(data)
    
    all_data = data.copy()
    # Loop over remaining pages
    for start in range(100, total_entries, 100):
        _, page_data, _ = scrape_page(start, 100)
        if page_data:
            all_data.extend(page_data)
        else:
            print(f"[MAIN] No data for start={start}")
        time.sleep(1)

    print(f"[MAIN] Total rows scraped: {len(all_data)}")
    
    # Create DataFrame using header from the first page.
    try:
        df = pd.DataFrame(all_data, columns=header)
    except Exception as e:
        print(f"[MAIN] Error creating DataFrame: {e}")
        df = pd.DataFrame(all_data)
    
    # Debug: print the header so we know which columns are available.
    print(f"[MAIN] Table header: {header}")
    
    # Based on inspection, decide which column(s) hold the full name and licence number.
    # For example, if the full name is in a column that contains "name" and licence number in a column that contains "license" or "licence".
    full_name_col = None
    licence_col = None
    for col in header:
        lower = col.lower()
        if "name" in lower and full_name_col is None:
            full_name_col = col
        if ("licence" in lower or "license" in lower) and licence_col is None:
            licence_col = col
    if not full_name_col or not licence_col:
        print("[MAIN] Could not determine the required columns from header.")
        return
    print(f"[MAIN] Using '{full_name_col}' for Full Name and '{licence_col}' for Licence_No.")

    # Keep only the two desired columns.
    df_subset = df[[full_name_col, licence_col]]
    df_subset = df_subset.rename(columns={full_name_col: "Full Name", licence_col: "Licence_No"})
    output_file = "Pharmacists_Register_Partial.xlsx"
    df_subset.to_excel(output_file, index=False)
    print(f"[MAIN] Data saved to {output_file}")

if __name__ == "__main__":
    main()
