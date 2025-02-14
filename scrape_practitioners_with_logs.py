import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from urllib.parse import urljoin

def scrape_details(detail_url):
    """
    Fetches the detail page and extracts values for:
      - Practice_Type
      - Licence_Type
      - Licence_No

    Checks for values in input fields or as plain text.
    """
    print(f"[DETAIL] Scraping detail page: {detail_url}")
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Scraper/1.0)"}
    try:
        response = requests.get(detail_url, headers=headers)
    except Exception as e:
        print(f"[DETAIL] Error fetching detail page {detail_url}: {e}")
        return {"Practice_Type": None, "Licence_Type": None, "Licence_No": None}
    if response.status_code != 200:
        print(f"[DETAIL] Error fetching detail page {detail_url}: Status code {response.status_code}")
        return {"Practice_Type": None, "Licence_Type": None, "Licence_No": None}

    soup = BeautifulSoup(response.text, "html.parser")
    details = {"Practice_Type": None, "Licence_Type": None, "Licence_No": None}

    # Try table-based extraction first.
    table = soup.find("table")
    if table:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["th", "td"])
            if len(cells) < 2:
                continue
            label = cells[0].get_text(strip=True).lower()
            # Check if value is in an input element.
            input_elem = cells[1].find("input")
            if input_elem and input_elem.has_attr("value"):
                value = input_elem["value"].strip()
            else:
                value = cells[1].get_text(strip=True)
            if "practice type" in label:
                details["Practice_Type"] = value
            elif "licence type" in label or "license type" in label:
                details["Licence_Type"] = value
            elif "licence no" in label or "license no" in label:
                details["Licence_No"] = value
        # Print extracted details if found
        print(f"[DETAIL] Extracted from table: {details}")
        if any(details.values()):
            return details

    # Fallback: try div-based extraction (if applicable)
    groups = soup.find_all("div", class_="form-group")
    for group in groups:
        label_elem = group.find("label")
        value_elem = group.find("div")
        if label_elem and value_elem:
            label = label_elem.get_text(strip=True).lower()
            value = value_elem.get_text(strip=True)
            if "practice type" in label:
                details["Practice_Type"] = value
            elif "licence type" in label or "license type" in label:
                details["Licence_Type"] = value
            elif "licence no" in label or "license no" in label:
                details["Licence_No"] = value
    print(f"[DETAIL] Extracted using fallback: {details}")
    return details

def scrape_category(url):
    """
    Scrapes all pages for a given register URL.
    For each row in the main table, if the last cell contains an anchor with class "btn btn-info",
    that cell is removed and its link is used to scrape extra details (Practice_Type, Licence_Type, Licence_No),
    which are appended to the row.
    """
    all_data = []
    current_url = url
    while current_url:
        print(f"[CATEGORY] Scraping page: {current_url}")
        headers = {"User-Agent": "Mozilla/5.0 (compatible; Scraper/1.0)"}
        response = requests.get(current_url, headers=headers)
        if response.status_code != 200:
            print(f"[CATEGORY] Error fetching {current_url}: Status code {response.status_code}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table")
        if not table:
            print("[CATEGORY] No table found on this page.")
            break

        rows = table.find_all("tr")
        # Skip header row; process remaining rows.
        for row in rows[1:]:
            cols = row.find_all("td")
            if not cols:
                continue

            # Extract text from each cell.
            raw_cells = [col.get_text(strip=True) for col in cols]
            # Check if the last cell has an <a> with class "btn btn-info"
            last_cell = cols[-1]
            if last_cell.find("a", class_="btn btn-info"):
                row_data = raw_cells[:-1]  # Exclude the "View" cell
                view_link = last_cell.find("a").get("href")
                print(f"[CATEGORY] Found view link: {view_link}")
            else:
                row_data = raw_cells
                view_link = None

            # If a view link exists, follow it and get details.
            if view_link:
                detail_link = urljoin(current_url, view_link)
                details = scrape_details(detail_link)
                print(f"[CATEGORY] Details fetched: {details}")
                row_data.extend([
                    details.get("Practice_Type"),
                    details.get("Licence_Type"),
                    details.get("Licence_No")
                ])
            else:
                row_data.extend([None, None, None])
            all_data.append(row_data)
        # Look for a "Next" link for pagination.
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
            time.sleep(1)
        else:
            break
    return all_data

def get_table_header(url):
    """
    Fetches the header row from the table on the given URL and appends three extra columns.
    If the last header cell equals "View" (case-insensitive), it is removed.
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
            # Remove the last header cell if it equals "View"
            if header and header[-1].lower() == "view":
                header = header[:-1]
            header.extend(["Practice_Type", "Licence_Type", "Licence_No"])
            return header
    return None

def main():
    # Map of category sheet names to their URLs.
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

    output_file = "KMPDC_Practitioners_Details_1.xlsx"
    writer = pd.ExcelWriter(output_file, engine="openpyxl")

    for sheet_name, url in categories.items():
        print(f"[MAIN] Processing category: {sheet_name}")
        data = scrape_category(url)
        header = get_table_header(url)
        if header and data:
            try:
                df = pd.DataFrame(data, columns=header)
            except Exception as e:
                print(f"[MAIN] Error creating DataFrame for {sheet_name}: {e}")
                continue
        elif data:
            df = pd.DataFrame(data)
        else:
            df = pd.DataFrame()
            print(f"[MAIN] No data found for {sheet_name}")
        safe_sheet = sheet_name[:31]  # Excel sheet names are limited to 31 characters.
        df.to_excel(writer, sheet_name=safe_sheet, index=False)
        print(f"[MAIN] Finished processing {sheet_name}, rows scraped: {len(df)}")
        time.sleep(1)

    writer.close()
    print(f"[MAIN] All data saved to {output_file}")

if __name__ == "__main__":
    main()
