#!/usr/bin/env python3
"""
Download Swiss Ephemeris files for astrological calculations
"""

import os
import urllib.request
import zipfile
import shutil

def download_ephemeris():
    """Download and extract Swiss Ephemeris files"""
    
    # Create ephemeris directory
    ephe_dir = "ephe"
    if not os.path.exists(ephe_dir):
        os.makedirs(ephe_dir)
    
    print("📥 Downloading Swiss Ephemeris files...")
    
    # Swiss Ephemeris files URL (public domain)
    ephemeris_url = "https://www.astro.com/ftp/swisseph/ephe/archive/sweph_18.tar.gz"
    
    try:
        # Download the ephemeris files
        print("⬇️  Downloading sweph_18.tar.gz...")
        urllib.request.urlretrieve(ephemeris_url, "sweph_18.tar.gz")
        
        # Extract the files
        print("📦 Extracting ephemeris files...")
        import tarfile
        with tarfile.open("sweph_18.tar.gz", "r:gz") as tar:
            tar.extractall(ephe_dir)
        
        # Clean up
        os.remove("sweph_18.tar.gz")
        
        print("✅ Swiss Ephemeris files downloaded successfully!")
        print(f"📁 Files saved to: {ephe_dir}/")
        
        # List downloaded files
        files = os.listdir(ephe_dir)
        print(f"📋 Downloaded {len(files)} ephemeris files")
        
        return True
        
    except Exception as e:
        print(f"❌ Error downloading ephemeris files: {e}")
        return False

if __name__ == "__main__":
    download_ephemeris()
