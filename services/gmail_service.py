"""Gmail API service for authentication and email operations."""

import os
import base64
import logging
from typing import Optional
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']


class GmailService:
    """Service for interacting with Gmail API."""
    
    def __init__(self, token_file: str = 'token.json', credentials_file: str = 'credentials.json'):
        """
        Initialize Gmail service.
        
        Args:
            token_file: Path to OAuth token file
            credentials_file: Path to OAuth credentials file
        """
        self.token_file = token_file
        self.credentials_file = credentials_file
        self._service: Optional[object] = None
    
    def get_service(self) -> Optional[object]:
        """
        Get authenticated Gmail service instance.
        
        Returns:
            Gmail service object or None if authentication fails
        """
        if self._service is not None:
            return self._service
        
        creds = self._load_credentials()
        if not creds:
            return None
        
        try:
            self._service = build('gmail', 'v1', credentials=creds)
            logger.info('Gmail service initialized successfully')
            return self._service
        except HttpError as error:
            logger.error(f'Error building Gmail service: {error}')
            return None
    
    def check_authentication_status(self) -> dict:
        """
        Check the authentication status and provide diagnostic information.
        
        Returns:
            Dictionary with authentication status and diagnostic info
        """
        status = {
            'authenticated': False,
            'credentials_file_exists': os.path.exists(self.credentials_file),
            'token_file_exists': os.path.exists(self.token_file),
            'message': '',
            'instructions': []
        }
        
        if not status['credentials_file_exists']:
            status['message'] = 'credentials.json not found'
            status['instructions'] = [
                '1. Go to https://console.cloud.google.com/',
                '2. Create a project or select an existing one',
                '3. Enable Gmail API',
                '4. Create OAuth 2.0 Client ID (Desktop app)',
                '5. Download credentials.json and place it in the project root'
            ]
            return status
        
        if not status['token_file_exists']:
            status['message'] = 'token.json not found. Run test_gmail_auth.py to authenticate.'
            status['instructions'] = [
                'Run: python test_gmail_auth.py',
                'This will open a browser for Google OAuth authentication'
            ]
            return status
        
        # Try to load credentials
        creds = None
        try:
            if os.path.exists(self.token_file):
                creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        except Exception as e:
            status['message'] = f'Error loading token.json: {str(e)}'
            status['instructions'] = [
                'Token file may be corrupted.',
                'Run: python test_gmail_auth.py to regenerate it'
            ]
            return status
        
        if creds and creds.valid:
            status['authenticated'] = True
            status['message'] = 'Authentication successful'
        elif creds and creds.expired and creds.refresh_token:
            status['message'] = 'Token expired but can be refreshed'
            status['instructions'] = ['Token will be automatically refreshed on next use']
        else:
            status['message'] = 'Invalid or expired token'
            status['instructions'] = [
                'Run: python test_gmail_auth.py to re-authenticate'
            ]
        
        return status
    
    def _load_credentials(self) -> Optional[Credentials]:
        """
        Load and refresh OAuth credentials.
        
        Returns:
            Credentials object or None if authentication fails
        """
        creds = None
        
        # Check if credentials.json exists
        if not os.path.exists(self.credentials_file):
            logger.error(
                f'credentials.json not found at {self.credentials_file}. '
                'Please download it from Google Cloud Console and place it in the project root.'
            )
            return None
        
        # Load existing token
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
            except Exception as e:
                logger.error(f'Error loading credentials from {self.token_file}: {e}')
                logger.info('Token file may be corrupted. Please run test_gmail_auth.py to regenerate it.')
                return None
        
        # If there are no (valid) credentials available, return None
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    logger.info('Refreshing expired token...')
                    creds.refresh(Request())
                    self._save_credentials(creds)
                    logger.info('Token refreshed successfully')
                except Exception as e:
                    logger.error(f'Error refreshing token: {e}')
                    logger.info('Please run test_gmail_auth.py to re-authenticate.')
                    return None
            else:
                logger.warning(
                    f'No valid credentials found. Token file exists: {os.path.exists(self.token_file)}. '
                    f'Please run: python test_gmail_auth.py'
                )
                return None
        
        return creds
    
    def _save_credentials(self, creds: Credentials) -> None:
        """Save credentials to token file."""
        try:
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
            logger.info(f'Credentials saved to {self.token_file}')
        except Exception as e:
            logger.error(f'Error saving credentials: {e}')
    
    def create_message(self, to_email: str, subject: str, body: str, is_html: bool = False) -> dict:
        """
        Create a MIME message for sending via Gmail API.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            is_html: Whether the body is HTML formatted
        
        Returns:
            Dictionary with 'raw' key containing base64-encoded message
        """
        if is_html:
            message = MIMEText(body, 'html')
        else:
            message = MIMEText(body, 'plain')
        
        message['to'] = to_email
        message['subject'] = subject
        
        # Encode the message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        return {'raw': raw_message}
    
    def send_message(self, message: dict) -> dict:
        """
        Send a message via Gmail API.
        
        Args:
            message: Message dictionary with 'raw' key
        
        Returns:
            Dictionary with 'success' (bool), 'message' (str), and optional 'message_id' (str)
        """
        service = self.get_service()
        if not service:
            return {
                'success': False,
                'message': 'Failed to authenticate with Gmail. Please run test_gmail_auth.py first.'
            }
        
        try:
            sent_message = service.users().messages().send(
                userId='me',
                body=message
            ).execute()
            
            message_id = sent_message.get('id')
            logger.info(f'Email sent successfully. Message ID: {message_id}')
            
            return {
                'success': True,
                'message': 'Email sent successfully',
                'message_id': message_id
            }
        except HttpError as error:
            error_msg = f'Gmail API error: {error}'
            logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg
            }
        except Exception as e:
            error_msg = f'Unexpected error sending email: {str(e)}'
            logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg
            }

