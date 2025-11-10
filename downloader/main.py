"""
Main Orchestrator
Coordinates the Spotify listener and download processor
"""
import os
import time
import signal
import sys
import threading
from pathlib import Path

from downloader.spotify_listener import SpotifyListener
from downloader.backlog_manager import BacklogManager
from downloader.download_processor import DownloadProcessor


class MusicDownloaderService:
    """Main service orchestrating listener and downloader"""
    
    def __init__(self):
        # Listening account credentials (Spotify Web API)
        self.listening_client_id = os.getenv("LISTENING_CLIENT_ID")
        self.listening_client_secret = os.getenv("LISTENING_CLIENT_SECRET")
        self.listening_refresh_token = os.getenv("LISTENING_REFRESH_TOKEN")
        
        # Downloading account credentials (zotify)
        self.download_username = os.getenv("DOWNLOAD_USERNAME")
        self.download_password = os.getenv("DOWNLOAD_PASSWORD")
        
        # Configuration
        self.download_folder = os.getenv("DOWNLOAD_FOLDER", "/app/downloads")
        self.backlog_file = os.getenv("BACKLOG_FILE", "/app/data/backlog.json")
        self.check_interval = int(os.getenv("LISTEN_CHECK_INTERVAL", "30"))  # seconds
        self.download_interval = int(os.getenv("DOWNLOAD_INTERVAL", "900"))  # seconds (default: 15 minutes)
        
        # Validate required env vars
        self._validate_config()
        
        # Initialize components
        self.listener = SpotifyListener(
            self.listening_client_id,
            self.listening_client_secret,
            self.listening_refresh_token
        )
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
            "LISTENING_CLIENT_ID",
            "LISTENING_CLIENT_SECRET",
            "LISTENING_REFRESH_TOKEN",
            "DOWNLOAD_USERNAME",
            "DOWNLOAD_PASSWORD"
        ]
        
        missing = [var for var in required if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\nShutting down...")
        self.running = False
        sys.exit(0)
    
    def _listener_loop(self):
        """Run listener on schedule in a separate thread"""
        print("Starting Spotify listener service...")
        print(f"Monitoring account for currently playing tracks (checking every {self.check_interval}s)")
        
        while self.running:
            try:
                new_track = self.listener.check_for_new_track()
                
                if new_track:
                    track_name = new_track.get("track_name", "Unknown")
                    artists = ", ".join(new_track.get("artists", []))
                    print(f"New track detected: {track_name} by {artists}")
                    
                    if self.backlog.add_track(new_track):
                        print(f"Added to backlog: {track_name}")
                    else:
                        print(f"Track already in backlog: {track_name}")
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                print(f"Error in listener loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(self.check_interval)
    
    def _downloader_loop(self):
        """Run downloader on schedule in a separate thread"""
        while self.running:
            try:
                print("Processing backlog...")
                print(f"Backlog file: {self.backlog_file}")
                
                backlog_size = self.backlog.get_backlog_size()
                
                if backlog_size > 0:
                    print(f"Backlog has {backlog_size} track(s), processing...")
                    downloaded = self.processor.process_backlog(self.backlog, max_tracks=10)
                    print(f"Downloaded {downloaded} track(s)")
                else:
                    print("Backlog is empty, nothing to process.")
                
                # Sleep for the downloader interval
                time.sleep(self.download_interval)
                
            except Exception as e:
                print(f"Error in downloader loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(self.download_interval)
    
    def run(self):
        """Run both listener and downloader together"""
        print("Starting Zotify Downloader Service...")
        print(f"Listener check interval: {self.check_interval}s")
        print(f"Downloader interval: {self.download_interval}s (every {self.download_interval // 60} minutes)")
        
        # Start listener in a separate thread
        listener_thread = threading.Thread(target=self._listener_loop, daemon=True)
        listener_thread.start()
        print("Listener thread started")
        
        # Start downloader in a separate thread
        downloader_thread = threading.Thread(target=self._downloader_loop, daemon=True)
        downloader_thread.start()
        print("Downloader thread started")
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            self.running = False


if __name__ == "__main__":
    service = MusicDownloaderService()
    service.run()

