"""
Clinic search agent for finding nearby clinics in Singapore.
Supports postal code-based and area-based search with distance calculation.
"""
import pandas as pd
import json
import os
import re
from typing import List, Dict, Any, Optional, Tuple

from rapidfuzz import process, fuzz

from .llm import get_llm_client, get_default_model
from .config import PROJECT_ROOT
from .location import (
    calculate_postal_distance,
    extract_postal_code,
    get_nearby_areas,
    create_clinic_map,
    map_to_html,
    SINGAPORE_AREA_COORDS
)


class ClinicSearchAgent:
    """Agent for searching clinics based on location."""

    def __init__(self, data_path: str = None):
        """
        Initialize the clinic search agent.

        Args:
            data_path: Path to clinic data Excel/CSV file
        """
        self.data_path = data_path or os.path.join(PROJECT_ROOT, "Clinics.xlsx")
        self.df = None
        self.load_data()

    def load_data(self) -> bool:
        """
        Load and standardize clinic data.

        Returns:
            True if data loaded successfully, False otherwise
        """
        if not os.path.exists(self.data_path):
            print(f"Clinic data file not found: {self.data_path}")
            return False

        try:
            # Read file based on extension
            if self.data_path.endswith('.csv'):
                df = pd.read_csv(self.data_path)
            else:
                df = pd.read_excel(self.data_path)

            df = df.fillna('')

            # Map column names to standard keys
            c_map = {}
            for col in df.columns:
                cl = col.lower()
                if 'gp clinic name' in cl or 'clinic name' in cl or 'name' in cl:
                    c_map[col] = 'Name'
                elif 'clinic address' in cl or 'address' in cl:
                    c_map[col] = 'Address'
                elif 'area' in cl:
                    c_map[col] = 'Area'
                elif 'contact' in cl or 'phone' in cl or 'tel' in cl:
                    c_map[col] = 'Contact'
                elif 'postal' in cl:
                    c_map[col] = 'PostalCode'

            if c_map:
                df.rename(columns=c_map, inplace=True)

            # Convert all to string
            for col in df.columns:
                df[col] = df[col].astype(str)

            # Extract postal codes from addresses if not already present
            if 'PostalCode' not in df.columns and 'Address' in df.columns:
                df['PostalCode'] = df['Address'].apply(
                    lambda x: extract_postal_code(x) or ''
                )

            self.df = df
            print(f"Loaded {len(df)} clinics from {self.data_path}")
            return True

        except Exception as e:
            print(f"Error loading clinic data: {e}")
            self.df = pd.DataFrame()
            return False

    def think(self, query: str) -> Optional[Dict]:
        """
        Analyze search intent using LLM.

        Args:
            query: User's natural language query

        Returns:
            Parsed intent as dict or None
        """
        system_prompt = """
        You are a clinic location search analyzer for Singapore.

        Task: Parse user query to extract location search parameters.

        Logic:
        1. If query contains postal code (6 digits), extract it to "postal_code"
        2. If query contains area name (Bedok, Tampines, etc.), extract to "area"
        3. If query mentions "nearest", "closest", "near", set "find_nearest": true
        4. If query contains clinic name, extract to "clinic_name"

        Singapore Areas: Bedok, Tampines, Yishun, Woodlands, Jurong West, Jurong East,
        Ang Mo Kio, Sengkang, Punggol, Serangoon, Hougang, Bukit Batok, Clementi,
        Toa Payoh, Bishan, Kallang, Pasir Ris, Sembawang, Choa Chu Kang, etc.

        Output JSON Format:
        {
            "intent": "find_clinic",
            "postal_code": "123456 or empty",
            "area": "area name or empty",
            "clinic_name": "specific clinic name or empty",
            "find_nearest": true/false,
            "reasoning": "brief explanation"
        }

        Examples:
        - "clinic nearest 641652" -> postal_code: "641652", find_nearest: true
        - "clinics in Bedok" -> area: "Bedok"
        - "find ABC clinic" -> clinic_name: "ABC"
        - "nearest clinic to Tampines" -> area: "Tampines", find_nearest: true
        """

        try:
            client = get_llm_client()
            response = client.chat.completions.create(
                model=get_default_model(),
                messages=[
                    {"role": "system", "content": system_prompt + "\n\nCRITICAL: Return ONLY valid JSON."},
                    {"role": "user", "content": query}
                ],
                temperature=0.1
            )
            content = response.choices[0].message.content.strip()

            # Extract JSON from potential code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            return json.loads(content)
        except Exception as e:
            print(f"Intent analysis failed: {e}")
            return None

    def search_by_postal(self, postal_code: str, top_k: int = 10) -> List[Dict]:
        """
        Search for nearest clinics to a postal code.

        Args:
            postal_code: 6-digit Singapore postal code
            top_k: Number of results to return

        Returns:
            List of clinic dicts with distance info
        """
        if self.df is None or self.df.empty:
            return []

        try:
            query_postal = int(postal_code)
        except ValueError:
            return []

        results = []
        for idx, row in self.df.iterrows():
            clinic_postal = row.get('PostalCode', '')
            if not clinic_postal:
                # Try extracting from address
                clinic_postal = extract_postal_code(row.get('Address', ''))

            if clinic_postal and clinic_postal.isdigit() and len(clinic_postal) == 6:
                distance = calculate_postal_distance(query_postal, int(clinic_postal))
                clinic_data = dict(row)
                clinic_data['_distance'] = distance
                results.append(clinic_data)

        # Sort by distance
        results.sort(key=lambda x: x['_distance'])
        return results[:top_k]

    def search_by_area(self, area: str, top_k: int = 15) -> List[Dict]:
        """
        Search for clinics in a specific area.

        Args:
            area: Area name (e.g., "Bedok", "Tampines")
            top_k: Number of results to return

        Returns:
            List of clinic dicts
        """
        if self.df is None or self.df.empty:
            return []

        results = []
        seen_clinics = set()  # Track seen clinics by unique key (name + address)
        area_lower = area.lower()

        def get_clinic_key(clinic_dict: Dict) -> str:
            """Generate unique key for clinic deduplication."""
            name = clinic_dict.get('Name', '').strip().lower()
            address = clinic_dict.get('Address', '').strip().lower()[:50]
            return f"{name}|{address}"

        def add_clinic(clinic_dict: Dict) -> bool:
            """Add clinic if not already seen. Returns True if added."""
            key = get_clinic_key(clinic_dict)
            if key not in seen_clinics:
                seen_clinics.add(key)
                results.append(clinic_dict)
                return True
            return False

        # Search in Area column first
        if 'Area' in self.df.columns:
            area_matches = self.df[self.df['Area'].str.lower().str.contains(area_lower, na=False)]
            for _, row in area_matches.iterrows():
                add_clinic(dict(row))

        # Also search in Address column
        if len(results) < top_k and 'Address' in self.df.columns:
            addr_matches = self.df[self.df['Address'].str.lower().str.contains(area_lower, na=False)]
            for _, row in addr_matches.iterrows():
                add_clinic(dict(row))

        # If not enough results, search nearby areas
        if len(results) < 5:
            nearby = get_nearby_areas(area)
            for nearby_area in nearby:
                if 'Area' in self.df.columns:
                    nearby_matches = self.df[self.df['Area'].str.lower().str.contains(nearby_area, na=False)]
                    for _, row in nearby_matches.iterrows():
                        row_dict = dict(row)
                        row_dict['_from_nearby'] = nearby_area.title()
                        add_clinic(row_dict)
                if len(results) >= top_k:
                    break

        return results[:top_k]

    def search_by_name(self, name: str, top_k: int = 5) -> List[Dict]:
        """
        Search for clinics by name using fuzzy matching.

        Args:
            name: Clinic name to search
            top_k: Number of results to return

        Returns:
            List of matching clinic dicts
        """
        if self.df is None or self.df.empty or 'Name' not in self.df.columns:
            return []

        names = self.df['Name'].tolist()
        matches = process.extract(name, names, limit=top_k, scorer=fuzz.token_set_ratio)

        results = []
        for matched_name, score, idx in matches:
            if score > 40:
                results.append(dict(self.df.iloc[idx]))

        return results

    def search(self, query: str) -> Tuple[List[Dict], Dict, Optional[str]]:
        """
        Perform intelligent clinic search based on query.

        Args:
            query: Natural language search query

        Returns:
            Tuple of (results list, parsed plan dict, map HTML or None)
        """
        if self.df is None or self.df.empty:
            return [], {"error": "Clinic database not loaded"}, None

        # Parse intent
        plan = self.think(query)
        if not plan:
            return [], {"error": "Failed to analyze query"}, None

        results = []
        map_html = None

        # Search based on intent
        postal_code = plan.get('postal_code', '').strip()
        area = plan.get('area', '').strip()
        clinic_name = plan.get('clinic_name', '').strip()
        find_nearest = plan.get('find_nearest', False)

        if postal_code and len(postal_code) == 6:
            # Postal code based search
            results = self.search_by_postal(postal_code)
            try:
                m = create_clinic_map(results, query_postal=postal_code)
                map_html = map_to_html(m)
            except Exception as e:
                print(f"Map generation error: {e}")

        elif area:
            # Area based search
            results = self.search_by_area(area)
            try:
                m = create_clinic_map(results, query_area=area)
                map_html = map_to_html(m)
            except Exception as e:
                print(f"Map generation error: {e}")

        elif clinic_name:
            # Name based search
            results = self.search_by_name(clinic_name)

        return results, plan, map_html

    def format_results(self, results: List[Dict], plan: Dict = None) -> str:
        """
        Format search results as Markdown.

        Args:
            results: List of clinic dicts
            plan: Optional parsed plan for context

        Returns:
            Formatted Markdown string
        """
        if not results:
            return "No clinics found matching your search."

        output = f"### Found {len(results)} Clinics\n\n"

        for i, clinic in enumerate(results):
            name = clinic.get('Name', 'Unknown')
            area = clinic.get('Area', '')
            address = clinic.get('Address', '')
            contact = clinic.get('Contact', '')
            distance = clinic.get('_distance')
            from_nearby = clinic.get('_from_nearby')

            # Clean address
            address_clean = re.sub(r'[\n\r\t]+', ' ', address).strip()

            output += f"#### {i+1}. {name}\n"
            if area:
                output += f"- **Area:** {area}"
                if from_nearby:
                    output += f" *(nearby: {from_nearby})*"
                output += "\n"
            if address_clean:
                output += f"- **Address:** {address_clean[:150]}{'...' if len(address_clean) > 150 else ''}\n"
            if contact:
                output += f"- **Contact:** {contact}\n"
            if distance is not None:
                output += f"- **Distance Score:** {distance:.0f}\n"
            output += "\n---\n"

        return output


# Singleton instance
_clinic_agent = None


def get_clinic_agent(data_path: str = None) -> ClinicSearchAgent:
    """Get or create the clinic search agent singleton."""
    global _clinic_agent
    if _clinic_agent is None or (data_path and data_path != _clinic_agent.data_path):
        _clinic_agent = ClinicSearchAgent(data_path)
    return _clinic_agent
