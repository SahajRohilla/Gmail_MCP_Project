"""MCP tools for Claude Desktop integration."""

import logging
from mcp.server.fastmcp import FastMCP
from services.email_service import EmailService

logger = logging.getLogger(__name__)


def setup_mcp_tools(mcp: FastMCP) -> None:
    """
    Register MCP tools with the FastMCP instance.
    
    Args:
        mcp: FastMCP instance to register tools with
    """
    email_service = EmailService()
    
    @mcp.tool()
    def send_email_tool(
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False
    ) -> str:
        """
        Send an email using Gmail API. Requires Gmail OAuth setup (run test_gmail_auth.py first).
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            body: Email body content
            is_html: Whether the body is HTML formatted (default: false)
        
        Returns:
            Success or error message
        """
        try:
            result = email_service.send_email(to_email, subject, body, is_html)
            if result['success']:
                return result['message']
            else:
                logger.error(f"MCP tool send_email failed: {result['message']}")
                return f"Error: {result['message']}"
        except Exception as e:
            error_msg = f"Unexpected error in MCP tool: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return f"Error: {error_msg}"

