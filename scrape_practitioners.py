import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from urllib.parse import urljoin


def scrape_category(url):
    """
    Scrapes all pages of a given register URL.
    Returns a list of rows (each row is a list of cell values).
    Handles pagination by looking for a 'Next' link.
    """
    all_data = []
    current_url = url
    while current_url:
        print(f"Scraping page: {current_url}")
        headers = {"User-Agent": "Mozilla/5.0 (compatible; Scraper/1.0)"}
        response = requests.get(current_url, headers=headers)
        if response.status_code != 200:
            print(f"Error fetching {current_url}: Status code {response.status_code}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table")
        if not table:
            print("No table found on this page.")
            break

        rows = table.find_all("tr")
        # Skip the header row (assumes first row is header)
        for row in rows[1:]:
            cols = row.find_all("td")
            if cols:
                row_data = [col.get_text(strip=True) for col in cols]
                all_data.append(row_data)

        # Look for a "Next" link (check common pagination patterns)
        next_link = None
        paginate = soup.find("div", class_="dataTables_paginate")
        if paginate:
            next_anchor = paginate.find(
                "a", string=lambda text: text and "next" in text.lower()
            )
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
    Fetches the header row from the table on the given URL.
    Returns a list of header names.
    """
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Scraper/1.0)"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    if table:
        header_row = table.find("tr")
        if header_row:
            header_cells = header_row.find_all(["th", "td"])
            return [cell.get_text(strip=True) for cell in header_cells]
    return None


def main():
    # Categories mapping: sheet name -> URL.
    # NOTE: Several URLs are returning 404. Verify and update them as needed.
    categories = {
        "Local Licensed Practitioners’ Master Register": "https://kmpdc.go.ke/Registers/practitioners.php",
        "Medical & Dental General Practice Register": "http://kmpdc.go.ke/Registers/General_Practitioners.php",
        "Medical & Dental Registrar Register": "https://kmpdc.go.ke/Registers/Registrar_Practitioners.php",
        "Medical & Dental Senior Registrar Register": "http://kmpdc.go.ke/Registers/Senior_Registrar_Practitioners.php",
        "Medical & Dental Specialist Practice Register": "http://kmpdc.go.ke/Registers/Specialist_Practitioners.php",
        "Community Oral Health Officers’ Register": "http://kmpdc.go.ke/Registers/Licenced_COHO.php",
        "Medical & Dental Internship Register": "http://kmpdc.go.ke/Registers/InternshipRegister.php",
        "Foreign Practitioners’ Register": "http://kmpdc.go.ke/Registers/LicencedForeignPractitioners.php",
        "Foreign Students’ Register": "http://kmpdc.go.ke/Registers/LicencedForeignPractitioners.php",
    }

    output_file = "KMPDC_Practitioners.xlsx"
    writer = pd.ExcelWriter(output_file, engine="openpyxl")

    for sheet_name, url in categories.items():
        print(f"Processing category: {sheet_name}")
        data = scrape_category(url)
        header = get_table_header(url)
        if header and data:
            df = pd.DataFrame(data, columns=header)
        elif data:
            df = pd.DataFrame(data)
        else:
            df = pd.DataFrame()
            print(f"No data found for {sheet_name}")
        # Excel sheet names have a maximum length of 31 characters.
        safe_sheet = sheet_name[:31]
        df.to_excel(writer, sheet_name=safe_sheet, index=False)
        time.sleep(1)

    # Use writer.close() instead of writer.save()
    writer.close()
    print(f"All data saved to {output_file}")


if __name__ == "__main__":
    main()
