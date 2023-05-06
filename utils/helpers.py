import hashlib

import bencode


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
    # Parse the torrent file using bencode
    torrent_info = bencode.bdecode(torrent_file)
    # Calculate the SHA1 hash of the "info" section of the torrent file
    info_hash = hashlib.sha1(bencode.bencode(torrent_info["info"])).hexdigest()
    # Construct the magnet link using the info hash, name, and tracker URL
    return f"magnet:?xt=urn:btih:{info_hash}&dn={torrent_info['info']['name']}&tr={torrent_info.get('announce')}"
