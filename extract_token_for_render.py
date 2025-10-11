"""
Script to extract Google Drive token for Render environment variable
Run this script to get the token content to paste in Render's GOOGLE_DRIVE_TOKEN variable
"""

import json
import os

def extract_token():
    """Extract the Google Drive token content for Render deployment"""
    
    token_file = 'google_drive_token.json'
    
    if not os.path.exists(token_file):
        print(f"[ERROR] Token file not found: {token_file}")
        print("Please run 'python setup_google_drive_oauth.py' first")
        return
    
    try:
        with open(token_file, 'r') as f:
            token_content = f.read()
        
        print("=" * 70)
        print("Google Drive Token for Render Environment Variable")
        print("=" * 70)
        print()
        print("Copy the content below and paste it as the value for 'GOOGLE_DRIVE_TOKEN'")
        print("in your Render service environment variables:")
        print()
        print("-" * 70)
        print(token_content)
        print("-" * 70)
        print()
        print("Instructions:")
        print("1. Go to your Render dashboard")
        print("2. Select your PLUMASTRO service")
        print("3. Go to 'Environment' tab")
        print("4. Add new environment variable:")
        print("   - Key: GOOGLE_DRIVE_TOKEN")
        print("   - Value: [paste the content above]")
        print("5. Save and redeploy")
        print()
        print("=" * 70)
        
    except Exception as e:
        print(f"[ERROR] Failed to read token file: {e}")

if __name__ == "__main__":
    extract_token()
