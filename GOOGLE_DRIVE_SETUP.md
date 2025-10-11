# Google Drive Integration Setup

This guide explains how to set up Google Drive integration for automatic upload of birth charts and radar charts.

## 📋 Prerequisites

- Google account
- Google Cloud project with Drive API enabled

## 🔧 Setup Steps

### Step 1: Create OAuth 2.0 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Select your project (or create a new one: `PLUMASTRO-API`)
3. Click **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**
4. If prompted, configure OAuth consent screen:
   - User Type: **External**
   - App name: `PLUMASTRO API`
   - User support email: Your email
   - Developer contact: Your email
   - Click **Save and Continue** through all steps
5. Back to Create OAuth client ID:
   - Application type: **Desktop app**
   - Name: `PLUMASTRO Desktop Client`
   - Click **CREATE**
6. Download the JSON file
7. Rename it to `google_drive_credentials.json`
8. Place it in the project root directory

### Step 2: Generate OAuth Token

Run the setup script:

```bash
python setup_google_drive_oauth.py
```

This will:
1. Open a browser window
2. Ask you to sign in to your Google account
3. Ask you to authorize the app
4. Generate `google_drive_token.json` (used by the API)

### Step 3: Create and Share Google Drive Folder

1. Go to [Google Drive](https://drive.google.com/)
2. Create a folder named `PLUMASTRO_Orders`
3. Note the folder ID from the URL: `https://drive.google.com/drive/folders/[FOLDER_ID]`
4. Update `PARENT_FOLDER_ID` in `google_drive_uploader.py` if different

## 📁 File Structure

After setup, you should have:

```
project/
├── google_drive_credentials.json  # OAuth client credentials (gitignored)
├── google_drive_token.json        # OAuth token (gitignored)
├── google_drive_uploader.py       # Uploader module
└── setup_google_drive_oauth.py    # Setup script
```

## 🚀 Usage

The `/order` endpoint will automatically upload files to Google Drive:

```bash
POST /order
{
  "order_name_nb": "#1050-1",
  "customAttributes_item_value": "Homme¬¬..."
}
```

Response includes Google Drive info:

```json
{
  "google_drive": {
    "uploaded": true,
    "folder_url": "https://drive.google.com/drive/folders/...",
    "files_uploaded": {
      "birth_chart.png": "file_id_1",
      "radar1.png": "file_id_2",
      "radar2.png": "file_id_3",
      "radar3.png": "file_id_4"
    }
  }
}
```

## 🔒 Security Notes

- Never commit `google_drive_credentials.json` or `google_drive_token.json` to Git
- These files are automatically gitignored
- For production (Render), store credentials as environment variables

## 🌐 Production Deployment (Render)

For Render deployment, you'll need to:

1. Store the OAuth token as an environment variable
2. Or use a secret management service
3. Update the uploader to read from environment variables

Example:

```python
import json
import os

# In google_drive_uploader.py
token_data = os.environ.get('GOOGLE_DRIVE_TOKEN')
if token_data:
    with open('google_drive_token.json', 'w') as f:
        f.write(token_data)
```

## ❓ Troubleshooting

### Error: "Service Accounts do not have storage quota"

- This means you're using a Service Account
- Service Accounts need Shared Drives (Google Workspace)
- Solution: Use OAuth 2.0 instead (follow this guide)

### Error: "No credentials found"

- Run `python setup_google_drive_oauth.py`
- Make sure `google_drive_credentials.json` exists

### Error: "Token expired"

- Delete `google_drive_token.json`
- Run `python setup_google_drive_oauth.py` again

## 📚 API Documentation

- [Google Drive API](https://developers.google.com/drive/api/v3/about-sdk)
- [OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)

