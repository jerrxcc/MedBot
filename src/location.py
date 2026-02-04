"""
Location services for Singapore clinic search.
Provides postal code distance calculation, geocoding, and map generation.
"""
import re
import time
from typing import Optional, Tuple, List, Dict, Any

# Lazy imports for optional dependencies
_geolocator = None
_folium = None


def get_geolocator():
    """Get or initialize the geocoder."""
    global _geolocator
    if _geolocator is None:
        try:
            from geopy.geocoders import Nominatim
            _geolocator = Nominatim(user_agent="medbot_clinic_search")
        except ImportError:
            raise ImportError("geopy is required for geocoding. Install with: pip install geopy")
    return _geolocator


def get_folium():
    """Get folium module for map generation."""
    global _folium
    if _folium is None:
        try:
            import folium
            _folium = folium
        except ImportError:
            raise ImportError("folium is required for map generation. Install with: pip install folium")
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

    Singapore postal codes follow a pattern where:
    - First 2 digits represent the district/area (01-99)
    - Last 4 digits represent specific location within the area

    Args:
        postal1: First postal code (6 digits)
        postal2: Second postal code (6 digits)

    Returns:
        Estimated distance score (lower is closer)
    """
    # Extract 2-digit area codes
    area1 = postal1 // 10000
    area2 = postal2 // 10000

    # Same area - use last 4 digits difference
    if area1 == area2:
        return abs(postal1 - postal2)

    # Cross-area distance mapping based on Singapore geography
    area_distances = {
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

    # Check direct mapping
    area_pair = tuple(sorted([area1, area2]))
    if area_pair in area_distances:
        base_distance = area_distances[area_pair] * 10000
    else:
        # Default cross-area distance based on area code difference
        base_distance = abs(area1 - area2) * 10000

    # Add sub-area distance
    sub_distance = abs((postal1 % 10000) - (postal2 % 10000)) / 100

    return base_distance + sub_distance


def extract_postal_code(address: str) -> Optional[str]:
    """Extract Singapore postal code from address string."""
    match = re.search(r'Singapore\s+(\d{6})', address, re.IGNORECASE)
    if match:
        return match.group(1)
    # Also try standalone 6-digit postal code
    match = re.search(r'\b(\d{6})\b', address)
    if match:
        return match.group(1)
    return None


def get_coordinates(address: str, area: str = None) -> Optional[Tuple[float, float]]:
    """
    Get coordinates for an address using geocoding with fallbacks.

    Args:
        address: Full address string
        area: Optional area name for fallback

    Returns:
        Tuple of (latitude, longitude) or None
    """
    try:
        geolocator = get_geolocator()

        # Clean address
        clean_address = address.replace('\n', ' ').replace('  ', ' ').strip()

        # Try 1: Full address geocoding
        location = geolocator.geocode(f"{clean_address}", timeout=5)
        if location:
            return location.latitude, location.longitude

        # Try 2: Extract and geocode street address
        postal_match = re.search(r'(\d+\s+[\w\s]+Street\s+\d+)', clean_address)
        if postal_match:
            street_address = postal_match.group(1) + ', Singapore'
            time.sleep(0.5)
            location = geolocator.geocode(street_address, timeout=5)
            if location:
                return location.latitude, location.longitude

        # Try 3: Use area name
        if area:
            time.sleep(0.5)
            location = geolocator.geocode(f"{area}, Singapore", timeout=5)
            if location:
                return location.latitude, location.longitude

        # Try 4: Fallback to predefined area coordinates
        if area and area in SINGAPORE_AREA_COORDS:
            return SINGAPORE_AREA_COORDS[area]

    except Exception as e:
        print(f"Geocoding error for {address}: {e}")

    return None


def get_nearby_areas(area: str) -> List[str]:
    """Get list of nearby areas for fallback search."""
    area_lower = area.lower()
    return NEARBY_AREAS.get(area_lower, [])


def create_clinic_map(
    clinic_results: List[Dict[str, Any]],
    query_postal: str = None,
    query_area: str = None
) -> Any:
    """
    Create an interactive map showing clinic locations.

    Args:
        clinic_results: List of clinic data dicts with 'Name', 'Address', 'Area' fields
        query_postal: Optional postal code that was queried
        query_area: Optional area name that was queried

    Returns:
        Folium map object
    """
    folium = get_folium()

    # Singapore center
    singapore_center = [1.3521, 103.8198]

    # Create map
    m = folium.Map(
        location=singapore_center,
        zoom_start=12,
        tiles='OpenStreetMap'
    )

    # Add query location marker if postal code provided
    if query_postal:
        try:
            query_coords = get_coordinates(f"Singapore {query_postal}")
            if query_coords:
                folium.Marker(
                    query_coords,
                    popup=f"Your Location (Postal: {query_postal})",
                    icon=folium.Icon(color='red', icon='home')
                ).add_to(m)
        except Exception as e:
            print(f"Error adding query marker: {e}")

    # Add clinic markers
    import random
    for i, clinic in enumerate(clinic_results[:15]):  # Limit to 15 clinics
        name = clinic.get('Name', 'Unknown Clinic')
        address = clinic.get('Address', '')
        area = clinic.get('Area', '')
        distance = clinic.get('_distance')

        # Get coordinates (may make API call)
        coords = get_coordinates(address, area)
        used_geocoding_api = coords is not None  # If we got coords, API may have been called

        if not coords and area in SINGAPORE_AREA_COORDS:
            # Add small offset for each clinic to spread them out (no API call)
            base_lat, base_lng = SINGAPORE_AREA_COORDS[area]
            random.seed(hash(name) % 1000)
            offset_lat = (random.random() - 0.5) * 0.01
            offset_lng = (random.random() - 0.5) * 0.01
            coords = (base_lat + offset_lat, base_lng + offset_lng)
            used_geocoding_api = False

        if not coords:
            # Fallback to Singapore center with offset (no API call)
            random.seed(hash(name) % 1000)
            coords = (1.3521 + (random.random() - 0.5) * 0.05,
                     103.8198 + (random.random() - 0.5) * 0.05)
            used_geocoding_api = False

        # Create popup content
        popup_html = f"""
        <div style='font-family: Arial; width: 220px;'>
            <h4 style='margin: 0 0 8px 0; color: #2E8B57;'>{name}</h4>
            <p style='margin: 4px 0;'><b>Area:</b> {area}</p>
            <p style='margin: 4px 0;'><b>Address:</b> {address[:100]}{'...' if len(address) > 100 else ''}</p>
            {f'<p style="margin: 4px 0;"><b>Distance:</b> {distance:.0f}</p>' if distance else ''}
        </div>
        """

        # Determine marker color based on distance
        if distance is not None:
            if distance <= 2000:
                color = 'green'
            elif distance <= 10000:
                color = 'orange'
            else:
                color = 'gray'
        else:
            color = 'blue'

        folium.Marker(
            coords,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{i+1}. {name}",
            icon=folium.Icon(color=color, icon='plus-sign')
        ).add_to(m)

        # Only rate limit when we actually made a geocoding API call
        if used_geocoding_api:
            time.sleep(0.1)

    return m


def map_to_html(m) -> str:
    """Convert folium map to HTML string for embedding."""
    return m._repr_html_()
