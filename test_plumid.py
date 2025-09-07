#!/usr/bin/env python3
"""Test du générateur PlumID avec format 24h"""

from plumid_generator import PlumIDGenerator

# Test avec différentes heures
test_cases = [
    ("1998-12-22", "10:13", 42.35843, -71.05977),
    ("1998-12-22", "15:30", 42.35843, -71.05977),
    ("2000-01-01", "00:00", 0.0, 0.0),
    ("2023-12-31", "23:59", -45.12345, 123.67890)
]

print("🧪 Test du générateur PlumID avec format 24h")
print("=" * 50)

for date, time, lat, lon in test_cases:
    plumid = PlumIDGenerator.generate_plumid(date, time, lat, lon)
    parsed = PlumIDGenerator.parse_plumid(plumid)
    
    print(f"Input:  {date} {time} {lat} {lon}")
    print(f"PlumID: {plumid}")
    print(f"Parsed: {parsed}")
    print(f"Valid:  {PlumIDGenerator.validate_plumid(plumid)}")
    print("-" * 30)
