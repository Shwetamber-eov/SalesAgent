import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SERP_API_KEY = os.getenv("SERP_API_KEY")


def radius_to_zoom(radius_km):
    """Approximate Google Maps zoom level based on desired search radius."""
    if radius_km <= 5:
        return 14
    elif radius_km <= 10:
        return 13
    elif radius_km <= 20:
        return 12
    elif radius_km <= 40:
        return 11
    elif radius_km <= 60:
        return 10
    elif radius_km <= 100:
        return 9
    else:
        return 8


def find_website_via_search(company_name, address=""):
    """Agar Google Maps se website nahi mila, toh normal Google search se try karo."""
    if not company_name:
        return "N/A"

    url = "https://serpapi.com/search"
    params = {
        "engine": "google",
        "q": f"{company_name} {address} official website",
        #"api_key": SERP_API_KEY,
        "num": 3,
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            return "N/A"

        results = response.json()
        organic_results = results.get("organic_results", [])

        if organic_results:
            link = organic_results[0].get("link", "N/A")
            return link if link else "N/A"

    except Exception as e:
        print(f"Website search failed for {company_name}: {e}")

    return "N/A"


def fetch_local_companies(query, lat=None, lon=None, num_pages=3, radius_km=50):
    url = "https://serpapi.com/search"
    all_companies = []
    zoom = radius_to_zoom(radius_km)

    for page in range(num_pages):
        start_index = page * 20
        params = {
            "engine": "google_maps",
            "q": query,
            "hl": "en",
            "start": start_index,
            "api_key": SERP_API_KEY,
        }
        if lat and lon:
            params["ll"] = f"@{lat},{lon},{zoom}z"

        try:
            response = requests.get(url, params=params)
            if response.status_code != 200:
                break

            results = response.json()
            raw_companies = results.get("local_results", [])

            if not raw_companies:
                break

            for item in raw_companies:
                company_name = item.get("title")
                address = item.get("address", "N/A")
                website = item.get("website", "N/A")

                # 👇 Website missing ho toh Google search se dhoondo
                if not website or website == "N/A":
                    website = find_website_via_search(company_name, address)

                company = {
                    "company_name": company_name,
                    "type": item.get("type", "N/A"),
                    "address": address,
                    "phone": item.get("phone", "N/A"),
                    "website": website,
                    "rating": item.get("rating", "N/A"),
                    "reviews": item.get("reviews", 0),
                    "latitude": item.get("gps_coordinates", {}).get("latitude"),
                    "longitude": item.get("gps_coordinates", {}).get("longitude"),
                    "open_state": item.get("open_state", "Unknown"),
                }
                all_companies.append(company)

        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break

    return all_companies


def save_to_master_csv(
    companies, industry, file_path="leads/all_companies.csv"
):
    if not companies:
        return

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    df_new = pd.DataFrame(companies)

    df_new["searched_industry"] = industry
    df_new["searched_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if os.path.exists(file_path):
        try:
            df_old = pd.read_csv(file_path)
            df_combined = pd.concat([df_old, df_new], ignore_index=True)
            df_combined.drop_duplicates(
                subset=["company_name", "address"], keep="last", inplace=True
            )
        except Exception:
            df_combined = df_new
    else:
        df_combined = df_new

    df_combined.to_csv(file_path, index=False, encoding="utf-8-sig")