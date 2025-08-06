"""
Server startup script for Chime Dashboard API.
"""
import uvicorn
import logging
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main function to run the server."""
    logger.info("Starting Chime Dashboard API Server...")
    logger.info(f"Host: {settings.HOST}")
    logger.info(f"Port: {settings.PORT}")
    logger.info(f"Reload: {settings.RELOAD}")
    logger.info(f"Workers: {settings.WORKERS}")
    
    try:
        # Run the server
        uvicorn.run(
            "app.main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.RELOAD,
            workers=1 if settings.RELOAD else settings.WORKERS,
            log_level=settings.LOG_LEVEL.lower(),
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()