#!/usr/bin/env python3
"""
Script to convert JSON array format to the format expected by the batch processor
"""

import json

# Your 500 profiles in JSON array format
profiles_json = '''
[
  {
    "name": "",
    "date": "1972-10-18",
    "time": "20:44",
    "lat": 41.133806,
    "lon": 28.835051,
    "country": "",
    "state": ""
  },
  {
    "name": "",
    "date": "1961-01-28",
    "time": "03:38",
    "lat": 10.312158,
    "lon": -67.14608,
    "country": "",
    "state": ""
  }
]
'''

# Parse the JSON array
profiles = json.loads(profiles_json)

# Convert to the format expected by batch processor
output = ""
for profile in profiles:
    output += json.dumps(profile, indent=2) + "\n"

# Write to file
with open('profiles_500_converted.txt', 'w', encoding='utf-8') as f:
    f.write(output)

print(f"Converted {len(profiles)} profiles to batch processor format")
print("Saved to profiles_500_converted.txt")
