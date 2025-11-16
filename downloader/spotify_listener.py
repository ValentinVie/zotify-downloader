"""
Spotify API Listener Service
Monitors the listening account's currently playing track using Spotify Web API
"""
import os
import time
import requests
import logging
from typing import Optional, Dict
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class SpotifyListener:
    """Monitors Spotify Web API for currently playing tracks"""
    
    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token: Optional[str] = None
        self.token_expires_at: float = 0
        self.last_track_id: Optional[str] = None
        
    def _get_access_token(self) -> str:
        """Get or refresh access token"""
        if self.access_token and time.time() < self.token_expires_at:
            # Type assertion: we know it's not None because of the check above
            assert self.access_token is not None
            return self.access_token
        
        logger.debug("Refreshing access token")
        url = "https://accounts.spotify.com/api/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            access_token = token_data.get("access_token")
            if not access_token:
                raise ValueError("No access token in response")
            
            self.access_token = access_token
            expires_in = token_data.get("expires_in", 3600)
            self.token_expires_at = time.time() + expires_in - 60  # Refresh 1 min early
            
            logger.debug(f"Access token refreshed, expires in {expires_in}s")
            return access_token
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to refresh access token: {e}")
            raise
    
    def _make_api_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make authenticated API request"""
        token = self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"https://api.spotify.com/v1{endpoint}"
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 204:  # No content (not playing)
            return None
            
        response.raise_for_status()
        return response.json()
    
    def get_currently_playing(self, market: Optional[str] = None) -> Optional[Dict]:
        """
        Get currently playing track from listening account
        
        Reference: https://developer.spotify.com/documentation/web-api/reference/get-information-about-the-users-current-playback
        
        Args:
            market: An ISO 3166-1 alpha-2 country code. Provide this parameter if you want
                   to apply Track Relinking. If not specified, the user's market is used.
        
        Returns:
            Track info dict or None if nothing is playing
        """
        try:
            params = {"market": market} if market else None
            
            data = self._make_api_request("/me/player/currently-playing", params=params)
            
            if not data or "item" not in data or data["item"] is None:
                return None
            
            # Check if it's actually a track (not an episode)
            currently_playing_type = data.get("currently_playing_type", "track")
            if currently_playing_type != "track":
                return None
            
            track = data["item"]
            
            # Extract track information according to API response structure
            return {
                "track_id": track["id"],
                "track_name": track["name"],
                "artists": [artist["name"] for artist in track.get("artists", [])],
                "album": track.get("album", {}).get("name", "Unknown Album"),
                "spotify_url": track.get("external_urls", {}).get("spotify", ""),
                "uri": track.get("uri", ""),
                "timestamp": datetime.now().isoformat(),
                "is_playing": data.get("is_playing", False),
                "progress_ms": data.get("progress_ms", 0),
                "duration_ms": track.get("duration_ms", 0)
            }
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 204:
                # 204 No Content means no active playback
                logger.debug("No active playback (204 No Content)")
                return None
            logger.warning(f"HTTP error getting currently playing track: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting currently playing track: {e}", exc_info=True)
            return None
    
    def check_for_new_track(self) -> Optional[Dict]:
        """
        Check if a new track is playing (different from last checked)
        Returns track info if new track detected, None otherwise
        """
        current_track = self.get_currently_playing()
        
        if not current_track or not current_track.get("is_playing"):
            return None
            
        track_id = current_track["track_id"]
        
        # If this is a new track, update last_track_id and return it
        if track_id != self.last_track_id:
            self.last_track_id = track_id
            return current_track
            
        return None

