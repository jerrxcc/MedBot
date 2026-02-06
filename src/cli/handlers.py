"""
Feature handlers for routing queries to appropriate MedBot functionality.
"""

import sys
from typing import Optional
import re

from ..retriever import retrieve_with_fallback, format_context
from ..llm import (
    get_response_stream,
    build_messages,
    rewrite_query_with_context,
    APIKeyMissingError,
    APICallError,
)
from ..prompts import get_prompt
from ..search_agent import MedicalSearchAgent
from ..clinic_search import ClinicSearchAgent


class FeatureHandler:
    """
    Handles routing and execution of different MedBot features.
    """

    # Collection names for RAG features
    COLLECTIONS = {
        'symptoms': 'medquad_symptoms',
        'medication': 'fda_drugs',
    }

    def __init__(self):
        """Initialize feature handler."""
        self.doctor_agent = None
        self.clinic_agent = None

    def handle(self, query: str, intent: str, history: list) -> tuple[str, bool]:
        """
        Route query to appropriate handler based on intent.

        Args:
            query: User query
            intent: Detected intent
            history: Conversation history

        Returns:
            Tuple of (response string, already_streamed flag).
            When already_streamed is True, the response was already
            printed to stdout token-by-token.

        Raises:
            APIKeyMissingError: If API key is not configured
            APICallError: If API call fails
        """
        if intent in ['doctors', 'clinics']:
            return self._handle_search(query, intent), False
        return self._handle_rag(query, intent, history), True

    def _handle_rag(self, query: str, feature: str, history: list) -> str:
        """
        Handle RAG-based queries (symptoms, medication).

        Args:
            query: User query
            feature: Feature type
            history: Conversation history

        Returns:
            Response string
        """
        search_query = query
        if history:
            search_query = rewrite_query_with_context(query, history)
            if search_query != query:
                print(f"[Rewritten query: {search_query}]")

        # Retrieve relevant documents
        collection = self.COLLECTIONS[feature]
        results = {
            "documents": [],
            "metadatas": [],
            "distances": [],
            "confidence_score": None,
            "confidence_level": "none",
            "fallback_used": False,
        }

        # Skip retrieval for unspecified dosage questions in both symptoms and medication modes
        # since neither collection will have useful info without a specific medication name
        skip_retrieval = feature in ("symptoms", "medication") and _is_unspecified_dosage_question(query)
        if not skip_retrieval:
            print(f"Searching {feature} knowledge base...")
            results = retrieve_with_fallback(search_query, collection, top_k=5)

        # Show confidence warning
        confidence = results.get('confidence_level', 'low')
        if confidence == 'low':
            print(f"⚠️  Low confidence match - results may not be directly relevant\n")
        elif confidence == 'medium':
            print(f"ℹ️  Medium confidence - review results carefully\n")

        # Format context
        context = format_context(results)

        # Get system prompt
        system_prompt = get_prompt(feature)
        confidence_level = results.get("confidence_level", "none")
        if confidence_level in ["low", "very_low", "none"]:
            system_prompt += (
                "\n\n## Retrieval Confidence\n"
                "The retrieved context may be weak or partially irrelevant. "
                "Avoid over-specific claims and ask one clarifying question. "
                "If context seems unrelated, say so briefly and answer more generally. "
                "Keep the response brief (about 100–150 words) unless the user asks for more."
            )

        # Build messages and get response
        messages = build_messages(
            system_prompt=system_prompt,
            user_message=query,
            context=context,
            history=history
        )

        response = ""
        for token in get_response_stream(messages):
            sys.stdout.write(token)
            sys.stdout.flush()
            response += token
        sys.stdout.write("\n")

        # Add metadata info
        metadata_lines = []
        if results.get('fallback_used'):
            metadata_lines.append(f"[Used fallback collection: {results.get('collection')}]")
        if results.get('confidence_score'):
            metadata_lines.append(f"[Confidence: {int(results['confidence_score'] * 100)}%]")

        if metadata_lines:
            # Mirror how chat clients behave: stream the answer first, then print
            # a short postamble (citations/metadata) once generation finishes.
            sys.stdout.write("\n" + "\n".join(metadata_lines) + "\n")
            sys.stdout.flush()
            response += "\n\n" + "\n".join(metadata_lines)

        return response


    def _handle_search(self, query: str, search_type: str) -> str:
        """
        Handle search-based queries (doctors, clinics).

        Args:
            query: User query
            search_type: 'doctors' or 'clinics'

        Returns:
            Response string

        Raises:
            APIKeyMissingError: If API key is not configured
            APICallError: If API call fails
        """
        try:
            if search_type == 'doctors':
                return self._handle_doctor_search(query)
            return self._handle_clinic_search(query)
        except (APIKeyMissingError, APICallError):
            # Let API errors propagate for consistent handling in REPL
            raise
        except Exception as e:
            # Catch other errors (file not found, data errors, etc.)
            return f"Search error: {str(e)}"

    def _handle_doctor_search(self, query: str) -> str:
        """
        Handle doctor search using MedicalSearchAgent.

        Args:
            query: User query

        Returns:
            Formatted search results
        """
        # Lazy load doctor agent
        if self.doctor_agent is None:
            print("Loading doctor database...")
            self.doctor_agent = MedicalSearchAgent()

        print("Searching for doctors...")
        return self.doctor_agent.search(query)

    def _handle_clinic_search(self, query: str) -> str:
        """
        Handle clinic search using ClinicSearchAgent.

        Args:
            query: User query

        Returns:
            Formatted search results
        """
        # Lazy load clinic agent
        if self.clinic_agent is None:
            print("Loading clinic database...")
            self.clinic_agent = ClinicSearchAgent()

        print("Searching for clinics...")
        results, metadata = self.clinic_agent.search(query)

        if not results:
            if metadata.get('error'):
                return metadata['error']
            return "No clinics found matching your criteria."

        # Format results
        lines = [f"Found {len(results)} clinics:\n"]

        for i, clinic in enumerate(results, 1):
            lines.append(f"{i}. {clinic.get('Name', 'Unknown Clinic')}")

            # Add location info
            if clinic.get('Postal Code'):
                lines.append(f"   Postal: {clinic['Postal Code']}")
            if clinic.get('distance_km'):
                lines.append(f"   Distance: {clinic['distance_km']:.2f} km")

            # Add address
            if clinic.get('Address'):
                lines.append(f"   Address: {clinic['Address']}")

            # Add phone
            if clinic.get('Phone'):
                lines.append(f"   Phone: {clinic['Phone']}")

            lines.append("")  # Blank line

        # Add search metadata
        if metadata.get('postal_code'):
            lines.append(f"\nSearch center: Postal {metadata['postal_code']}")
        elif metadata.get('area'):
            lines.append(f"\nSearch area: {metadata['area']}")
        if metadata.get('postal_code') or metadata.get('area'):
            lines.append("")

        return "\n".join(lines)


def _is_unspecified_dosage_question(query: str) -> bool:
    """Detect dosage questions without a specific medication name."""
    q = query.lower()
    dosage_terms = [r"\bdosage\b", r"\bdose\b", r"\bmg\b", r"\bmilligram"]
    if not any(re.search(pat, q) for pat in dosage_terms):
        return False

    medication_terms = [
        "ibuprofen", "paracetamol", "acetaminophen", "aspirin", "naproxen",
        "tylenol", "advil", "motrin", "amoxicillin", "doxycycline",
        "antibiotic", "antibiotics", "cetirizine", "loratadine",
        "diphenhydramine", "dextromethorphan", "guaifenesin"
    ]
    return not any(term in q for term in medication_terms)
