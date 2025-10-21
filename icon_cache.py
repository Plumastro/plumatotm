#!/usr/bin/env python3
"""
Global Icon Cache System for PLUMATOTM Charts

This module provides a unified icon caching system that ensures icons are loaded
only once and shared between birth chart and radar chart generators.
"""

import os
import logging
from typing import Dict, Optional, Tuple
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

class GlobalIconCache:
    """Global icon cache shared between all chart generators."""
    
    def __init__(self, max_cache_size: int = 100):
        self.cache: Dict[str, np.ndarray] = {}
        self.max_cache_size = max_cache_size
        self.access_count: Dict[str, int] = {}
        self.icons_dir = "icons"
        
    def get_cache_key(self, icon_path: str, size: int) -> str:
        """Generate a unique cache key for an icon."""
        return f"{icon_path}_{size}"
    
    def load_icon(self, icon_path: str, size: int) -> Optional[np.ndarray]:
        """
        Load an icon with caching. Returns the icon as a numpy array.
        
        Args:
            icon_path: Path to the icon file
            size: Desired size for the icon
            
        Returns:
            Icon as numpy array or None if loading failed
        """
        cache_key = self.get_cache_key(icon_path, size)
        
        # Check if already cached
        if cache_key in self.cache:
            self.access_count[cache_key] = self.access_count.get(cache_key, 0) + 1
            logger.debug(f"Loaded icon from cache: {icon_path} ({size}x{size})")
            return self.cache[cache_key]
        
        # Load and cache the icon
        if not os.path.exists(icon_path):
            logger.warning(f"Icon file not found: {icon_path}")
            return None
            
        try:
            # Load and resize icon with high quality
            img = Image.open(icon_path).convert("RGBA")
            img = img.resize((size, size), Image.Resampling.LANCZOS)
            icon_array = np.asarray(img)
            
            # Store in cache
            self.cache[cache_key] = icon_array
            self.access_count[cache_key] = 1
            
            # Cleanup cache if it's too large
            self._cleanup_cache()
            
            logger.debug(f"Loaded and cached icon: {icon_path} ({size}x{size})")
            return icon_array
            
        except Exception as e:
            logger.warning(f"Could not load icon {icon_path}: {e}")
            return None
    
    def _cleanup_cache(self):
        """Remove least recently used icons if cache is too large."""
        if len(self.cache) <= self.max_cache_size:
            return
            
        # Remove least accessed icons
        sorted_items = sorted(self.access_count.items(), key=lambda x: x[1])
        items_to_remove = len(self.cache) - self.max_cache_size
        
        for i in range(items_to_remove):
            cache_key = sorted_items[i][0]
            if cache_key in self.cache:
                del self.cache[cache_key]
                del self.access_count[cache_key]
                logger.debug(f"Removed from cache: {cache_key}")
    
    def clear_cache(self):
        """Clear all cached icons."""
        self.cache.clear()
        self.access_count.clear()
        logger.debug("Icon cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "cached_icons": len(self.cache),
            "max_cache_size": self.max_cache_size,
            "total_accesses": sum(self.access_count.values())
        }

# Global instance shared by all chart generators
_global_icon_cache = GlobalIconCache()

def get_global_icon_cache() -> GlobalIconCache:
    """Get the global icon cache instance."""
    return _global_icon_cache

def load_icon(icon_path: str, size: int) -> Optional[np.ndarray]:
    """
    Load an icon using the global cache.
    
    Args:
        icon_path: Path to the icon file
        size: Desired size for the icon
        
    Returns:
        Icon as numpy array or None if loading failed
    """
    return _global_icon_cache.load_icon(icon_path, size)

def clear_global_cache():
    """Clear the global icon cache."""
    _global_icon_cache.clear_cache()

def get_cache_stats() -> Dict[str, int]:
    """Get global cache statistics."""
    return _global_icon_cache.get_cache_stats()
