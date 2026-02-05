"""
Location utilities for Singapore clinic search.
Provides postal code distance calculation and nearby-area lookup.
"""
import re
from typing import List, Optional


# Singapore nearby areas mapping for fallback search
NEARBY_AREAS = {
    'bedok': ['tampines', 'pasir ris', 'changi', 'geylang'],
    'tampines': ['bedok', 'pasir ris', 'sengkang', 'changi'],
    'yishun': ['woodlands', 'sembawang', 'ang mo kio'],
    'woodlands': ['yishun', 'sembawang', 'choa chu kang'],
    'jurong west': ['jurong east', 'choa chu kang', 'bukit batok'],
    'jurong east': ['jurong west', 'clementi', 'bukit batok'],
    'sengkang': ['punggol', 'tampines', 'serangoon', 'hougang'],
    'punggol': ['sengkang', 'tampines', 'serangoon'],
    'ang mo kio': ['yishun', 'serangoon', 'bishan', 'toa payoh'],
    'serangoon': ['ang mo kio', 'sengkang', 'bishan', 'hougang'],
    'hougang': ['sengkang', 'serangoon', 'ang mo kio'],
    'bukit batok': ['jurong east', 'jurong west', 'choa chu kang', 'clementi'],
    'clementi': ['jurong east', 'bukit batok', 'queenstown'],
    'toa payoh': ['bishan', 'ang mo kio', 'kallang'],
    'bishan': ['toa payoh', 'ang mo kio', 'serangoon'],
}


def calculate_postal_distance(postal1: int, postal2: int) -> float:
    """
    Calculate distance between two Singapore postal codes.

    Singapore postal codes: first 2 digits = district/area (01-99),
    last 4 digits = specific location within the area.

    Returns:
        Estimated distance score (lower is closer)
    """
    area1, area2 = postal1 // 10000, postal2 // 10000

    # Same area: use direct difference
    if area1 == area2:
        return abs(postal1 - postal2)

    # Cross-area distance mapping based on Singapore geography
    adjacent_areas = {
        # Central (01-09)
        (1, 2): 1, (1, 3): 2, (1, 4): 3, (1, 5): 4, (1, 6): 5,
        (1, 7): 6, (1, 8): 7, (1, 9): 8, (1, 10): 9,
        # North (72-73, 75-82)
        (75, 76): 1, (75, 77): 2, (75, 78): 3, (75, 79): 4,
        (79, 80): 1, (80, 81): 1, (81, 82): 1,
        # South (10-16)
        (10, 11): 1, (11, 12): 1, (12, 13): 1, (13, 14): 1,
        (14, 15): 1, (15, 16): 1,
        # East (46-52)
        (46, 47): 1, (47, 48): 1, (48, 49): 1, (49, 50): 1,
        (50, 51): 1, (51, 52): 1,
        # West (60-69)
        (60, 61): 1, (61, 62): 1, (62, 63): 1, (63, 64): 1,
        (64, 65): 1, (65, 66): 1, (66, 67): 1, (67, 68): 1,
        (68, 69): 1,
        # Northeast (53-59)
        (53, 54): 1, (54, 55): 1, (55, 56): 1, (56, 57): 1,
        (57, 58): 1, (58, 59): 1,
    }

    area_pair = tuple(sorted([area1, area2]))
    base_distance = adjacent_areas.get(area_pair, abs(area1 - area2)) * 10000
    sub_distance = abs((postal1 % 10000) - (postal2 % 10000)) / 100

    return base_distance + sub_distance


def extract_postal_code(address: str) -> Optional[str]:
    """Extract Singapore postal code from address string."""
    # Try "Singapore XXXXXX" format first
    match = re.search(r'Singapore\s+(\d{6})', address, re.IGNORECASE)
    if match:
        return match.group(1)
    # Fallback to any standalone 6-digit number
    match = re.search(r'\b(\d{6})\b', address)
    return match.group(1) if match else None


def get_nearby_areas(area: str) -> List[str]:
    """Get list of nearby areas for fallback search."""
    return NEARBY_AREAS.get(area.lower(), [])
