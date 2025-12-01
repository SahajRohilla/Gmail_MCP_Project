"""Email service for business logic and orchestration."""

import logging
from typing import Dict, Any, Optional
from services.gmail_service import GmailService

logger = logging.getLogger(__name__)


class EmailService:
    """Service for email operations and business logic."""
    
    def __init__(self, gmail_service: Optional[GmailService] = None):
        """
        Initialize email service.
        
        Args:
            gmail_service: Gmail service instance (creates new one if not provided)
        """
        self.gmail_service = gmail_service or GmailService()
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False
    ) -> Dict[str, Any]:
        """
        Send an email using Gmail API.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            body: Email body content
            is_html: Whether the body is HTML formatted
        
        Returns:
            Dictionary with 'success' (bool), 'message' (str), and optional 'message_id' (str)
        """
        try:
            # Validate inputs
            if not to_email or not to_email.strip():
                return {
                    'success': False,
                    'message': 'Recipient email address is required'
                }
            
            if not subject or not subject.strip():
                return {
                    'success': False,
                    'message': 'Email subject is required'
                }
            
            if not body or not body.strip():
                return {
                    'success': False,
                    'message': 'Email body is required'
                }
            
            # Create message
            message = self.gmail_service.create_message(
                to_email=to_email.strip(),
                subject=subject.strip(),
                body=body.strip(),
                is_html=is_html
            )
            
            # Send message
            result = self.gmail_service.send_message(message)
            
            if result['success']:
                result['message'] = f"Email sent successfully to {to_email}"
            
            return result
            
        except Exception as e:
            error_msg = f'Unexpected error in email service: {str(e)}'
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'message': error_msg
            }

