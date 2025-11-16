"""
Spotify Watcher Service
Monitors Spotify account and adds tracks to backlog
"""
import os
import time
import signal
import sys
from pathlib import Path

from downloader.spotify_listener import SpotifyListener
from downloader.backlog_manager import BacklogManager


class SpotifyWatcherService:
    """Service that monitors Spotify and adds tracks to backlog"""
    
    def __init__(self):
        # Listening account credentials (Spotify Web API)
        self.listening_client_id = os.getenv("LISTENING_CLIENT_ID")
        self.listening_client_secret = os.getenv("LISTENING_CLIENT_SECRET")
        self.listening_refresh_token = os.getenv("LISTENING_REFRESH_TOKEN")
        
        # Configuration
        self.backlog_file = os.getenv("BACKLOG_FILE", "/app/data/backlog.json")
        self.check_interval = int(os.getenv("LISTEN_CHECK_INTERVAL", "30"))  # seconds
        
        # Validate required env vars
        self._validate_config()
        
        # Type assertions after validation (guaranteed to be non-None)
        assert self.listening_client_id is not None, "LISTENING_CLIENT_ID must be set"
        assert self.listening_client_secret is not None, "LISTENING_CLIENT_SECRET must be set"
        assert self.listening_refresh_token is not None, "LISTENING_REFRESH_TOKEN must be set"
        
        # Initialize components
        self.listener = SpotifyListener(
            self.listening_client_id,
            self.listening_client_secret,
            self.listening_refresh_token
        )
        self.backlog = BacklogManager(self.backlog_file)
        
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _validate_config(self):
        """Validate that all required environment variables are set"""
        required = [
            "LISTENING_CLIENT_ID",
            "LISTENING_CLIENT_SECRET",
            "LISTENING_REFRESH_TOKEN"
        ]
        
        missing = [var for var in required if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\nShutting down watcher...")
        self.running = False
        sys.exit(0)
    
    def run(self):
        """Run the watcher service"""
        print("Starting Spotify Watcher Service...")
        print(f"Monitoring account for currently playing tracks (checking every {self.check_interval}s)")
        print(f"Backlog file: {self.backlog_file}")
        
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
                print(f"Error in watcher loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(self.check_interval)


if __name__ == "__main__":
    service = SpotifyWatcherService()
    service.run()

