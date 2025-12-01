"""Email-related Pydantic models for request/response validation."""

from pydantic import BaseModel, EmailStr
from typing import Optional


class EmailRequest(BaseModel):
    """Request model for sending email via HTTP API."""
    
    to_email: EmailStr
    subject: str
    body: str
    is_html: Optional[bool] = False
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "to_email": "recipient@example.com",
                "subject": "Test Email",
                "body": "This is a test email body",
                "is_html": False
            }
        }


class EmailResponse(BaseModel):
    """Response model for email sending operations."""
    
    success: bool
    message: str
    subject: Optional[str] = None
    message_id: Optional[str] = None
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Email sent successfully to recipient@example.com",
                "subject": "Test Email",
                "message_id": "1234567890"
            }
        }

