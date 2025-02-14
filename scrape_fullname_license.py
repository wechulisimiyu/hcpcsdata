import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from urllib.parse import urljoin


def scrape_details(detail_url):
    """
    Opens the detail page and extracts the Licence_No value.
    It looks for a table row whose label contains "licence no" (or "license no").
    """
    print(f"[DETAIL] Scraping detail page: {detail_url}")
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Scraper/1.0)"}
    try:
        response = requests.get(detail_url, headers=headers)
    except Exception as e:
        print(f"[DETAIL] Error fetching detail page {detail_url}: {e}")
        return None
    if response.status_code != 200:
        print(
            f"[DETAIL] Error fetching detail page {detail_url}: Status code {response.status_code}"
        )
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    licence_no = None

    # Try table-based extraction
    table = soup.find("table")
    if table:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["th", "td"])
            if len(cells) < 2:
                continue
            label = cells[0].get_text(strip=True).lower()
            if "licence no" in label or "license no" in label:
                # Try to get value from an input element if available
                input_elem = cells[1].find("input")
                if input_elem and input_elem.has_attr("value"):
                    licence_no = input_elem["value"].strip()
                else:
                    licence_no = cells[1].get_text(strip=True)
                break

    if licence_no:
        print(f"[DETAIL] Found Licence_No: {licence_no}")
    else:
        print(f"[DETAIL] Licence_No not found on {detail_url}")
    return licence_no


def scrape_practitioners(url):
    """
    Scrapes the main practitioners page.
    For each row, extracts the full name (assumed to be in the first cell) and,
    if available, follows the view link in the last cell to get the Licence_No.
    Returns a list of dictionaries with keys "Full Name" and "Licence_No".
    """
    results = []
    current_url = url
    while current_url:
        print(f"[MAIN] Scraping page: {current_url}")
        headers = {"User-Agent": "Mozilla/5.0 (compatible; Scraper/1.0)"}
        response = requests.get(current_url, headers=headers)
        if response.status_code != 200:
            print(
                f"[MAIN] Error fetching {current_url}: Status code {response.status_code}"
            )
            break

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table")
        if not table:
            print("[MAIN] No table found on this page.")
            break

        rows = table.find_all("tr")
        # Assume the first row is the header
        for row in rows[1:]:
            cols = row.find_all("td")
            if not cols:
                continue
            # Extract full name from the first cell
            full_name = cols[0].get_text(strip=True)
            # Look for the "View" link in the last cell
            last_cell = cols[-1]
            detail_link = None
            a_tag = last_cell.find("a", class_="btn btn-info")
            if a_tag:
                detail_link = urljoin(current_url, a_tag.get("href"))
                print(f"[MAIN] Found view link for '{full_name}': {detail_link}")
            # Get licence number from the detail page (if link exists)
            licence_no = None
            if detail_link:
                licence_no = scrape_details(detail_link)
                time.sleep(1)
            results.append({"Full Name": full_name, "Licence_No": licence_no})
        # Pagination: look for a "Next" link
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
            time.sleep(1)
        else:
            break
    return results


def main():
    main_url = "https://kmpdc.go.ke/Registers/practitioners.php"
    print(f"[MAIN] Starting scraping of practitioners from {main_url}")
    data = scrape_practitioners(main_url)
    print(f"[MAIN] Total practitioners scraped: {len(data)}")
    df = pd.DataFrame(data)
    output_file = "Practitioners_FullName_Licence.xlsx"
    df.to_excel(output_file, index=False)
    print(f"[MAIN] Data saved to {output_file}")


if __name__ == "__main__":
    main()
