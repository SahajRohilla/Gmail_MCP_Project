"""
Gmail MCP Server - Main Application Entry Point

A FastAPI application that provides HTTP API and MCP protocol endpoints
for sending emails via Gmail API.
"""

import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.fastmcp import FastMCP
from controllers.email_controller import router as email_router
from mcp_integration.tools import setup_mcp_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global MCP instance to manage lifespan
_mcp_instance: FastMCP | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app. Manages the MCP session manager lifecycle."""
    global _mcp_instance
    
    if _mcp_instance:
        session_manager = _mcp_instance.session_manager
        if session_manager:
            async with session_manager.run():
                logger.info("MCP session manager started")
                yield
                logger.info("MCP session manager stopped")
            return
    
    yield


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="Gmail MCP Server",
        version="1.0.0",
        description="A minimal Gmail MCP server built with FastAPI",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify allowed origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register API routes
    app.include_router(email_router)
    
    # Setup MCP integration
    global _mcp_instance
    _mcp_instance = FastMCP(
        "Gmail MCP Server",
        streamable_http_path="/",
        json_response=True,
        stateless_http=True,
    )
    
    setup_mcp_tools(_mcp_instance)
    mcp_app = _mcp_instance.streamable_http_app()
    app.mount("/mcp", mcp_app)
    
    logger.info("MCP server mounted at /mcp")
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "message": "Gmail MCP Server",
            "version": "1.0.0",
            "endpoints": {
                "send_email": "/api/v1/send-email",
                "health": "/api/v1/health",
                "mcp": "/mcp",
                "docs": "/docs"
            }
        }
    
    # Health check endpoint
    @app.get("/health")
    async def health():
        """Application health check."""
        return {"status": "healthy", "service": "gmail-mcp-server"}
    
    logger.info("Application created successfully")
    return app


app = create_app()


def main():
    """Main entry point for running the application."""
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()

