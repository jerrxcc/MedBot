"""
Location services for Singapore clinic search.
Provides postal code distance calculation, geocoding, and map generation.
"""
import random
import re
import time
from typing import Any, Dict, List, Optional, Tuple

# Lazy-loaded dependencies
_geolocator = None
_folium = None


def get_geolocator():
    """Get or initialize the geocoder (lazy loading)."""
    global _geolocator
    if _geolocator is None:
        from geopy.geocoders import Nominatim
        _geolocator = Nominatim(user_agent="medbot_clinic_search")
    return _geolocator


def get_folium():
    """Get folium module (lazy loading)."""
    global _folium
    if _folium is None:
        import folium
        _folium = folium
    return _folium


# Singapore area coordinates mapping
SINGAPORE_AREA_COORDS = {
    'Jurong West': (1.347, 103.717),
    'Jurong East': (1.333, 103.742),
    'Bedok': (1.324, 103.930),
    'Tampines': (1.345, 103.944),
    'Yishun': (1.429, 103.835),
    'Woodlands': (1.437, 103.786),
    'Ang Mo Kio': (1.375, 103.845),
    'Sengkang': (1.391, 103.895),
    'Punggol': (1.405, 103.902),
    'Serangoon': (1.357, 103.874),
    'Bukit Batok': (1.358, 103.754),
    'Bukit Merah': (1.277, 103.823),
    'Clementi': (1.315, 103.760),
    'Hougang': (1.371, 103.886),
    'Pasir Ris': (1.372, 103.949),
    'Toa Payoh': (1.334, 103.856),
    'Bishan': (1.351, 103.848),
    'Kallang': (1.311, 103.862),
    'Sembawang': (1.449, 103.820),
    'Choa Chu Kang': (1.385, 103.744),
    'Queenstown': (1.294, 103.806),
    'Geylang': (1.318, 103.884),
    'Marine Parade': (1.302, 103.907),
    'Bukit Timah': (1.333, 103.776),
    'Central': (1.290, 103.852),
}

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


def get_coordinates(address: str, area: str = None) -> Optional[Tuple[float, float]]:
    """Get coordinates for an address using geocoding with fallbacks."""
    try:
        geolocator = get_geolocator()
        clean_address = address.replace('\n', ' ').replace('  ', ' ').strip()

        # Try full address geocoding
        location = geolocator.geocode(clean_address, timeout=5)
        if location:
            return location.latitude, location.longitude

        # Try street address extraction
        street_match = re.search(r'(\d+\s+[\w\s]+Street\s+\d+)', clean_address)
        if street_match:
            time.sleep(0.5)
            location = geolocator.geocode(f"{street_match.group(1)}, Singapore", timeout=5)
            if location:
                return location.latitude, location.longitude

        # Try area name
        if area:
            time.sleep(0.5)
            location = geolocator.geocode(f"{area}, Singapore", timeout=5)
            if location:
                return location.latitude, location.longitude

        # Fallback to predefined coordinates
        if area and area in SINGAPORE_AREA_COORDS:
            return SINGAPORE_AREA_COORDS[area]

    except Exception as e:
        print(f"Geocoding error for {address}: {e}")

    return None


def get_nearby_areas(area: str) -> List[str]:
    """Get list of nearby areas for fallback search."""
    return NEARBY_AREAS.get(area.lower(), [])


def create_clinic_map(
    clinic_results: List[Dict[str, Any]],
    query_postal: str = None,
    query_area: str = None
) -> Any:
    """Create an interactive map showing clinic locations."""
    folium = get_folium()
    singapore_center = [1.3521, 103.8198]

    m = folium.Map(location=singapore_center, zoom_start=12, tiles='OpenStreetMap')

    # Add query location marker
    if query_postal:
        query_coords = get_coordinates(f"Singapore {query_postal}")
        if query_coords:
            folium.Marker(
                query_coords,
                popup=f"Your Location (Postal: {query_postal})",
                icon=folium.Icon(color='red', icon='home')
            ).add_to(m)

    # Add clinic markers (limit to 15)
    for i, clinic in enumerate(clinic_results[:15]):
        name = clinic.get('Name', 'Unknown Clinic')
        address = clinic.get('Address', '')
        area = clinic.get('Area', '')
        distance = clinic.get('_distance')

        coords, used_api = _get_clinic_coordinates(name, address, area)

        popup_html = _build_popup_html(name, area, address, distance)
        color = _get_marker_color(distance)

        folium.Marker(
            coords,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{i+1}. {name}",
            icon=folium.Icon(color=color, icon='plus-sign')
        ).add_to(m)

        if used_api:
            time.sleep(0.1)

    return m


def _get_clinic_coordinates(name: str, address: str, area: str) -> Tuple[Tuple[float, float], bool]:
    """Get coordinates for a clinic, with fallbacks."""
    coords = get_coordinates(address, area)
    if coords:
        return coords, True

    # Fallback to area coordinates with offset
    if area in SINGAPORE_AREA_COORDS:
        base_lat, base_lng = SINGAPORE_AREA_COORDS[area]
        random.seed(hash(name) % 1000)
        offset = lambda: (random.random() - 0.5) * 0.01
        return (base_lat + offset(), base_lng + offset()), False

    # Final fallback: Singapore center with offset
    random.seed(hash(name) % 1000)
    offset = lambda: (random.random() - 0.5) * 0.05
    return (1.3521 + offset(), 103.8198 + offset()), False


def _build_popup_html(name: str, area: str, address: str, distance: float) -> str:
    """Build HTML for clinic popup."""
    truncated_address = address[:100] + '...' if len(address) > 100 else address
    distance_html = f'<p style="margin: 4px 0;"><b>Distance:</b> {distance:.0f}</p>' if distance else ''

    return f"""
    <div style='font-family: Arial; width: 220px;'>
        <h4 style='margin: 0 0 8px 0; color: #2E8B57;'>{name}</h4>
        <p style='margin: 4px 0;'><b>Area:</b> {area}</p>
        <p style='margin: 4px 0;'><b>Address:</b> {truncated_address}</p>
        {distance_html}
    </div>
    """


def _get_marker_color(distance: float) -> str:
    """Determine marker color based on distance."""
    if distance is None:
        return 'blue'
    if distance <= 2000:
        return 'green'
    if distance <= 10000:
        return 'orange'
    return 'gray'


def map_to_html(m) -> str:
    """Convert folium map to HTML string for embedding."""
    return m._repr_html_()
