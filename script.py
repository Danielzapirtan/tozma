#!/usr/bin/env python3
"""
Search for shoe material suppliers and warehouses in Bucharest using OpenStreetMap.
"""

import requests
import json
import csv

def fetch_osm_suppliers():
    """
    Fetches potential shoe material suppliers from OSM using Romanian keywords.
    """
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    # Overpass QL query focusing on suppliers, warehouses, and wholesale in Bucharest
    query = """
    [out:json][timeout:30];
    area[name="București"]->.searchArea;
    (
      // Search by shop type: wholesale, industrial supplies, leather
      node["shop"="wholesale"](area.searchArea);
      node["shop"="trade"](area.searchArea);
      node["shop"="industrial"](area.searchArea);
      
      // Search by craft type
      node["craft"="shoemaker"](area.searchArea);
      
      // Broad search by name for suppliers, warehouses, materials
      node["name"~"depozit|depozitare|material|materiale|brutărie|en-gros|angro|provizionare|piele|nelucrată|cizmărie", i](area.searchArea);
      way["name"~"depozit|depozitare|material|materiale|brutărie|en-gros|angro|provizionare|piele|nelucrată|cizmărie", i](area.searchArea);
    );
    out center;
    """
    
    try:
        print("Querying OpenStreetMap for suppliers in Bucharest...")
        response = requests.post(overpass_url, data={'data': query})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def filter_and_process_data(osm_data):
    """
    Processes OSM data to filter and structure relevant supplier information.
    """
    if not osm_data or 'elements' not in osm_data:
        return []
    
    suppliers = []
    seen_ids = set()
    
    shoe_material_keywords = [
        'cizmărie', 'cizmar', 'pantof', 'shoe', 'footwear',
        'piele', 'leather', 'material', 'skin', 'textil',
        'depozit', 'warehouse', 'wholesale', 'en-gros', 'angro',
        'nelucrată', 'raw', 'brut', 'provizie', 'supply'
    ]
    
    for element in osm_data['elements']:
        # Get OSM ID (node or way)
        element_id = f"{element['type']}_{element['id']}"
        if element_id in seen_ids:
            continue
        seen_ids.add(element_id)
        
        tags = element.get('tags', {})
        name = tags.get('name', '').lower()
        shop_type = tags.get('shop', '').lower()
        craft_type = tags.get('craft', '').lower()
        
        # Filtering logic for potential suppliers/warehouses
        is_relevant = False
        
        # 1. Check by business type
        if shop_type in ['wholesale', 'trade', 'industrial']:
            is_relevant = True
        elif craft_type == 'shoemaker':
            is_relevant = True
        
        # 2. Check by name keywords
        name_check = any(keyword in name for keyword in shoe_material_keywords)
        if name_check:
            is_relevant = True
        
        # If relevant, compile the supplier's data
        if is_relevant:
            # Determine coordinates
            lat, lon = None, None
            if element['type'] == 'node':
                lat, lon = element.get('lat'), element.get('lon')
            elif element['type'] == 'way' and 'center' in element:
                lat, lon = element['center'].get('lat'), element['center'].get('lon')
            
            supplier = {
                'id': element['id'],
                'type': element['type'],
                'name': tags.get('name', 'N/A'),
                'address': f"{tags.get('addr:street', '')} {tags.get('addr:housenumber', '')}".strip(),
                'city': tags.get('addr:city', 'București'),
                'postcode': tags.get('addr:postcode', ''),
                'shop': tags.get('shop', ''),
                'craft': tags.get('craft', ''),
                'description': tags.get('description', ''),
                'phone': tags.get('phone', ''),
                'website': tags.get('website', ''),
                'latitude': lat,
                'longitude': lon
            }
            suppliers.append(supplier)
    
    return suppliers

def save_to_csv(suppliers, filename="bucharest_shoe_suppliers.csv"):
    """Saves supplier data to a CSV file."""
    if not suppliers:
        print("No data to save.")
        return
    
    fieldnames = ['id', 'type', 'name', 'address', 'city', 'postcode', 
                  'shop', 'craft', 'description', 'phone', 'website', 
                  'latitude', 'longitude']
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(suppliers)
    
    print(f"✓ Data for {len(suppliers)} locations saved to '{filename}'.")

def display_results(suppliers):
    """Displays a summary of found suppliers."""
    if not suppliers:
        print("\nNo potential suppliers found with the current query.")
        print("Try broadening the search or checking other sources.")
        return
    
    print(f"\nFound {len(suppliers)} potential suppliers/warehouses:\n")
    print("=" * 60)
    
    for i, supplier in enumerate(suppliers, 1):
        print(f"{i}. {supplier['name']}")
        if supplier['address']:
            print(f"   📍 {supplier['address']}, {supplier['city']}")
        if supplier['shop']:
            print(f"   🏪 Shop type: {supplier['shop']}")
        if supplier['craft']:
            print(f"   🛠 Craft: {supplier['craft']}")
        if supplier['phone']:
            print(f"   📞 {supplier['phone']}")
        print()

def main():
    print("=" * 60)
    print("Searching for shoe material suppliers in Bucharest")
    print("Source: OpenStreetMap (OSM) Database")
    print("=" * 60)
    
    # Fetch and process data
    raw_data = fetch_osm_suppliers()
    suppliers_list = filter_and_process_data(raw_data)
    
    # Display and save results
    display_results(suppliers_list)
    
    if suppliers_list:
        save_to_csv(suppliers_list)
        print("\n💡 Tips for better results:")
        print("• Visit the locations found; suppliers might not be fully listed online.")
        print("• Search Romanian B2B platforms (e.g., Romania-Export.ro, Bizoo.ro).")
        print("• Contact professional shoemaker associations in Romania.")

if __name__ == "__main__":
    main()
