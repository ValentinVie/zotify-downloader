"""
Spotify Downloader Service
Processes backlog and downloads tracks
"""
import os
import time
import signal
import sys
import logging
from pathlib import Path

from downloader.backlog_manager import BacklogManager
from downloader.download_processor import DownloadProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class SpotifyDownloaderService:
    """Service that processes backlog and downloads tracks"""
    
    def __init__(self):
        # Downloading account credentials (zotify)
        self.download_username = os.getenv("DOWNLOAD_USERNAME")
        self.download_password = os.getenv("DOWNLOAD_PASSWORD")
        
        # Configuration
        self.download_folder = os.getenv("DOWNLOAD_FOLDER", "/app/downloads")
        self.backlog_file = os.getenv("BACKLOG_FILE", "/app/data/backlog.json")
        self.download_interval = int(os.getenv("DOWNLOAD_INTERVAL", "900"))  # seconds (default: 15 minutes)
        
        # Validate required env vars
        self._validate_config()
        
        # Type assertions after validation (guaranteed to be non-None)
        assert self.download_username is not None, "DOWNLOAD_USERNAME must be set"
        assert self.download_password is not None, "DOWNLOAD_PASSWORD must be set"
        
        # Initialize components
        self.backlog = BacklogManager(self.backlog_file)
        self.processor = DownloadProcessor(
            self.download_username,
            self.download_password,
            self.download_folder
        )
        
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _validate_config(self):
        """Validate that all required environment variables are set"""
        required = [
            "DOWNLOAD_USERNAME",
            "DOWNLOAD_PASSWORD"
        ]
        
        missing = [var for var in required if not os.getenv(var)]
        if missing:
            logger.error(f"Missing required environment variables: {', '.join(missing)}")
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        logger.info("Configuration validated successfully")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("Received shutdown signal, shutting down downloader...")
        self.running = False
        sys.exit(0)
    
    def run(self):
        """Run the downloader service"""
        logger.info("Starting Spotify Downloader Service...")
        logger.info(f"Download interval: {self.download_interval}s (every {self.download_interval // 60} minutes)")
        logger.info(f"Backlog file: {self.backlog_file}")
        logger.info(f"Download folder: {self.download_folder}")
        
        while self.running:
            try:
                logger.debug("Processing backlog...")
                
                backlog_size = self.backlog.get_backlog_size()
                
                if backlog_size > 0:
                    logger.info(f"Backlog has {backlog_size} track(s), processing...")
                    downloaded = self.processor.process_backlog(self.backlog, max_tracks=10)
                    logger.info(f"Downloaded {downloaded} track(s)")
                else:
                    logger.debug("Backlog is empty, nothing to process.")
                
                # Sleep for the downloader interval
                time.sleep(self.download_interval)
                
            except Exception as e:
                logger.error(f"Error in downloader loop: {e}", exc_info=True)
                time.sleep(self.download_interval)


if __name__ == "__main__":
    service = SpotifyDownloaderService()
    service.run()

