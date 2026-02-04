"""Medical search agent for finding doctors and specialists."""
import json
import os
from typing import Optional, Dict

import pandas as pd
from rapidfuzz import fuzz, process

from .config import PROJECT_ROOT
from .llm import get_response

class MedicalSearchAgent:
    """Agent for searching doctors and specialists."""

    def __init__(self, data_path: str = None):
        self.data_path = data_path or os.path.join(PROJECT_ROOT, "Specialists.xlsx")
        self.df = None
        self.load_data()

    def load_data(self) -> None:
        """Load and standardize doctor data from Specialists.xlsx."""
        try:
            df = pd.read_excel(self.data_path)
            df = df.fillna('')

            # Column name mappings: (keywords to check, standard name)
            column_mappings = [
                (['doctor name', 'name'], 'Name'),
                (['specialty'], 'Specialty'),
                (['languages spoken', 'language'], 'Languages'),
                (['services'], 'Services'),
                (['qualifications'], 'Qualifications'),
                (['designation'], 'Designation'),
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

            for col in df.columns:
                df[col] = df[col].astype(str)

            self.df = df
        except Exception as e:
            print(f"Error loading doctor data: {e}")
            self.df = pd.DataFrame()

    def think(self, query: str) -> Optional[Dict]:
        """Analyze search intent using LLM."""
        system_prompt = """You are a medical search intent analyzer.
Target Data: Doctors (Fields: Name, Specialty, Languages, Services)

Task: Parse user query into a JSON object.

Logic for parsing:
1. NAME DETECTION: If query contains "find dr. [name]", "doctor [name]", or specific names, extract to "keywords" and leave "Specialty" EMPTY.
2. Language extraction: "Chinese", "Mandarin", "English" etc. -> "Languages" field
3. SPECIALTY FROM SYMPTOMS (use EXACT names):
  - fever/cold/flu/general illness/sick -> "General Medicine"
  - baby/kid/child/infant -> "Family & Community Medicine"
  - emergency/urgent/serious -> "Emergency Medicine"
  - heart/chest pain/cardiac -> "Cardiology"
  - stomach/gut/digestive -> "Gastroenterology"
  - bone/fracture/injury -> "Orthopaedic Surgery"
  - eye/vision -> "Ophthalmology"
  - throat/ear/nose -> "Otolaryngology"
  - mental/depression/anxiety -> "Psychiatry"
  - tooth/teeth/dentist -> "Dental"
  - diabetes/sugar -> "Endocrinology"
  - kidney/renal -> "Renal Medicine"
  - urine/bladder -> "Urology"
  - breathing/lung -> "Respiratory Medicine"
  - Default: "General Medicine" for common symptoms

Output JSON Format:
{
    "intent": "find_doctor",
    "keywords": "Specific name of person (leave empty if general search)",
    "filters": {"Specialty": "...", "Languages": "..."},
    "reasoning": "Brief explanation of inference"
}

CRITICAL: Return ONLY a valid JSON object."""

        try:
            # Use temperature=0 for deterministic JSON output
            # Falls back to default if model doesn't support temperature
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
            content = get_response(messages, temperature=0)
            return json.loads(self._extract_json(content.strip()))
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

    def search(self, query: str) -> str:
        """Perform search based on LLM intent analysis."""
        if self.df is None or self.df.empty:
            return "Knowledge base not loaded."

        plan = self.think(query)
        if not plan:
            return "Failed to analyze search intent."

        filtered_df = self._apply_filters(plan.get('filters', {}))
        results = self._find_matches(filtered_df, plan.get('keywords', ''))

        if not results:
            return "No matching doctors found."

        return self._format_results(results)

    def _apply_filters(self, filters: dict) -> pd.DataFrame:
        """Apply specialty and language filters to the dataframe."""
        df = self.df.copy()

        # Apply Specialty filter
        if filters.get('Specialty'):
            specialty_corrections = {
                'GP': 'General Medicine',
                'General Practitioner': 'General Medicine',
                'Family Medicine': 'Family & Community Medicine'
            }
            spec = specialty_corrections.get(filters['Specialty'], filters['Specialty'])

            mask = pd.Series([False] * len(df))
            for col in ['Specialty', 'Designation', 'Services']:
                if col in df.columns:
                    mask |= df[col].str.contains(spec, case=False, na=False)
            df = df[mask]

        # Apply Language filter
        if filters.get('Languages') and 'Languages' in df.columns:
            lang = filters['Languages']
            if lang.lower() in ['chinese', 'mandarin']:
                lang = 'Mandarin'
            df = df[df['Languages'].str.contains(lang, case=False, na=False)]

        return df

    def _find_matches(self, df: pd.DataFrame, keywords: str) -> list:
        """Find matching doctors using fuzzy name matching or top results."""
        if df.empty:
            return []

        if keywords and len(keywords) > 1:
            matches = process.extract(keywords, df['Name'].tolist(), limit=5, scorer=fuzz.token_set_ratio)
            return [df.iloc[idx] for _, score, idx in matches if score > 40]

        return [row for _, row in df.head(5).iterrows()]

    def _format_results(self, results: list) -> str:
        """Format search results as Markdown."""
        lines = [f"### Found {len(results)} Matching Doctors\n"]

        for i, row in enumerate(results, 1):
            lines.append(f"#### {i}. {row['Name']}")
            lines.append(f"- **Specialty:** {row.get('Specialty', 'N/A')}")
            lines.append(f"- **Languages:** {row.get('Languages', 'N/A')}")

            if 'Designation' in row:
                lines.append(f"- **Designation:** {row['Designation']}")

            if 'Services' in row:
                services = row['Services']
                truncated = services[:200] + "..." if len(services) > 200 else services
                lines.append(f"- **Services:** {truncated}")

            lines.append("\n---")

        return "\n".join(lines)
