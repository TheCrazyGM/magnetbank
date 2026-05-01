import hashlib
import re
import urllib.parse
import bencode
import requests
import os
import sys

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import get_db_engine, get_session, Setting


def is_valid_info_hash(info_hash: str) -> bool:
    """Check if the string is a valid v1 (40 hex) or v2 (32 base32) info hash."""
    if not info_hash:
        return False
    # SHA-1 (Hex) - 40 chars
    if re.match(r"^[a-fA-F0-9]{40}$", info_hash):
        return True
    # Base32 (BitTorrent v1) - 32 chars
    if re.match(r"^[a-zA-Z2-7]{32}$", info_hash):
        return True
    return False


def is_safe_url(url: str, allowed_schemes=None) -> bool:
    """Validate that a URL is well-formed and uses an allowed scheme."""
    if not url:
        return False
    if allowed_schemes is None:
        allowed_schemes = ["http", "https", "udp", "ws", "wss"]
    try:
        parsed = urllib.parse.urlparse(url)
        return parsed.scheme in allowed_schemes and bool(parsed.netloc)
    except Exception:
        return False


def sanitize_input(text: str, max_length: int = 255) -> str:
    """Remove HTML tags, control characters, and truncate text."""
    if not text:
        return ""
    # Remove HTML tags using regex
    clean = re.sub(r"<[^>]*?>", "", text)
    # Remove non-printable characters (except basic whitespace)
    clean = "".join(char for char in clean if char.isprintable() or char in "\n\r\t")
    # Truncate
    return clean[:max_length].strip()


def generate_magnet_link(torrent_file):
    """
    Generate a magnet link from a given torrent file.

    Args:
    ----
    torrent_file (bytes): The contents of the torrent file.

    Returns:
    -------
    str: The magnet link generated from the torrent file.
    """
    try:
        # Parse the torrent file using bencode
        torrent_info = bencode.bdecode(torrent_file)
        # Calculate the SHA1 hash of the "info" section of the torrent file
        info_hash = hashlib.sha1(bencode.bencode(torrent_info["info"])).hexdigest()
        # Construct the magnet link using the info hash, name, and tracker URL
        name = torrent_info["info"].get("name", "unknown")
        announce = torrent_info.get("announce", "")
        return f"magnet:?xt=urn:btih:{info_hash}&dn={name}&tr={announce}"
    except Exception as e:
        print(f"Error generating magnet link: {e}")
        return None


def update_announce_urls():
    """
    Update the list of available tracker URLs in the database.
    """
    try:
        url = "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best.txt"
        response = requests.get(url, timeout=10)
        tracker_list = response.text.split("\n")
        stripped_list = [t.strip() for t in tracker_list if t.strip()]

        db_path = os.getenv("SQLITE_DB", "magnetbank.db")
        engine = get_db_engine(db_path)
        session = get_session(engine)

        # In the new schema, we store list as separate entries or a single JSON string?
        # Let's store as a single setting for 'announce_list' for simplicity
        setting = (
            session.query(Setting).filter_by(id="announce_list", key="urls").first()
        )
        import json

        urls_json = json.dumps(stripped_list)

        if setting:
            setting.value = urls_json
        else:
            setting = Setting(id="announce_list", key="urls", value=urls_json)
            session.add(setting)

        session.commit()
        session.close()
    except Exception as e:
        print(f"Error updating tracker list: {e}")
