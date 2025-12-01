"""Email controller for handling HTTP requests."""

import logging
from fastapi import APIRouter, HTTPException, status
from models.email_models import EmailRequest, EmailResponse
from services.email_service import EmailService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["email"])

# Initialize service (could be injected via dependency injection in production)
email_service = EmailService()


@router.post("/send-email", response_model=EmailResponse, status_code=status.HTTP_200_OK)
async def send_email(request: EmailRequest) -> EmailResponse:
    """
    Send an email via Gmail API.
    
    Args:
        request: EmailRequest with to_email, subject, body, and optional is_html
    
    Returns:
        EmailResponse with success status and message
    
    Raises:
        HTTPException: If email sending fails
    """
    try:
        result = email_service.send_email(
            to_email=request.to_email,
            subject=request.subject,
            body=request.body,
            is_html=request.is_html
        )
        
        if result['success']:
            return EmailResponse(
                success=True,
                message=result['message'],
                subject=request.subject,
                message_id=result.get('message_id')
            )
        else:
            logger.error(f"Email sending failed: {result['message']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result['message']
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in send_email endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending email: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for email service."""
    return {
        "status": "healthy",
        "service": "email"
    }


@router.get("/auth/status")
async def auth_status():
    """
    Check Gmail authentication status and provide diagnostic information.
    
    Returns:
        Dictionary with authentication status and setup instructions
    """
    from services.gmail_service import GmailService
    
    gmail_service = GmailService()
    status = gmail_service.check_authentication_status()
    
    return status

