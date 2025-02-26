import requests
import pandas as pd

def fetch_distribution_data():
    url = "https://practice.pharmacyboardkenya.org/ajax/public?graph=distribution"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Scraper/1.0)"}
    print(f"[FETCH] Fetching distribution data from: {url}")
    response = requests.get(url, headers=headers)
    print(f"[FETCH] Status code: {response.status_code}")
    # Print the first 500 characters of the response text for debugging.
    response_text = response.text.strip()
    print("[FETCH] Response text (first 500 chars):")
    print(response_text[:500])
    
    try:
        data = response.json()
    except Exception as e:
        print(f"[FETCH] Error decoding JSON: {e}")
        return None
    return data

def main():
    data = fetch_distribution_data()
    if data is None:
        print("[MAIN] Failed to fetch distribution data.")
        return
    
    # Convert the fetched JSON data to a DataFrame.
    # (If data is not already a flat list/dict, you may need to adjust the DataFrame construction.)
    try:
        df = pd.DataFrame(data)
    except Exception as e:
        print(f"[MAIN] Error creating DataFrame: {e}")
        return
    
    output_file = "Pharmacists_Distribution.xlsx"
    df.to_excel(output_file, index=False)
    print(f"[MAIN] Data saved to {output_file}")

if __name__ == "__main__":
    main()
