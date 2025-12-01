"""
One-time script to perform Gmail OAuth and create token.json.
Run this script once to authenticate with Gmail and generate the token file.
"""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']


def main():
    """Perform OAuth flow and save token.json"""
    creds = None
    
    # Check if token.json already exists
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("ERROR: credentials.json not found!")
                print("Please download credentials.json from Google Cloud Console:")
                print("1. Go to https://console.cloud.google.com/")
                print("2. Create a project or select an existing one")
                print("3. Enable Gmail API")
                print("4. Create OAuth 2.0 Client ID (Desktop app)")
                print("5. Download credentials.json and place it in this directory")
                return
            
            print("Starting OAuth flow...")
            print("A browser window will open for Google login and consent.")
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        print("Token saved to token.json")
    else:
        print("Valid token.json already exists. No action needed.")


if __name__ == '__main__':
    main()

