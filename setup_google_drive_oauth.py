"""
Setup script to generate Google Drive OAuth tokens
This needs to be run ONCE to generate the refresh token
"""

import json
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Scopes required for Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def setup_oauth():
    """
    Generate OAuth credentials for Google Drive
    This will open a browser window for you to authorize the app
    """
    print("=" * 70)
    print("Google Drive OAuth Setup")
    print("=" * 70)
    print("\nThis script will:")
    print("1. Open a browser window")
    print("2. Ask you to sign in to your Google account")
    print("3. Ask you to authorize the app")
    print("4. Generate a refresh token for future use")
    print("\nStarting OAuth flow automatically...")
    
    creds = None
    token_file = 'google_drive_token.json'
    credentials_file = 'google_drive_credentials.json'
    
    # Check if we already have a token
    if os.path.exists(token_file):
        print(f"\n[INFO] Found existing token file: {token_file}")
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("\n[INFO] Refreshing expired token...")
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_file):
                print(f"\n[ERROR] Credentials file not found: {credentials_file}")
                print("\nYou need to:")
                print("1. Go to https://console.cloud.google.com/apis/credentials")
                print("2. Create OAuth 2.0 Client ID (Desktop app)")
                print("3. Download the JSON file")
                print("4. Save it as 'google_drive_credentials.json' in this directory")
                return False
            
            print("\n[INFO] Starting OAuth flow...")
            print("[INFO] A browser window will open...")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
        print(f"\n[OK] Token saved to: {token_file}")
    
    print("\n[OK] OAuth setup complete!")
    print(f"[OK] Token file: {token_file}")
    print("\nYou can now use the Google Drive uploader!")
    
    return True

if __name__ == "__main__":
    success = setup_oauth()
    if success:
        print("\n" + "=" * 70)
        print("Setup completed successfully!")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("Setup failed - please follow the instructions above")
        print("=" * 70)

