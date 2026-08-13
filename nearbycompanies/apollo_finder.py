import os
import time
import requests
import pandas as pd
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")

PEOPLE_SEARCH_URL = "https://api.apollo.io/api/v1/mixed_people/api_search"
ORG_SEARCH_URL = "https://api.apollo.io/api/v1/mixed_companies/search"
MATCH_URL = "https://api.apollo.io/api/v1/people/match"


def extract_domain(website):
    """Website URL se clean domain nikalo (e.g. https://abc.com/ -> abc.com)"""
    if not website or website == "N/A":
        return None
    try:
        parsed = urlparse(website if website.startswith("http") else f"http://{website}")
        domain = parsed.netloc or parsed.path
        return domain.replace("www.", "").strip("/")
    except Exception:
        return None


def find_domain_by_company_name(company_name):
    """Website missing ho toh company naam se Apollo ke Organization Search se domain dhoondo."""
    if not company_name:
        return None

    headers = {"Content-Type": "application/json", "X-Api-Key": APOLLO_API_KEY}
    params = {"q_organization_name": company_name, "per_page": 1}

    try:
        resp = requests.post(ORG_SEARCH_URL, params=params, headers=headers)
        if resp.status_code != 200:
            print(f"Org search failed for {company_name}: {resp.status_code}")
            return None

        orgs = resp.json().get("organizations", [])
        if orgs:
            org = orgs[0]
            domain = org.get("primary_domain")
            if domain:
                return domain
            # fallback: website_url se nikaalo
            return extract_domain(org.get("website_url"))

    except Exception as e:
        print(f"Org search error for {company_name}: {e}")

    return None


def find_people_for_domain(domain, titles=None, per_page=5):
    """Ek company domain ke liye log (people) dhoondo."""
    headers = {"Content-Type": "application/json", "X-Api-Key": APOLLO_API_KEY}
    payload = {
        "q_organization_domains_list": [domain],
        "per_page": per_page,
    }
    if titles:
        payload["person_titles"] = titles

    resp = requests.post(PEOPLE_SEARCH_URL, json=payload, headers=headers)
    if resp.status_code != 200:
        print(f"People search failed for {domain}: {resp.status_code} {resp.text[:200]}")
        return []

    return resp.json().get("people", [])


def enrich_person(person_id):
    """Ek person ka email reveal karo (credits use hote hain)."""
    headers = {"Content-Type": "application/json", "X-Api-Key": APOLLO_API_KEY}
    payload = {"id": person_id, "reveal_personal_emails": False}

    resp = requests.post(MATCH_URL, json=payload, headers=headers)
    if resp.status_code != 200:
        return None

    return resp.json().get("person")


def process_companies_csv(input_csv="leads/all_companies.csv",
                           output_csv="leads/contacts.csv",
                           titles=None,
                           enrich_emails=True):
    df = pd.read_csv(input_csv)
    all_contacts = []

    for _, row in df.iterrows():
        website = row.get("website")
        company_name = row.get("company_name", "Unknown")

        domain = extract_domain(website)
        match_type = "domain"

        # 👇 Website missing ho toh naam se domain dhoondo
        if not domain:
            print(f"Website missing for {company_name}, searching by name...")
            domain = find_domain_by_company_name(company_name)
            match_type = "name_lookup"
            time.sleep(1)

        if not domain:
            print(f"Skipping {company_name} — koi domain nahi mila.")
            continue

        print(f"Searching contacts for: {company_name} ({domain}) [{match_type}]")
        people = find_people_for_domain(domain, titles=titles)

        for p in people:
            contact = {
                "company_name": company_name,
                "domain": domain,
                "match_type": match_type,   # 👈 track karo kaise domain mila
                "person_name": f"{p.get('first_name', '')} {p.get('last_name', '')}".strip(),
                "title": p.get("title", "N/A"),
                "linkedin_url": p.get("linkedin_url", "N/A"),
                "email": "N/A",
            }

            if enrich_emails and p.get("id"):
                enriched = enrich_person(p["id"])
                if enriched:
                    contact["email"] = enriched.get("email", "N/A")
                time.sleep(1)
                if enrich_emails and p.get("id"):
    

                 all_contacts.append(contact)

        time.sleep(1)

    contacts_df = pd.DataFrame(all_contacts)
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    contacts_df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"\n✅ {len(contacts_df)} contacts saved to {output_csv}")


if __name__ == "__main__":
    target_titles = ["Founder", "CEO", "Owner", "Director", "Manager", "Co-Founder", "Managing Director", "Head"]

    process_companies_csv(
        input_csv="leads/all_companies.csv",
        output_csv="leads/contacts.csv",
        titles=target_titles,
        enrich_emails=True,
    )