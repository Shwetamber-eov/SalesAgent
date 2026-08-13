from dataclasses import dataclass
import os
import pandas as pd
import streamlit as st
from streamlit_geolocation import streamlit_geolocation
from geopy.geocoders import Nominatim
from map_scraper import fetch_local_companies, save_to_master_csv


# 1. DATA MODEL
@dataclass
class UserLocation:
    latitude: float
    longitude: float
    address: str = ""


# 2. LOCATION SERVICE
class LocationService:

    def __init__(self):
        self.geolocator = Nominatim(user_agent="sales_agent_company_finder")

    def get_location(self):
        """Get user's current latitude and longitude."""
        data = streamlit_geolocation()

        if not data:
            return None

        latitude = data.get("latitude")
        longitude = data.get("longitude")

        if latitude is None or longitude is None:
            return None

        address = self.get_address(latitude, longitude)

        return UserLocation(
            latitude=latitude, longitude=longitude, address=address
        )

    def get_address(self, latitude, longitude):
        """Convert coordinates into an address."""
        try:
            location = self.geolocator.reverse((latitude, longitude))
            return location.address if location else ""
        except Exception:
            return ""


# 3. COMPANY FINDER SERVICE
class CompanyFinder:
    def search(self, industry, location, radius):
        if industry == "All Industries":
            query = f"companies near {location.address}"
        else:
            query = f"{industry} companies near {location.address}"

        return fetch_local_companies(
            query=query,
            lat=location.latitude,
            lon=location.longitude,
            num_pages=3,
            radius_km=radius,   
        )

# 4. SALES AGENT APPLICATION
class SalesAgentApp:

    INDUSTRIES = [
        "All Industries",
        "IT",
        "Pharma",
        "Food",
        "Manufacturing",
        "Healthcare",
        "Automobile",
        "Logistics",
        "Textile",
        "Construction",
        "Education",
        "Finance",
        "Retail",
    ]

    def __init__(self):
        self.location_service = LocationService()
        self.company_finder = CompanyFinder()

    def setup_page(self):
        st.set_page_config(
            page_title="Sales Agent - Nearby Companies",
            page_icon="🏢",
            layout="wide",
        )

    def show_header(self):
        st.title("🏢 Sales Agent - Nearby Companies Finder")
        st.caption("Find nearby companies based on location and industry.")
        st.divider()

    def get_user_location(self):
        st.subheader("Your Location")

        location = self.location_service.get_location()

        if not location:
            st.info("Please allow location access to find nearby companies.")
            return None

        st.success("Location detected successfully!")

        if location.address:
            st.write("**Your Address:**", location.address)
        else:
            st.warning("Could not determine your address.")

        return location

    def show_search_settings(self):
        st.divider()
        st.subheader(" Search Companies")

        col1, col2 = st.columns(2)
        with col1:
            industry = st.selectbox("Select Industry", self.INDUSTRIES)
        with col2:
            radius = st.slider(
                "Search Radius (km)",
                min_value=5,
                max_value=100,
                value=50,
                step=5,
            )

        st.info(f"Companies will be searched within **{radius} km**.")
        return industry, radius

    def search_companies(self, industry, location, radius): #👈 radius add kiya
        if not location.address:
            st.warning("Location/address is not available.")
            return []

        with st.spinner("Searching nearby companies..."):
            return self.company_finder.search(industry, location, radius) #👈 radius pass kiya

    def display_export_options(self, df: pd.DataFrame):
        """Display download button for CSV export."""
        st.subheader("Export Data")

        csv_data = df.to_csv(index=False).encode("utf-8")

        col1, col2 = st.columns([1, 3])
        with col1:
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name="nearby_companies.csv",
                mime="text/csv",
                use_container_width=True,
            )

    def display_map(self, companies):
        """Display an interactive map showing company locations."""
        map_data = []
        for c in companies:
            if c.get("latitude") and c.get("longitude"):
                map_data.append(
                    {
                        "lat": c["latitude"],
                        "lon": c["longitude"],
                        "company_name": c.get("company_name", "Unknown"),
                    }
                )

        if map_data:
            st.subheader("🗺️ Map View")
            map_df = pd.DataFrame(map_data)
            st.map(map_df, zoom=11, color="#FF0000")

        

    def display_companies(self, companies):
        if not companies:
            st.warning(
                "No companies found. Try another industry or location."
            )
            return

        st.success(f"Found {len(companies)} companies.")

        df = pd.DataFrame(companies)

        export_columns = [
            "company_name",
            "type",
            "address",
            "phone",
            "website",
            "rating",
            "reviews",
            "open_state",
            "latitude",
            "longitude",
        ]
        df = df[[col for col in export_columns if col in df.columns]]

        self.display_export_options(df)
        self.display_map(companies)

        st.divider()
        st.subheader("Nearby Companies Details")

        for index, company in enumerate(companies, 1):
            self.display_company(index, company)

    def display_company(self, index, company):
        with st.container():
            st.markdown(f"### {index}. {company.get('company_name', 'Unknown')}")

            col1, col2 = st.columns(2)

            with col1:
                st.write("**Industry:**", company.get("type", "N/A"))
                st.write("**Address:**", company.get("address", "N/A"))
                st.write("**Rating:**", company.get("rating", "N/A"))

            with col2:
                st.write("**Reviews:**", company.get("reviews", 0))
                st.write("**Phone:**", company.get("phone", "N/A"))

                website = company.get("website", "N/A")
                if website != "N/A" and website:
                    st.write(f"**Website:** [{website}]({website})")
                else:
                    st.write("**Website:** N/A")

            st.divider()

    def run(self):
        self.setup_page()
        self.show_header()

        location = self.get_user_location()

        if not location:
            return

        industry, radius = self.show_search_settings()

        if "companies" not in st.session_state:
            st.session_state.companies = None

        if st.button("🔍 Search Companies", use_container_width=True):
            # radius variable yahan pass kiya 👇
            companies = self.search_companies(industry, location, radius)

            if companies:
                save_to_master_csv(companies, industry)
                st.session_state.companies = companies
                st.success(
                    f"✅ {len(companies)} companies saved to 'leads/all_companies.csv'!"
                )

        if st.session_state.companies is not None:
            self.display_companies(st.session_state.companies)


# 5. RUN APPLICATION
if __name__ == "__main__":
    app = SalesAgentApp()
    app.run()