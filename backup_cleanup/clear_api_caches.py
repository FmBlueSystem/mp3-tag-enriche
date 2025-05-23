#!/usr/bin/env python3
"""Utility script to clear API caches."""
import os
import shutil
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

def clear_api_caches():
    """Clear all API caches to ensure fresh data retrieval."""
    cache_dir = Path("cache/music_apis")
    
    if not cache_dir.exists():
        logging.info(f"Cache directory {cache_dir} doesn't exist. No caches to clear.")
        return
    
    try:
        # Get API names from subdirectories
        api_caches = [d for d in cache_dir.iterdir() if d.is_dir()]
        
        if not api_caches:
            logging.info(f"No API cache subdirectories found in {cache_dir}")
            return
            
        for api_cache in api_caches:
            logging.info(f"Clearing cache for {api_cache.name}")
            try:
                shutil.rmtree(api_cache)
                logging.info(f"Successfully cleared cache for {api_cache.name}")
            except Exception as e:
                logging.error(f"Error clearing cache for {api_cache.name}: {e}")
        
        logging.info("All API caches have been cleared.")
        
    except Exception as e:
        logging.error(f"Error clearing API caches: {e}")

if __name__ == "__main__":
    clear_api_caches()
    print("API caches cleared successfully. Your next search will retrieve fresh data from APIs.")
