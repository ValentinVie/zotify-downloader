"""
Download Processor
Processes backlog tracks using zotify with the downloading account
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Dict

# Add zotify to path
sys.path.insert(0, '/app')

logger = logging.getLogger(__name__)

from zotify.app import download_from_urls
from zotify.config import Config, CONFIG_VALUES
from zotify.zotify import Zotify
from librespot.audio.decoders import AudioQuality


class DownloadProcessor:
    """Processes downloads from backlog using zotify"""
    
    def __init__(self, download_username: str, download_password: str, download_folder: str):
        self.download_username = download_username
        self.download_password = download_password
        self.download_folder = download_folder
        self._zotify_initialized = False
        
    def _initialize_zotify(self):
        """Initialize zotify session if not already done"""
        if self._zotify_initialized and Zotify.SESSION is not None:
            return
        
        logger.info("Initializing zotify session...")
        
        # Create args object for zotify
        args = argparse.Namespace()
        args.username = self.download_username
        args.password = self.download_password
        args.config_location = None
        args.no_splash = True
        
        # Set download folder (Music folder is mapped directly via Docker)
        args.root_path = self.download_folder
        
        # Set all config values to None (will use defaults from config file)
        for key in CONFIG_VALUES:
            attr_name = key.lower().replace('_', '-')
            setattr(args, attr_name, None)
        
        # Explicitly enable skip_existing to prevent duplicate downloads
        args.skip_existing = True
        
        # Set output format: {artist}/{album}/{song_name}.{ext}
        # This must be set after the loop to ensure it's not overridden
        args.output = "{artist}/{album}/{song_name}.{ext}"
        
        # Initialize zotify
        Zotify(args)
        
        # Set download quality
        quality_options = {
            'auto': AudioQuality.VERY_HIGH if Zotify.check_premium() else AudioQuality.HIGH,
            'normal': AudioQuality.NORMAL,
            'high': AudioQuality.HIGH,
            'very_high': AudioQuality.VERY_HIGH
        }
        Zotify.DOWNLOAD_QUALITY = quality_options.get('auto', AudioQuality.HIGH)
        
        is_premium = Zotify.check_premium()
        logger.info(f"Zotify initialized successfully (Premium: {is_premium}, Quality: {Zotify.DOWNLOAD_QUALITY})")
        self._zotify_initialized = True
        
    def download_track(self, track_info: Dict) -> bool:
        """
        Download a single track using zotify
        Returns True if successful, False otherwise
        """
        spotify_url = track_info.get("spotify_url") or track_info.get("uri", "")
        
        # Convert URI to URL if needed
        if spotify_url.startswith("spotify:track:"):
            track_id = spotify_url.replace("spotify:track:", "")
            spotify_url = f"https://open.spotify.com/track/{track_id}"
        
        if not spotify_url or not spotify_url.startswith("http"):
            logger.error(f"Invalid URL for track {track_info.get('track_id')}: {spotify_url}")
            return False
        
        try:
            # Initialize zotify if needed
            self._initialize_zotify()
            
            # Download the track
            track_name = track_info.get('track_name', 'Unknown')
            artists = ', '.join(track_info.get('artists', []))
            logger.info(f"Downloading: {track_name} by {artists}")
            
            success = download_from_urls([spotify_url])
            
            if success:
                logger.info(f"Successfully downloaded: {track_name} by {artists}")
            else:
                logger.warning(f"Download returned False for: {track_name} by {artists}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error downloading track {track_info.get('track_id')}: {e}", exc_info=True)
            return False
    
    def process_backlog(self, backlog_manager, max_tracks: int = 10) -> int:
        """
        Process up to max_tracks from backlog
        Returns number of tracks successfully downloaded
        """
        downloaded = 0
        
        for _ in range(max_tracks):
            track = backlog_manager.get_next_track()
            if not track:
                break
            
            track_id = track["track_id"]
            track_name = track.get('track_name', 'Unknown')
            logger.info(f"Processing track: {track_name} ({track_id})")
            
            if self.download_track(track):
                backlog_manager.remove_track(track_id)
                downloaded += 1
                logger.info(f"Successfully downloaded and removed from backlog: {track_name}")
            else:
                logger.warning(f"Failed to download: {track_name}, keeping in backlog for retry")
                # Keep in backlog for retry later
        
        return downloaded

