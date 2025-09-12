#!/usr/bin/env python3
"""
Script to convert the 500 profiles from JSON array format to the format expected by the batch processor
"""

import json

def convert_profiles():
    # Read the JSON file with 500 profiles
    with open('plumastro_500_profiles.json', 'r', encoding='utf-8') as f:
        profiles = json.load(f)
    
    # Convert to the format expected by batch processor (separate JSON objects)
    output = ""
    for profile in profiles:
        output += json.dumps(profile, indent=2) + "\n"
    
    # Write to file
    with open('profiles_500_converted.txt', 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(f"✅ Converted {len(profiles)} profiles to batch processor format")
    print("📁 Saved to profiles_500_converted.txt")
    return output

if __name__ == "__main__":
    convert_profiles()

