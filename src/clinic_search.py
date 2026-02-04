"""
Clinic search agent for finding nearby clinics in Singapore.
Supports postal code-based and area-based search with distance calculation.
"""
import json
import os
import re
from typing import Dict, List, Optional, Tuple

import pandas as pd
from rapidfuzz import fuzz, process

from .config import PROJECT_ROOT
from .llm import get_default_model, get_llm_client
from .location import (
    calculate_postal_distance,
    create_clinic_map,
    extract_postal_code,
    get_nearby_areas,
    map_to_html,
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
        """Load and standardize clinic data."""
        if not os.path.exists(self.data_path):
            print(f"Clinic data file not found: {self.data_path}")
            return False

        try:
            df = pd.read_csv(self.data_path) if self.data_path.endswith('.csv') else pd.read_excel(self.data_path)
            df = df.fillna('')

            # Column name mappings: (keywords to check, standard name)
            column_mappings = [
                (['gp clinic name', 'clinic name', 'name'], 'Name'),
                (['clinic address', 'address'], 'Address'),
                (['area'], 'Area'),
                (['contact', 'phone', 'tel'], 'Contact'),
                (['postal'], 'PostalCode'),
            ]

            rename_map = {}
            for col in df.columns:
                col_lower = col.lower()
                for keywords, standard_name in column_mappings:
                    if any(kw in col_lower for kw in keywords):
                        rename_map[col] = standard_name
                        break

            if rename_map:
                df.rename(columns=rename_map, inplace=True)

            # Convert all columns to string
            for col in df.columns:
                df[col] = df[col].astype(str)

            # Extract postal codes from addresses if not already present
            if 'PostalCode' not in df.columns and 'Address' in df.columns:
                df['PostalCode'] = df['Address'].apply(lambda x: extract_postal_code(x) or '')

            self.df = df
            print(f"Loaded {len(df)} clinics from {self.data_path}")
            return True

        except Exception as e:
            print(f"Error loading clinic data: {e}")
            self.df = pd.DataFrame()
            return False

    def think(self, query: str) -> Optional[Dict]:
        """Analyze search intent using LLM."""
        system_prompt = """You are a clinic location search analyzer for Singapore.

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

CRITICAL: Return ONLY valid JSON."""

        try:
            client = get_llm_client()
            response = client.chat.completions.create(
                model=get_default_model(),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ]
            )
            content = response.choices[0].message.content.strip()
            return json.loads(self._extract_json(content))
        except Exception as e:
            print(f"Intent analysis failed: {e}")
            return None

    def _extract_json(self, content: str) -> str:
        """Extract JSON from LLM response, handling code blocks."""
        if "```json" in content:
            return content.split("```json")[1].split("```")[0].strip()
        if "```" in content:
            return content.split("```")[1].split("```")[0].strip()
        return content

    def search_by_postal(self, postal_code: str, top_k: int = 10) -> List[Dict]:
        """Search for nearest clinics to a postal code."""
        if self.df is None or self.df.empty:
            return []

        if not postal_code.isdigit():
            return []

        query_postal = int(postal_code)
        results = []

        for _, row in self.df.iterrows():
            clinic_postal = row.get('PostalCode', '') or extract_postal_code(row.get('Address', ''))

            if clinic_postal and clinic_postal.isdigit() and len(clinic_postal) == 6:
                clinic_data = dict(row)
                clinic_data['_distance'] = calculate_postal_distance(query_postal, int(clinic_postal))
                results.append(clinic_data)

        results.sort(key=lambda x: x['_distance'])
        return results[:top_k]

    def search_by_area(self, area: str, top_k: int = 15) -> List[Dict]:
        """Search for clinics in a specific area."""
        if self.df is None or self.df.empty:
            return []

        results = []
        seen_keys = set()
        area_lower = area.lower()

        def add_clinic(clinic_dict: Dict) -> bool:
            """Add clinic if not already seen."""
            key = f"{clinic_dict.get('Name', '').strip().lower()}|{clinic_dict.get('Address', '').strip().lower()[:50]}"
            if key in seen_keys:
                return False
            seen_keys.add(key)
            results.append(clinic_dict)
            return True

        def search_column(column: str, search_term: str) -> None:
            """Search a column for matching clinics."""
            if column not in self.df.columns:
                return
            matches = self.df[self.df[column].str.lower().str.contains(search_term, na=False)]
            for _, row in matches.iterrows():
                add_clinic(dict(row))

        # Search in Area and Address columns
        search_column('Area', area_lower)
        if len(results) < top_k:
            search_column('Address', area_lower)

        # Search nearby areas if not enough results
        if len(results) < 5:
            for nearby_area in get_nearby_areas(area):
                if len(results) >= top_k:
                    break
                if 'Area' not in self.df.columns:
                    continue
                matches = self.df[self.df['Area'].str.lower().str.contains(nearby_area, na=False)]
                for _, row in matches.iterrows():
                    row_dict = dict(row)
                    row_dict['_from_nearby'] = nearby_area.title()
                    add_clinic(row_dict)

        return results[:top_k]

    def search_by_name(self, name: str, top_k: int = 5) -> List[Dict]:
        """Search for clinics by name using fuzzy matching."""
        if self.df is None or self.df.empty or 'Name' not in self.df.columns:
            return []

        matches = process.extract(name, self.df['Name'].tolist(), limit=top_k, scorer=fuzz.token_set_ratio)
        return [dict(self.df.iloc[idx]) for _, score, idx in matches if score > 40]

    def search(self, query: str) -> Tuple[List[Dict], Dict, Optional[str]]:
        """Perform intelligent clinic search based on query."""
        if self.df is None or self.df.empty:
            return [], {"error": "Clinic database not loaded"}, None

        plan = self.think(query)
        if not plan:
            return [], {"error": "Failed to analyze query"}, None

        postal_code = plan.get('postal_code', '').strip()
        area = plan.get('area', '').strip()
        clinic_name = plan.get('clinic_name', '').strip()

        # Determine search type and execute
        if postal_code and len(postal_code) == 6:
            results = self.search_by_postal(postal_code)
            map_html = self._generate_map(results, query_postal=postal_code)
        elif area:
            results = self.search_by_area(area)
            map_html = self._generate_map(results, query_area=area)
        elif clinic_name:
            results = self.search_by_name(clinic_name)
            map_html = None
        else:
            results = []
            map_html = None

        return results, plan, map_html

    def _generate_map(self, results: List[Dict], query_postal: str = None, query_area: str = None) -> Optional[str]:
        """Generate map HTML from search results."""
        try:
            m = create_clinic_map(results, query_postal=query_postal, query_area=query_area)
            return map_to_html(m)
        except Exception as e:
            print(f"Map generation error: {e}")
            return None

    def format_results(self, results: List[Dict], plan: Dict = None) -> str:
        """Format search results as Markdown."""
        if not results:
            return "No clinics found matching your search."

        lines = [f"### Found {len(results)} Clinics\n"]

        for i, clinic in enumerate(results, 1):
            name = clinic.get('Name', 'Unknown')
            area = clinic.get('Area', '')
            address = re.sub(r'[\n\r\t]+', ' ', clinic.get('Address', '')).strip()
            contact = clinic.get('Contact', '')
            distance = clinic.get('_distance')
            from_nearby = clinic.get('_from_nearby')

            lines.append(f"#### {i}. {name}")

            if area:
                area_text = f"- **Area:** {area}"
                if from_nearby:
                    area_text += f" *(nearby: {from_nearby})*"
                lines.append(area_text)

            if address:
                truncated = address[:150] + '...' if len(address) > 150 else address
                lines.append(f"- **Address:** {truncated}")

            if contact:
                lines.append(f"- **Contact:** {contact}")

            if distance is not None:
                lines.append(f"- **Distance Score:** {distance:.0f}")

            lines.append("\n---")

        return "\n".join(lines)


# Singleton instance
_clinic_agent = None


def get_clinic_agent(data_path: str = None) -> ClinicSearchAgent:
    """Get or create the clinic search agent singleton."""
    global _clinic_agent
    if _clinic_agent is None or (data_path and data_path != _clinic_agent.data_path):
        _clinic_agent = ClinicSearchAgent(data_path)
    return _clinic_agent
