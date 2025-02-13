import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from urllib.parse import urljoin


def scrape_details(detail_url):
    """
    Given a URL for a detail page (from the 'view' link),
    fetches the page and extracts the three fields:
    Practice_Type, Licence_Type, Licence_No.
    Assumes the page shows a table with rows where the first cell is a label and
    the second cell is the value.
    """
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Scraper/1.0)"}
    try:
        response = requests.get(detail_url, headers=headers)
    except Exception as e:
        print(f"Error fetching detail page {detail_url}: {e}")
        return {"Practice_Type": None, "Licence_Type": None, "Licence_No": None}

    if response.status_code != 200:
        print(
            f"Error fetching detail page {detail_url}: Status code {response.status_code}"
        )
        return {"Practice_Type": None, "Licence_Type": None, "Licence_No": None}

    soup = BeautifulSoup(response.text, "html.parser")
    details = {"Practice_Type": None, "Licence_Type": None, "Licence_No": None}

    # Attempt to locate a table with the details.
    rows = soup.find_all("tr")
    for row in rows:
        cells = row.find_all(["th", "td"])
        if len(cells) < 2:
            continue
        label = cells[0].get_text(strip=True).lower()
        value = cells[1].get_text(strip=True)
        if "practice type" in label:
            details["Practice_Type"] = value
        elif "licence type" in label or "license type" in label:
            details["Licence_Type"] = value
        elif "licence no" in label or "license no" in label:
            details["Licence_No"] = value

    return details


def scrape_category(url):
    """
    Scrapes all pages for a given practitioner register URL.
    For each row, looks for a 'view' link in the last column, follows it,
    and appends the extra details to the row.
    Returns a list of rows (each row is a list of cell values, including extra details).
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
        # Assume first row is header; process remaining rows
        for row in rows[1:]:
            cols = row.find_all("td")
            if not cols:
                continue
            # Get the text of each cell
            row_data = [col.get_text(strip=True) for col in cols]
            # Assume the last column holds the 'view' link
            last_td = cols[-1]
            link_tag = last_td.find("a")
            if link_tag and link_tag.get("href"):
                detail_link = urljoin(current_url, link_tag.get("href"))
                details = scrape_details(detail_link)
                row_data.extend(
                    [
                        details.get("Practice_Type"),
                        details.get("Licence_Type"),
                        details.get("Licence_No"),
                    ]
                )
            else:
                row_data.extend([None, None, None])
            all_data.append(row_data)

        # Look for pagination "Next" link
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
            time.sleep(1)  # Delay between page requests
        else:
            break
    return all_data


def get_table_header(url):
    """
    Fetches the header row from the table on the given URL.
    Returns a list of header names and appends the extra columns.
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
            # Append new columns for the extra details
            header.extend(["Practice_Type", "Licence_Type", "Licence_No"])
            return header
    return None


def main():
    # Map category sheet names to their register URLs.
    categories = {
        "Local Licensed Practitioners’ Master Register": "https://kmpdc.go.ke/Registers/practitioners.php",
        "Medical & Dental General Practice Register": "https://kmpdc.go.ke/Registers/General_Practitioners.php",
        "Medical & Dental Registrar Register": "https://kmpdc.go.ke/Registers/Registrar.php",
        "Medical & Dental Senior Registrar Register": "https://kmpdc.go.ke/Registers/Senior_Registrar.php",
        "Medical & Dental Specialist Practice Register": "https://kmpdc.go.ke/Registers/Specialist_Practice.php",
        "Community Oral Health Officers’ Register": "https://kmpdc.go.ke/Registers/Community_Oral_Health.php",
        "Medical & Dental Internship Register": "https://kmpdc.go.ke/Registers/Internship.php",
        "Foreign Practitioners’ Register": "https://kmpdc.go.ke/Registers/Foreign_Practitioners.php",
        "Foreign Students’ Register": "https://kmpdc.go.ke/Registers/Foreign_Students.php",
    }

    output_file = "KMPDC_Practitioners_with_Details.xlsx"
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
        # Excel sheet names have a 31-character limit
        safe_sheet = sheet_name[:31]
        df.to_excel(writer, sheet_name=safe_sheet, index=False)
        time.sleep(1)  # Delay between categories

    writer.close()
    print(f"All data saved to {output_file}")


if __name__ == "__main__":
    main()
