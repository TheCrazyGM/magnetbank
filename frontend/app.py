import re
import urllib.parse
import os
import sys
import json

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, render_template, request, g
from flask_paginate import Pagination, get_page_parameter
from sqlalchemy import or_, desc

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import get_db_engine, get_session, Torrent, Setting
from utils.helpers import generate_magnet_link, update_announce_urls

# Load configuration from environment
from dotenv import load_dotenv

load_dotenv()

ADMIN = os.getenv("ADMIN_ACCOUNT")
HIVE_NODE = os.getenv("HIVE_NODE")
DB_PATH = os.getenv("SQLITE_DB", "magnetbank.db")

# Create a scheduler instance
scheduler = BackgroundScheduler()


# Define a function that wraps `update_announce_urls`
def update_announce_urls_job():
    try:
        update_announce_urls()
    except Exception as e:
        print(f"Error updating announce URLs: {e}")


# Run the job once on start
update_announce_urls_job()

# Schedule the job to run every day at 2am
scheduler.add_job(update_announce_urls_job, "cron", hour=2)
scheduler.start()

# Create Flask app instance
base_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    "magnetbank",
    template_folder=os.path.join(base_dir, "templates"),
    static_folder=os.path.join(base_dir, "static"),
)

# Database setup
engine = get_db_engine(DB_PATH)


@app.before_request
def before_request():
    g.db = get_session(engine)


@app.teardown_request
def teardown_request(exception=None):
    db = getattr(g, "db", None)
    if db is not None:
        db.close()


# Set number of torrents to display per page
per_page = 99


@app.route("/")
@app.route("/category/<category>")
def index(category=None):
    page = request.args.get(get_page_parameter(), type=int, default=1)

    query = g.db.query(Torrent)

    if category:
        query = query.filter(Torrent.category == category.upper())

    if q := request.args.get("q", ""):
        search_filter = or_(
            Torrent.hash.ilike(f"%{q}%"),
            Torrent.file_name.ilike(f"%{q}%"),
            Torrent.submitted_by.ilike(f"%{q}%"),
        )
        query = query.filter(search_filter)

    total_torrents = query.count()

    pagination = Pagination(
        page=page, total=total_torrents, per_page=per_page, css_framework="bootstrap5"
    )

    torrents_objs = (
        query.order_by(desc(Torrent.timestamp), Torrent.hash)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    torrents = [t.to_dict() for t in torrents_objs]
    header = f"{category.upper()} Torrents" if category else "All Torrents"

    return render_template(
        "list.html", torrents=torrents, pagination=pagination, header=header
    )


@app.route("/category/<category>/<filename>")
def serve_torrent(category, filename):
    torrent_obj = (
        g.db.query(Torrent)
        .filter(
            Torrent.category == category.upper(),
            or_(Torrent.file_name == filename, Torrent.hash == filename),
        )
        .first()
    )

    torrent = torrent_obj.to_dict() if torrent_obj else None
    return render_template("details.html", torrent=torrent)


@app.route("/user/<username>")
def serve_user(username):
    page = request.args.get(get_page_parameter(), type=int, default=1)

    query = g.db.query(Torrent).filter(Torrent.submitted_by == username)
    total_torrents = query.count()

    pagination = Pagination(
        page=page, total=total_torrents, per_page=per_page, css_framework="bootstrap5"
    )

    torrents_objs = (
        query.order_by(desc(Torrent.timestamp), Torrent.hash)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    torrents = [t.to_dict() for t in torrents_objs]
    header = f"{username}'s Profile"

    return render_template(
        "user.html",
        torrents=torrents,
        pagination=pagination,
        header=header,
        total_torrents=total_torrents,
        username=username,
    )


@app.route("/add")
def add(category=None):
    magnet = request.args.get("magnet")
    if magnet is not None:
        magnet = urllib.parse.unquote(magnet)
    category = request.args.get("category")

    message = "Please add a valid magnet link"
    torrent_json = None

    if magnet:
        if not re.match(r"magnet:\?xt=urn:btih:[a-fA-F0-9]{40}&", magnet):
            message = "Invalid magnet link"
        else:
            magnet_parts = magnet.split("&")
            info_hash = magnet_parts[0].split(":")[3].upper()
            file_name = urllib.parse.unquote(magnet_parts[1].split("=")[1])

            # Simple metadata extraction
            announce_url = "http://tracker.openbittorrent.com:80/announce"
            for part in magnet_parts:
                if part.startswith("tr="):
                    url = part.split("=")[1]
                    if url and url != "None":
                        announce_url = url
                        break

            # Check if torrent already exists
            existing = g.db.query(Torrent).filter_by(hash=info_hash).first()
            if existing:
                message = "Error: Torrent already exists in the database."
            else:
                message = "Magnet link appears valid."
                torrent_json = {
                    "announce_url": announce_url,
                    "file_name": file_name,
                    "hash": info_hash,
                }

    return render_template(
        "add.html",
        magnet=magnet,
        msg=message,
        torrent_json=torrent_json,
        category=category,
    )


@app.route("/convert", methods=["POST", "GET"])
def convert(uploaded_file=None):
    if request.method == "POST":
        uploaded_file = request.files["torrent"]

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
        message = (
            "Magnet link generated successfully"
            if magnet_link
            else "Failed to generate magnet link"
        )

    return render_template(
        "convert.html",
        msg=message,
        magnet=magnet_link,
    )


@app.route("/about")
def about():
    total_torrents = g.db.query(Torrent).count()

    # Get all info settings
    info_settings = g.db.query(Setting).filter_by(id="info").all()
    latest_info = {}
    for s in info_settings:
        try:
            latest_info[s.key] = int(s.value)
        except (ValueError, TypeError):
            latest_info[s.key] = s.value

    # Ensure critical keys exist as integers for template calculations
    for key in ["last_block", "genisys", "head_block"]:
        if key not in latest_info or not isinstance(latest_info[key], int):
            latest_info[key] = 0

    # Get Hive head block
    current_head_block = 0
    try:
        hive_url = HIVE_NODE or "https://api.hive.blog"
        response = requests.post(
            hive_url,
            json={
                "jsonrpc": "2.0",
                "method": "condenser_api.get_dynamic_global_properties",
                "params": [],
                "id": 1,
            },
            timeout=10,
        )
        if response.status_code == 200:
            res_json = response.json()
            if "result" in res_json and "head_block_number" in res_json["result"]:
                current_head_block = int(res_json["result"]["head_block_number"])
    except Exception as e:
        print(f"Error fetching live head block: {e}")
        # If we can't get actual head, use the head_block from our DB
        current_head_block = latest_info.get("head_block", 0)

    # Final fallback if still 0
    if current_head_block == 0:
        current_head_block = latest_info.get("last_block", 0)

    return render_template(
        "about.html",
        total_torrents=total_torrents,
        latest_info=latest_info,
        current_head_block=current_head_block,
    )


@app.route("/admin")
def admin():
    return render_template("admin.html", admin=ADMIN)


# API routes
@app.route("/api/json/<q>")
def export_json(q=None):
    results = g.db.query(Torrent).filter(Torrent.file_name.ilike(f"%{q}%")).all()
    return jsonify([t.to_dict() for t in results])


@app.route("/api/hash/<q>")
def export_hash(q=None):
    results = g.db.query(Torrent).filter(Torrent.hash == q.upper()).all()
    return jsonify([t.to_dict() for t in results])


@app.route("/api/user/<q>")
def export_user(q=None):
    results = g.db.query(Torrent).filter(Torrent.submitted_by == q).all()
    return jsonify([t.to_dict() for t in results])


@app.route("/api/generate/<q>")
def generate_torrent(q=None):
    search_filter = or_(
        Torrent.hash.ilike(f"%{q}%"),
        Torrent.file_name.ilike(f"%{q}%"),
        Torrent.submitted_by.ilike(f"%{q}%"),
    )
    results = g.db.query(Torrent).filter(search_filter).all()

    json_data = []
    for torrent in results:
        magnet_link = (
            f"magnet:?xt=urn:btih:{torrent.hash}"
            f"&dn={torrent.file_name}"
            f"&tr={torrent.announce_url}"
        )
        json_data.append({"magnet_link": magnet_link})
    return jsonify(json_data)


@app.route("/api/announce_urls")
def announce_urls_api():
    # Fetch all announce URLs from settings
    result = g.db.query(Setting).filter_by(id="announce_list", key="urls").first()
    if result:
        return jsonify(json.loads(result.value))
    return jsonify([])


if __name__ == "__main__":
    app.run(debug=True)
