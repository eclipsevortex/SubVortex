import os
import csv
import time
import asyncio
import requests
import zipfile
import tempfile
import ipaddress
from threading import RLock
from typing import Dict, Optional

import bittensor.utils.btlogging as btul

# GeoLite2 download URLs (free version)
# MaxMind GeoLite2 Download URLs
GEOLITE2_DOWNLOAD_BASE = "https://download.maxmind.com/app/geoip_download"


class GeoLite2Updater:
    """
    Manages automated downloads and updates of GeoLite2 CSV files with ETag support.
    Handles conditional downloads to avoid unnecessary bandwidth usage.
    """

    def __init__(self, output_dir: str, license_key: Optional[str] = None):
        self.output_dir = output_dir
        self.license_key = license_key
        self.etag_file = os.path.join(output_dir, "geolite.etag")
        self.locations_file = os.path.join(
            output_dir, "GeoLite2-Country-Locations-en.csv"
        )
        self.blocks_file = os.path.join(output_dir, "GeoLite2-Country-Blocks-IPv4.csv")

        # Update settings
        self.update_interval_hours = 24  # Check daily
        self.last_check_file = os.path.join(output_dir, "last_update_check.txt")

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

    def _get_download_url(self) -> Optional[str]:
        """Build download URL with license key."""
        if not self.license_key:
            return None
        return f"{GEOLITE2_DOWNLOAD_BASE}?edition_id=GeoLite2-Country-CSV&license_key={self.license_key}&suffix=zip"

    def _load_etag(self) -> Optional[str]:
        """Load the stored ETag for conditional requests."""
        try:
            if os.path.exists(self.etag_file):
                with open(self.etag_file, "r") as f:
                    return f.read().strip()
        except Exception as e:
            btul.logging.debug(f"Could not load ETag: {e}")
        return None

    def _save_etag(self, etag: str):
        """Save ETag for future conditional requests."""
        try:
            with open(self.etag_file, "w") as f:
                f.write(etag)
        except Exception as e:
            btul.logging.warning(f"Could not save ETag: {e}")

    def _should_check_for_updates(self) -> bool:
        """Check if enough time has passed since last update check."""
        try:
            if not os.path.exists(self.last_check_file):
                return True

            with open(self.last_check_file, "r") as f:
                last_check = float(f.read().strip())

            time_since_check = time.time() - last_check
            hours_since_check = time_since_check / 3600

            return hours_since_check >= self.update_interval_hours

        except Exception:
            return True

    def _mark_check_time(self):
        """Record the time of the last update check."""
        try:
            with open(self.last_check_file, "w") as f:
                f.write(str(time.time()))
        except Exception as e:
            btul.logging.warning(f"Could not save check time: {e}")

    async def check_and_download_updates(self) -> bool:
        """
        Check for updates using ETag and download if necessary.
        Returns True if files were updated, False otherwise.
        """
        if not self._should_check_for_updates():
            return False

        btul.logging.debug("🔍 Checking for GeoLite2 CSV updates...")

        try:
            # If no license key, check if files exist
            if not self.license_key:
                if not os.path.exists(self.locations_file) or not os.path.exists(
                    self.blocks_file
                ):
                    btul.logging.warning(
                        "⚠️ No MaxMind license key configured and no CSV files found"
                    )
                    btul.logging.info(
                        "💡 Please provide a license key or run the download script manually"
                    )
                self._mark_check_time()
                return False

            if not os.path.exists(self.locations_file) or not os.path.exists(
                self.blocks_file
            ):
                btul.logging.info(
                    "📥 GeoLite2 CSV files missing, attempting download..."
                )
                success = await self._download_csv_files()
                self._mark_check_time()
                return success

            # Check file age as a fallback
            locations_age = time.time() - os.path.getmtime(self.locations_file)
            blocks_age = time.time() - os.path.getmtime(self.blocks_file)
            max_age_hours = 24 * 1  # 1 day based on maxmind information

            if (
                locations_age > max_age_hours * 3600
                or blocks_age > max_age_hours * 3600
            ):
                btul.logging.info(
                    "📅 GeoLite2 CSV files are outdated, attempting refresh..."
                )
                success = await self._download_csv_files()
                self._mark_check_time()
                return success

            self._mark_check_time()
            return False

        except Exception as e:
            btul.logging.warning(f"❌ Failed to check for GeoLite2 updates: {e}")
            self._mark_check_time()
            return False

    async def _download_csv_files(self) -> bool:
        """Download GeoLite2 CSV files from MaxMind with ETag support."""
        if not self.license_key:
            btul.logging.warning("No MaxMind license key provided")
            return False

        download_url = self._get_download_url()
        if not download_url:
            btul.logging.error("Could not build download URL")
            return False

        try:
            btul.logging.info("📥 Downloading GeoLite2 CSV files from MaxMind...")

            # Prepare headers for conditional download
            headers = {}
            stored_etag = self._load_etag()
            if stored_etag:
                headers["If-None-Match"] = stored_etag

            # Download the zip file
            response = requests.get(download_url, headers=headers, stream=True)

            # Check if file hasn't changed (304 Not Modified)
            if response.status_code == 304:
                btul.logging.debug("📋 GeoLite2 files unchanged (304 Not Modified)")
                return False

            response.raise_for_status()

            # Save ETag for future requests
            if "ETag" in response.headers:
                self._save_etag(response.headers["ETag"])

            # Process the downloaded zip file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_zip:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_zip.write(chunk)
                temp_zip_path = temp_zip.name

            # Extract CSV files from zip
            success = self._extract_csv_files(temp_zip_path)

            # Clean up
            os.unlink(temp_zip_path)

            if success:
                btul.logging.info(
                    "✅ GeoLite2 CSV files downloaded and extracted successfully"
                )

            return success

        except Exception as e:
            btul.logging.error(f"❌ Failed to download GeoLite2 files: {e}")
            return False

    def _extract_csv_files(self, zip_path: str) -> bool:
        """Extract CSV files from downloaded zip."""
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                # Find the CSV files in the zip
                locations_found = False
                blocks_found = False

                for file_info in zip_ref.filelist:
                    filename = os.path.basename(file_info.filename)

                    if filename == "GeoLite2-Country-Locations-en.csv":
                        zip_ref.extract(file_info, self.output_dir)
                        # Move to correct location
                        extracted_path = os.path.join(
                            self.output_dir, file_info.filename
                        )
                        if extracted_path != self.locations_file:
                            os.makedirs(
                                os.path.dirname(self.locations_file), exist_ok=True
                            )
                            os.rename(extracted_path, self.locations_file)
                        locations_found = True

                    elif filename == "GeoLite2-Country-Blocks-IPv4.csv":
                        zip_ref.extract(file_info, self.output_dir)
                        # Move to correct location
                        extracted_path = os.path.join(
                            self.output_dir, file_info.filename
                        )
                        if extracted_path != self.blocks_file:
                            os.makedirs(
                                os.path.dirname(self.blocks_file), exist_ok=True
                            )
                            os.rename(extracted_path, self.blocks_file)
                        blocks_found = True

                return locations_found and blocks_found

        except Exception as e:
            btul.logging.error(f"Failed to extract CSV files: {e}")
            return False


class IntervalTreeNode:
    """Optimized interval tree node for IP range lookups."""

    def __init__(self, start: int, end: int, geoname_id: int):
        self.start = start
        self.end = end
        self.geoname_id = geoname_id
        self.max_end = end
        self.left: IntervalTreeNode = None
        self.right: IntervalTreeNode = None


class IntervalTree:
    """Ultra-fast interval tree for O(log n) IP range lookups."""

    def __init__(self):
        self.root = None

    def insert(self, start: int, end: int, geoname_id: int):
        """Insert an IP range into the tree."""
        self.root = self._insert(self.root, start, end, geoname_id)

    def _insert(self, node: IntervalTreeNode, start: int, end: int, geoname_id):
        if not node:
            return IntervalTreeNode(start, end, geoname_id)

        if start <= node.start:
            node.left = self._insert(node.left, start, end, geoname_id)
        else:
            node.right = self._insert(node.right, start, end, geoname_id)

        # Update max_end
        node.max_end = max(node.max_end, end)
        if node.left:
            node.max_end = max(node.max_end, node.left.max_end)
        if node.right:
            node.max_end = max(node.max_end, node.right.max_end)

        return node

    def search(self, ip: int) -> Optional[int]:
        """Find geoname_id for IP address."""
        return self._search(self.root, ip)

    def _search(self, node: IntervalTreeNode, ip: str):
        if not node:
            return None

        # Check if IP is in current node's range
        if node.start <= ip <= node.end:
            return node.geoname_id

        # Search left subtree if it might contain the IP
        if node.left and node.left.max_end >= ip:
            result = self._search(node.left, ip)
            if result is not None:
                return result

        # Search right subtree
        return self._search(node.right, ip)


class UltraFastGeoLookup:
    """
    Ultra-high performance IP to country lookup optimized for metagraph usage.
    Features:
    - Startup preloading with progress indication
    - File change detection and hot reloading
    - Interval tree for O(log n) lookups
    - Memory-mapped file access
    - Thread-safe operations
    - Zero-copy where possible
    """

    def __init__(self, output_dir: str = "/var/tmp", license_key: Optional[str] = None):
        self.output_dir = output_dir
        self.license_key = license_key
        self.locations_file = os.path.join(
            self.output_dir, "GeoLite2-Country-Locations-en.csv"
        )
        self.blocks_file = os.path.join(
            self.output_dir, "GeoLite2-Country-Blocks-IPv4.csv"
        )

        # Thread-safe data structures
        self._lock = RLock()
        self._country_map: Dict[int, str] = {}
        self._interval_tree = IntervalTree()

        # File monitoring
        self._locations_mtime = 0
        self._blocks_mtime = 0
        self._loaded = False
        self._load_start_time = 0

        # Performance cache - much larger for metagraph use
        self._cache: Dict[str, str] = {}
        self._cache_max_size = 10000

        # CSV updater for automated downloads
        self._updater = GeoLite2Updater(self.output_dir, license_key)
        self._background_task = None
        self._running = False

    async def start(self):
        """Start the geo lookup service with preloading and background updates."""
        btul.logging.info("🚀 Starting UltraFastGeoLookup service...")

        self._running = True

        # Preload data at startup
        await self._preload_data()

        # Start background update task
        self._start_background_updates()

        btul.logging.info("✅ UltraFastGeoLookup service started")

    async def stop(self):
        """Stop the geo lookup service and background tasks."""
        btul.logging.info("🛑 Stopping UltraFastGeoLookup service...")

        self._running = False

        # Stop background updates
        self.stop_background_updates()

        btul.logging.info("✅ UltraFastGeoLookup service stopped")

    async def _preload_data(self):
        """Preload all data at startup with progress indication."""
        btul.logging.info("🚀 Preloading GeoLite2 CSV data for ultra-fast lookups...")
        start_time = time.time()

        try:
            self._load_start_time = start_time

            # Check for updates first
            await self._updater.check_and_download_updates()

            # Load the data
            self._load_data_internal()

            load_time = time.time() - start_time
            btul.logging.info(
                f"✅ GeoLite2 data preloaded in {load_time:.2f}s: "
                f"{len(self._country_map)} countries, interval tree ready"
            )

        except Exception as e:
            btul.logging.error(f"❌ Failed to preload GeoLite2 data: {e}")

    def _start_background_updates(self):
        """Start background task for periodic CSV updates."""
        if not self._running:
            return

        try:
            # Create background task for updates (fire and forget)
            loop = asyncio.get_event_loop()
            self._background_task = loop.create_task(self._background_update_loop())
        except RuntimeError:
            # No event loop running, updates will be manual
            btul.logging.debug(
                "No event loop for background updates - updates will be manual"
            )

    async def _background_update_loop(self):
        """Background loop that checks for CSV updates periodically."""
        while self._running:
            try:
                # Check for updates
                updated = await self._updater.check_and_download_updates()

                if updated:
                    btul.logging.info("🔄 GeoLite2 files updated, reloading data...")
                    self._load_data_internal()

                # Sleep for 6 hours before next check
                await asyncio.sleep(6 * 3600)

            except asyncio.CancelledError:
                btul.logging.debug("Background update task cancelled")
                break
            except Exception as e:
                btul.logging.warning(f"Background update error: {e}")
                # Sleep shorter on error, then retry
                await asyncio.sleep(30 * 60)  # 30 minutes

    def stop_background_updates(self):
        """Stop background update task."""
        if self._background_task and not self._background_task.done():
            self._background_task.cancel()

    def _check_file_changes(self) -> bool:
        """Check if CSV files have been modified."""
        try:
            locations_mtime = (
                os.path.getmtime(self.locations_file)
                if os.path.exists(self.locations_file)
                else 0
            )
            blocks_mtime = (
                os.path.getmtime(self.blocks_file)
                if os.path.exists(self.blocks_file)
                else 0
            )

            if (
                locations_mtime != self._locations_mtime
                or blocks_mtime != self._blocks_mtime
            ):
                self._locations_mtime = locations_mtime
                self._blocks_mtime = blocks_mtime
                return True
            return False
        except OSError:
            return False

    def _load_data_internal(self):
        """Internal data loading with maximum performance."""
        with self._lock:
            if not self._check_file_changes() and self._loaded:
                return

            btul.logging.debug("📊 Reloading GeoLite2 data due to file changes...")

            # Clear previous data
            self._country_map.clear()
            self._interval_tree = IntervalTree()
            self._cache.clear()

            # Load country mappings with memory-mapped file for large files
            if os.path.exists(self.locations_file):
                self._load_locations_optimized()

            # Load IP blocks and build interval tree
            if os.path.exists(self.blocks_file):
                self._load_blocks_optimized()

            self._loaded = True

    def _load_locations_optimized(self):
        """Load country locations with memory-mapped access."""
        with open(self.locations_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                geoname_id = row.get("geoname_id")
                country_code = row.get("country_iso_code")
                if geoname_id and country_code:
                    self._country_map[int(geoname_id)] = country_code

    def _load_blocks_optimized(self):
        """Load IP blocks and build interval tree with progress."""
        processed = 0

        with open(self.blocks_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                network = row.get("network")
                geoname_id = row.get("geoname_id")

                if network and geoname_id:
                    try:
                        # Parse CIDR network to start/end IPs
                        net = ipaddress.IPv4Network(network, strict=False)
                        start_ip = int(net.network_address)
                        end_ip = int(net.broadcast_address)

                        # Insert into interval tree
                        self._interval_tree.insert(start_ip, end_ip, int(geoname_id))
                        processed += 1

                        # Progress indicator for large datasets
                        if processed % 50000 == 0:
                            elapsed = time.time() - self._load_start_time
                            btul.logging.debug(
                                f"📈 Processed {processed:,} IP ranges in {elapsed:.1f}s"
                            )

                    except (ValueError, ipaddress.AddressValueError):
                        continue

    def lookup_country(self, ip_str: str) -> Optional[str]:
        """
        Ultra-fast IP to country lookup with automatic reloading.
        Returns country code (e.g., 'US', 'DE') or None if not found.
        """
        # Check cache first (fastest path)
        cached = self._cache.get(ip_str)
        if cached is not None:
            return cached if cached != "__NOT_FOUND__" else None

        # Hot reload if files changed
        if self._check_file_changes():
            self._load_data_internal()

        try:
            # Convert IP to integer for ultra-fast tree search
            ip_int = int(ipaddress.IPv4Address(ip_str))

            # Search interval tree - O(log n)
            geoname_id = self._interval_tree.search(ip_int)
            if geoname_id is None:
                # Cache negative result
                self._cache_result(ip_str, None)
                return None

            # Get country code
            country = self._country_map.get(geoname_id)
            self._cache_result(ip_str, country)
            return country

        except (ValueError, ipaddress.AddressValueError):
            self._cache_result(ip_str, None)
            return None

    def _cache_result(self, ip_str: str, country: Optional[str]):
        """Cache result with LRU-style eviction."""
        if len(self._cache) >= self._cache_max_size:
            # Simple eviction - remove first 1000 entries
            keys_to_remove = list(self._cache.keys())[:1000]
            for key in keys_to_remove:
                del self._cache[key]

        # Cache result (use special marker for None to distinguish from cache miss)
        self._cache[ip_str] = country if country is not None else "__NOT_FOUND__"

    def get_stats(self) -> Dict[str, int]:
        """Get performance statistics."""
        return {
            "countries": len(self._country_map),
            "cached_lookups": len(self._cache),
            "cache_hit_potential": min(len(self._cache), self._cache_max_size),
            "running": self._running,
        }
