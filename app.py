import random
import re
import urllib.parse

import requests
from flask import Flask, jsonify, render_template, request
from flask_paginate import Pagination, get_page_parameter

from config import collection, settings
from utils.helpers import generate_magnet_link

# Create Flask app instance
app = Flask("magnetbank")

# Set number of torrents to display per page
per_page = 99


# Define route for homepage and category pages
@app.route("/")
@app.route("/category/<category>")
def index(category=None):
    """
    Render the homepage or category page with a list of torrents.

    Args:
    ----
    category (str): The category of torrents to display.

    Returns:
    -------
    Rendered HTML template with list of torrents.
    """
    # Get current page number from query parameters
    page = request.args.get(get_page_parameter(), type=int, default=1)

    # Define query to filter torrents by category and search query
    query = {"category": {"$exists": True, "$ne": ""}}
    if category:
        query["category"] = category.upper()
    if q := request.args.get("q", ""):
        query["$or"] = [
            {"hash": {"$regex": q, "$options": "i"}},
            {"file_name": {"$regex": q, "$options": "i"}},
            {"submitted_by": {"$regex": q, "$options": "i"}},
        ]

    # Get total number of torrents matching the query
    total_torrents = collection.count_documents(query)

    # Create pagination object
    pagination = Pagination(
        page=page, total=total_torrents, per_page=per_page, css_framework="bootstrap5"
    )

    # Get cursor to iterate over torrents matching the query
    torrents_cursor = collection.find(query).sort([("timestamp", -1), ("hash", 1)])
    torrents_cursor = torrents_cursor.skip((page - 1) * per_page).limit(per_page)

    # Convert cursor to list of dictionaries
    torrents = list(torrents_cursor)

    # Set header for page
    header = f"{category.upper()} Torrents" if category else "All Torrents"

    # Render HTML template with list of torrents and pagination
    return render_template(
        "torrents.html", torrents=torrents, pagination=pagination, header=header
    )


# Define route for adding a new torrent
@app.route("/add")
def add(category=None):
    """
    Render the add torrent page with a form to submit a magnet link.

    Args:
    ----
    category (str): The category of the torrent being added.

    Returns:
    -------
    Rendered HTML template with form to submit magnet link.
    """
    # Get magnet link and category from query parameters
    magnet = request.args.get("magnet")
    if magnet is not None:
        magnet = urllib.parse.unquote(magnet)
    category = request.args.get("category")

    # Validate magnet link and extract metadata
    if magnet:
        if not re.match(r"magnet:\?xt=urn:btih:[a-fA-F0-9]{40}&", magnet):
            message = "Invalid magnet link"
            torrent_json = None
        else:
            magnet_parts = magnet.split("&")
            info_hash = magnet_parts[0].split(":")[3]
            file_name = urllib.parse.unquote(magnet_parts[1].split("=")[1])
            announce_urls = [
                url.split("=")[1] for url in magnet_parts if url.startswith("tr=")
            ]
            if announce_urls:
                random_announce_url = random.choice(announce_urls)
                random_announce_url = (
                    "http://tracker.openbittorrent.com:80/announce"
                    if random_announce_url == "None"
                    else random_announce_url
                )
            else:
                random_announce_url = "http://tracker.openbittorrent.com:80/announce"
            torrent_metadata = {
                "announce_url": random_announce_url,
                "file_name": file_name,
                "hash": info_hash,
            }

            # Check if torrent already exists in database
            existing_torrent = collection.find_one({"hash": info_hash})
            if existing_torrent:
                message = "Error: Torrent already exists in the database."
                torrent_json = None
            else:
                message = "Magnet link appears valid."
                torrent_json = dict(torrent_metadata)
    else:
        message = "Please add a valid magnet link"
        torrent_json = None

    # Render HTML template with form and validation message
    return render_template(
        "add.html",
        magnet=magnet,
        msg=message,
        torrent_json=torrent_json,
        category=category,
    )


# Define route for converting a torrent file to a magnet link
@app.route("/convert", methods=["POST", "GET"])
def convert(uploaded_file=None):
    """
    Render the convert torrent page with a form to upload a torrent file and generate a magnet link.

    Args:
    ----
    uploaded_file (FileStorage): The uploaded torrent file.

    Returns:
    -------
    Rendered HTML template with form to upload torrent file and generated magnet link.
    """
    # Handle form submission
    if request.method == "POST":
        uploaded_file = request.files["torrent"]

    # Validate uploaded file and generate magnet link
    if (
        not uploaded_file
        or uploaded_file.filename == ""
        or not uploaded_file.filename.endswith(".torrent")
    ):
        message = "Please upload a valid torrent file"
        magnet_link = None
    else:
        torrent_data = uploaded_file.read()
        magnet_link = generate_magnet_link(torrent_data)
        if magnet_link is None:
            message = "Failed to generate magnet link"
        else:
            message = "Magnet link generated successfully"

    # Render HTML template with form and validation message
    return render_template(
        "convert.html",
        msg=message,
        magnet=magnet_link,
    )


# Define route for about page
@app.route("/about")
def about():
    """
    Render the about page with information about the application.

    Returns
    -------
    Rendered HTML template with information about the application.
    """
    # Get total number of torrents in database
    total_torrents = collection.count_documents({})

    # Get latest information from settings collection
    latest_info = settings.find_one({"id": 1})

    # Get current head block number from Hive blockchain API
    url = "https://api.hive.blog"
    headers = {"Content-Type": "application/json"}
    data = {
        "jsonrpc": "2.0",
        "method": "condenser_api.get_dynamic_global_properties",
        "params": [],
        "id": 1,
    }
    response = requests.post(url, headers=headers, json=data)
    json_data = response.json()
    head_block_number = json_data["result"]["head_block_number"]

    # Render HTML template with information about the application
    return render_template(
        "about.html",
        total_torrents=total_torrents,
        latest_info=latest_info,
        current_head_block=head_block_number,
    )


# Define API routes for exporting torrent data
@app.route("/api/json/<q>")
def export_json(q=None):
    """
    Return a JSON response with a list of torrents matching the search query.

    Args:
    ----
    q (str): The search query.

    Returns:
    -------
    JSON response with a list of torrents matching the search query.
    """
    torrent_list = list(
        collection.find({"file_name": {"$regex": q, "$options": "i"}}, {"_id": False})
    )
    return jsonify(torrent_list)


@app.route("/api/hash/<hash>")
def export_hash(q=None):
    """
    Return a JSON response with a list of torrents matching the hash.

    Args:
    ----
    q (str): The hash of the torrent.

    Returns:
    -------
    JSON response with a list of torrents matching the hash.
    """
    torrent_list = list(collection.find({"hash": q}, {"_id": False}))
    return jsonify(torrent_list)


@app.route("/api/user/<q>")
def export_user(q=None):
    """
    Return a JSON response with a list of torrents submitted by the user.

    Args:
    ----
    q (str): The username of the user.

    Returns:
    -------
    JSON response with a list of torrents submitted by the user.
    """
    torrent_list = list(collection.find({"submitted_by": q}, {"_id": False}))
    return jsonify(torrent_list)


# Run Flask app
if __name__ == "__main__":
    app.run(debug=True)
