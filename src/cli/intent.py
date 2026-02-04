"""
Intent detection for routing queries to appropriate handlers.
"""

from typing import Optional
import re


class IntentDetector:
    """
    Detects user intent using keyword-based matching.
    Fast and deterministic without requiring LLM calls.
    """

    # Keywords for each feature (English + Chinese)
    KEYWORDS = {
        'symptoms': [
            # English symptoms
            'symptom', 'pain', 'ache', 'hurt', 'sore', 'fever', 'cough',
            'headache', 'dizzy', 'nausea', 'vomit', 'tired', 'fatigue',
            'rash', 'itch', 'swelling', 'bleeding', 'discharge', 'lump',
            'shortness of breath', 'chest pain', 'abdominal', 'stomach',
            'feel', 'feeling', 'experiencing',
            # Chinese symptoms
            '症状', '疼痛', '发烧', '咳嗽', '头痛', '恶心', '呕吐',
            '疲劳', '皮疹', '肿胀', '出血', '胸痛', '腹痛', '胃痛',
        ],
        'medication': [
            # English medication
            'medicine', 'medication', 'drug', 'pill', 'tablet', 'dose', 'dosage',
            'prescription', 'side effect', 'interact', 'how to take',
            'contraindication', 'overdose', 'painkiller', 'antibiotic',
            'aspirin', 'ibuprofen', 'paracetamol', 'acetaminophen',
            'amoxicillin', 'metformin', 'lisinopril', 'atorvastatin',
            # Chinese medication
            '药', '药物', '处方', '剂量', '副作用', '服用', '止痛药', '抗生素',
            '阿司匹林', '布洛芬', '扑热息痛',
        ],
        'records': [
            # English records
            'record', 'history', 'diagnosis', 'treatment', 'condition',
            'disease', 'disorder', 'syndrome', 'medical history',
            'past', 'previously', 'diagnosed with',
            'diabetes', 'hypertension', 'asthma', 'arthritis', 'cancer',
            'what is', 'tell me about', 'information about',
            # Chinese records
            '病历', '诊断', '治疗', '疾病', '病史', '糖尿病', '高血压', '哮喘',
        ],
        'doctors': [
            # English doctor search
            'doctor', 'physician', 'specialist', 'dentist', 'surgeon',
            'cardiologist', 'dermatologist', 'neurologist', 'oncologist',
            'pediatrician', 'psychiatrist', 'orthopedic', 'gynecologist',
            'find a doctor', 'see a doctor', 'looking for doctor',
            'find doctor', 'search doctor', 'need doctor',
            'appointment', 'consultation', 'practitioner',
            # Chinese doctor search
            '医生', '医师', '专家', '牙医', '外科医生', '心脏科', '皮肤科',
            '找医生', '看医生', '预约', '咨询',
        ],
        'clinics': [
            # English clinic search
            'clinic', 'hospital', 'medical center', 'healthcare facility',
            'near', 'nearby', 'location', 'address', 'postal code',
            'find a clinic', 'closest clinic',
            # Chinese clinic search
            '诊所', '医院', '医疗中心', '附近', '位置', '邮编', '找诊所',
        ],
    }

    def __init__(self):
        """Initialize intent detector."""
        # Pre-compile regex patterns for efficiency
        self.patterns = {}
        for intent, keywords in self.KEYWORDS.items():
            # Create word boundary pattern for each keyword
            pattern = '|'.join(re.escape(kw) for kw in keywords)
            self.patterns[intent] = re.compile(
                rf'\b({pattern})\b',
                re.IGNORECASE
            )

    def detect(self, query: str, mode: Optional[str] = None) -> str:
        """
        Detect intent from user query.

        Args:
            query: User query string
            mode: Optional forced mode (e.g., from /mode command)

        Returns:
            Detected intent: 'symptoms', 'medication', 'records', 'doctors', 'clinics'
        """
        # If mode is forced, use it
        if mode and mode in self.KEYWORDS:
            return mode

        query_lower = query.lower()

        # Priority rules for specific patterns
        # Rule 1: Explicit search phrases for doctors/clinics
        # Must include healthcare provider terms to avoid false positives like "find a cure"
        healthcare_providers = [
            'doctor', 'physician', 'specialist', 'dentist', 'surgeon',
            'cardiologist', 'dermatologist', 'neurologist', 'pediatrician',
            'psychiatrist', 'gynecologist', 'practitioner', 'gp',
            'clinic', 'hospital', 'medical center',
            '医生', '医师', '专家', '牙医', '诊所', '医院',
        ]
        search_phrases = ['find a', 'find', 'looking for', 'search for', 'need a', 'recommend', '找', '搜索']
        has_search_phrase = any(phrase in query_lower for phrase in search_phrases)
        has_provider = any(provider in query_lower for provider in healthcare_providers)

        if has_search_phrase and has_provider:
            # Check for clinic/hospital terms (including "medical center")
            clinic_terms = ['clinic', 'hospital', 'medical center', '诊所', '医院']
            if any(term in query_lower for term in clinic_terms):
                return 'clinics'
            else:
                return 'doctors'

        # Rule 2: Location-based queries are clinic searches
        if any(phrase in query_lower for phrase in ['near', 'nearby', 'postal', 'location', 'address']):
            return 'clinics'

        # Rule 3: Side effects queries are medication
        if 'side effect' in query_lower or 'interact' in query_lower:
            return 'medication'

        # Count matches for each intent
        scores = {}
        for intent, pattern in self.patterns.items():
            matches = pattern.findall(query)
            scores[intent] = len(matches)

        # Apply priority weights
        # Doctors and clinics get higher weight if they have any match
        if scores.get('doctors', 0) > 0:
            scores['doctors'] *= 1.5
        if scores.get('clinics', 0) > 0:
            scores['clinics'] *= 1.5
        if scores.get('medication', 0) > 0:
            scores['medication'] *= 1.3

        # Return intent with highest score
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)

        # Default to symptoms for medical queries
        # (most common use case)
        return 'symptoms'

    def get_confidence(self, query: str, intent: str) -> float:
        """
        Get confidence score for detected intent.

        Args:
            query: User query string
            intent: Detected intent

        Returns:
            Confidence score between 0.0 and 1.0
        """
        if intent not in self.patterns:
            return 0.0

        matches = self.patterns[intent].findall(query)
        if not matches:
            return 0.0

        # Calculate confidence based on:
        # 1. Number of keyword matches
        # 2. Length of query (more keywords in short query = higher confidence)
        words = query.split()
        if not words:
            return 0.0

        match_ratio = len(matches) / len(words)
        # Scale to 0.5-1.0 range (we already have a match)
        confidence = 0.5 + (match_ratio * 0.5)

        return min(confidence, 1.0)
