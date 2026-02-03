import pandas as pd
import json
import os
from rapidfuzz import process, fuzz
from .llm import get_response, build_messages, _get_client
from .config import PROJECT_ROOT

class MedicalSearchAgent:
    def __init__(self, data_path=None):
        self.data_path = data_path or os.path.join(PROJECT_ROOT, "Specialists.xlsx")
        self.df = None
        self.load_data()

    def load_data(self):
        """Load and standardize doctor data from Specialists.xlsx"""
        try:
            df = pd.read_excel(self.data_path)
            df = df.fillna('')
            
            # Map column names to standard keys
            d_map = {}
            for col in df.columns:
                cl = col.lower()
                if 'doctor name' in cl or 'name' in cl: d_map[col] = 'Name'
                elif 'specialty' in cl: d_map[col] = 'Specialty'
                elif 'languages spoken' in cl or 'language' in cl: d_map[col] = 'Languages'
                elif 'services' in cl: d_map[col] = 'Services'
                elif 'qualifications' in cl: d_map[col] = 'Qualifications'
                elif 'designation' in cl: d_map[col] = 'Designation'
            
            if d_map:
                df.rename(columns=d_map, inplace=True)
            
            # Convert all columns to string for easier searching
            for col in df.columns:
                df[col] = df[col].astype(str)
            
            self.df = df
        except Exception as e:
            print(f"Error loading doctor data: {e}")
            self.df = pd.DataFrame()

    def think(self, query):
        """Analyze search intent using LLM"""
        system_prompt = """
        You are a medical search intent analyzer.
        Target Data: Doctors (Fields: Name, Specialty, Languages, Services)

        Task: Parse user query into a JSON object.
       
        Logic for parsing:
        1. ***NAME DETECTION***: If query contains patterns like "find dr. [name]", "doctor [name]", or specific names, extract to "keywords" field and leave "Specialty" EMPTY.
        2. Language extraction: "Chinese", "Mandarin", "English" etc. -> "Languages" field  
        3. ***SPECIALTY FROM SYMPTOMS***: ONLY use these EXACT names that exist in database:
          - "fever/cold/flu/general illness/sick" -> "General Medicine"
          - "baby/kid/child/infant" -> "Family & Community Medicine"
          - "emergency/urgent/serious" -> "Emergency Medicine"
          - "heart/chest pain/cardiac" -> "Cardiology"
          - "stomach/gut/digestive" -> "Gastroenterology"
          - "bone/fracture/injury" -> "Orthopaedic Surgery"
          - "eye/vision" -> "Ophthalmology"
          - "throat/ear/nose" -> "Otolaryngology"
          - "mental/depression/anxiety" -> "Psychiatry"
          - "tooth/teeth/dentist" -> "Dental"
          - "diabetes/sugar" -> "Endocrinology"
          - "kidney/renal" -> "Renal Medicine"
          - "urine/bladder" -> "Urology"
          - "breathing/lung" -> "Respiratory Medicine"
          - Default: "General Medicine" for common symptoms
       
        Output JSON Format:
        {
            "intent": "find_doctor",
            "keywords": "Specific name of person (leave empty if general search)",
            "filters": {
                "Specialty": "...",
                "Languages": "..."
            },
            "reasoning": "Brief explanation of inference"
        }
        """

        try:
            client = _get_client()
            response = client.chat.completions.create(
                model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                messages=[
                    {"role": "system", "content": system_prompt + "\n\nCRITICAL: Return ONLY a valid JSON object. No other text, no markdown code blocks."},
                    {"role": "user", "content": query}
                ],
                temperature=0.1
            )
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from potential code blocks
            if content.startswith("```json"):
                content = content.split("```json")[-1].split("```")[0].strip()
            elif content.startswith("```"):
                content = content.split("```")[-1].split("```")[0].strip()
            
            return json.loads(content)
        except Exception as e:
            print(f"Intent analysis failed: {e}")
            print(f"Raw content: {content if 'content' in locals() else 'N/A'}")
            return None

    def search(self, query):
        """Perform search based on LLM intent analysis"""
        if self.df is None or self.df.empty:
            return "Knowledge base not loaded."

        plan = self.think(query)
        if not plan:
            return "Failed to analyze search intent."

        filters = plan.get('filters', {})
        keywords = plan.get('keywords', '')
        
        filtered_df = self.df.copy()

        # Apply Specialty filter
        if filters.get('Specialty'):
            spec = filters['Specialty']
            # Simple corrections
            spec_map = {
                'GP': 'General Medicine',
                'General Practitioner': 'General Medicine',
                'Family Medicine': 'Family & Community Medicine'
            }
            spec = spec_map.get(spec, spec)
            
            mask = pd.Series([False] * len(filtered_df))
            for col in ['Specialty', 'Designation', 'Services']:
                if col in filtered_df.columns:
                    mask |= filtered_df[col].str.contains(spec, case=False, na=False)
            filtered_df = filtered_df[mask]

        # Apply Language filter
        if filters.get('Languages'):
            lang = filters['Languages']
            if lang.lower() in ['chinese', 'mandarin']: lang = 'Mandarin'
            if 'Languages' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['Languages'].str.contains(lang, case=False, na=False)]

        # Fuzzy matching for names
        results = []
        if not filtered_df.empty:
            if keywords and len(keywords) > 1:
                names = filtered_df['Name'].tolist()
                matches = process.extract(keywords, names, limit=5, scorer=fuzz.token_set_ratio)
                
                for name, score, idx in matches:
                    if score > 40:
                        results.append(filtered_df.iloc[idx])
            else:
                # Top results for general specialty search
                results = [row for _, row in filtered_df.head(5).iterrows()]

        if not results:
            return "No matching doctors found."

        # Format results as Markdown
        formatted_output = f"### Found {len(results)} Matching Doctors\n\n"
        for i, row in enumerate(results):
            formatted_output += f"#### {i+1}. {row['Name']}\n"
            formatted_output += f"- **Specialty:** {row.get('Specialty', 'N/A')}\n"
            formatted_output += f"- **Languages:** {row.get('Languages', 'N/A')}\n"
            if 'Designation' in row:
                formatted_output += f"- **Designation:** {row['Designation']}\n"
            if 'Services' in row:
                services = row['Services'][:200] + "..." if len(row['Services']) > 200 else row['Services']
                formatted_output += f"- **Services:** {services}\n"
            formatted_output += "\n---\n"
        
        return formatted_output
