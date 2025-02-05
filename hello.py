import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

def scrape_hcpcs_codes(url):
    """
    Scrapes a HCPCS codes page from the given URL and returns a list of dictionaries.
    Each dictionary contains the code and its description.
    """
    headers = {"User-Agent": "Mozilla/5.0 (compatible; ExampleScraper/1.0)"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching {url}: Status code {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Attempt to locate the table with the codes
    table = soup.find("table")
    if not table:
        print(f"No table found on {url}")
        return []
    
    data = []
    rows = table.find_all("tr")
    # Skip the header row if one exists
    for row in rows[1:]:
        cols = row.find_all("td")
        if len(cols) >= 2:
            code = cols[0].get_text(strip=True)
            description = cols[1].get_text(strip=True)
            data.append({"Code": code, "Description": description})
    return data

def scrape_all_groups(groups, base_url="https://www.hcpcsdata.com/Codes/"):
    """
    Scrapes the HCPCS codes for each group in the provided list.
    Returns a dictionary mapping each group letter to its list of codes.
    """
    group_data = {}
    for group in groups:
        url = base_url + group
        print(f"Scraping group {group} from {url} ...")
        codes = scrape_hcpcs_codes(url)
        if codes:
            group_data[group] = codes
        else:
            print(f"No data for group {group}")
        # Pause to be respectful to the server
        time.sleep(1)
    return group_data

if __name__ == "__main__":
    # Create a list of groups from A to Z
    groups = [chr(i) for i in range(65, 91)]
    all_data = scrape_all_groups(groups)
    
    if all_data:
        output_file = "2025_HCPCS_codes_multisheet.xlsx"
        # Create an Excel file with a separate sheet for each group
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            for group, codes in all_data.items():
                df = pd.DataFrame(codes)
                # Use the group letter as the sheet name
                df.to_excel(writer, sheet_name=group, index=False)
        print(f"Scraped data saved to {output_file} with separate sheets for each group.")
    else:
        print("No codes were scraped. Please check your parsing logic or website structure.")

