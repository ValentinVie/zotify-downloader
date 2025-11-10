"""
Backlog Manager
Manages the queue of tracks waiting to be downloaded
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class BacklogManager:
    """Manages backlog of tracks to download"""
    
    def __init__(self, backlog_file: str = "/app/data/backlog.json"):
        self.backlog_file = Path(backlog_file)
        self.backlog_file.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_backlog_exists()
    
    def _ensure_backlog_exists(self):
        """Create backlog file if it doesn't exist"""
        if not self.backlog_file.exists():
            self._write_backlog([])
    
    def _read_backlog(self) -> List[Dict]:
        """Read backlog from file"""
        try:
            with open(self.backlog_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _write_backlog(self, backlog: List[Dict]):
        """Write backlog to file"""
        with open(self.backlog_file, 'w', encoding='utf-8') as f:
            json.dump(backlog, f, indent=2, ensure_ascii=False)
    
    def add_track(self, track_info: Dict) -> bool:
        """
        Add track to backlog if not already present
        Returns True if added, False if already exists
        """
        backlog = self._read_backlog()
        track_id = track_info["track_id"]
        
        # Check if track already in backlog
        if any(item["track_id"] == track_id for item in backlog):
            return False
        
        # Add timestamp if not present
        if "added_at" not in track_info:
            track_info["added_at"] = datetime.now().isoformat()
        
        backlog.append(track_info)
        self._write_backlog(backlog)
        return True
    
    def get_next_track(self) -> Optional[Dict]:
        """Get next track from backlog (FIFO)"""
        backlog = self._read_backlog()
        if not backlog:
            return None
        
        return backlog[0]
    
    def remove_track(self, track_id: str) -> bool:
        """Remove track from backlog by track_id"""
        backlog = self._read_backlog()
        original_length = len(backlog)
        backlog = [item for item in backlog if item["track_id"] != track_id]
        
        if len(backlog) < original_length:
            self._write_backlog(backlog)
            return True
        return False
    
    def get_all_tracks(self) -> List[Dict]:
        """Get all tracks in backlog"""
        return self._read_backlog()
    
    def clear_backlog(self):
        """Clear entire backlog"""
        self._write_backlog([])
    
    def get_backlog_size(self) -> int:
        """Get number of tracks in backlog"""
        return len(self._read_backlog())

