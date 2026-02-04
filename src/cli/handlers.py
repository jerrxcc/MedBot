"""
Feature handlers for routing queries to appropriate MedBot functionality.
"""

from typing import Optional

from ..retriever import retrieve_with_fallback, format_context
from ..llm import (
    get_response,
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
        'records': 'medical_records',
    }

    def __init__(self):
        """Initialize feature handler."""
        self.doctor_agent = None
        self.clinic_agent = None

    def handle(self, query: str, intent: str, history: list) -> str:
        """
        Route query to appropriate handler based on intent.

        Args:
            query: User query
            intent: Detected intent
            history: Conversation history

        Returns:
            Response string

        Raises:
            APIKeyMissingError: If API key is not configured
            APICallError: If API call fails
        """
        if intent in ['doctors', 'clinics']:
            return self._handle_search(query, intent)
        return self._handle_rag(query, intent, history)

    def _handle_rag(self, query: str, feature: str, history: list) -> str:
        """
        Handle RAG-based queries (symptoms, medication, records).

        Args:
            query: User query
            feature: Feature type
            history: Conversation history

        Returns:
            Response string
        """
        # Rewrite query with context for follow-ups
        search_query = query
        if history:
            search_query = rewrite_query_with_context(query, history)
            if search_query != query:
                print(f"[Rewritten query: {search_query}]")

        # Retrieve relevant documents
        collection = self.COLLECTIONS[feature]
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

        # Build messages and get response
        messages = build_messages(
            system_prompt=system_prompt,
            user_message=query,
            context=context,
            history=history
        )

        response = get_response(messages)

        # Add metadata info
        metadata_lines = []
        if results.get('fallback_used'):
            metadata_lines.append(f"[Used fallback collection: {results.get('collection')}]")
        if results.get('confidence_score'):
            metadata_lines.append(f"[Confidence: {int(results['confidence_score'] * 100)}%]")

        if metadata_lines:
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
        results, metadata, html_path = self.clinic_agent.search(query)

        if not results:
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

        # Add map info if available
        if html_path:
            lines.append(f"📍 Map saved to: {html_path}")

        # Add search metadata
        if metadata.get('postal_code'):
            lines.append(f"\nSearch center: Postal {metadata['postal_code']}")
        elif metadata.get('area'):
            lines.append(f"\nSearch area: {metadata['area']}")

        return "\n".join(lines)
