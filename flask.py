from flask import Flask, request, jsonify
from datetime import datetime, timezone
import uuid

app = Flask(__name__)

# Хранение объявлений в памяти: {id: {title, description, created_at, owner}}
listings = {}


@app.route("/")
def index():
    return jsonify({
        "message": "Listing API",
        "endpoints": {
            "POST /listings": "Create a listing",
            "GET /listings": "Get all listings",
            "GET /listings/<id>": "Get a single listing",
            "PUT /listings/<id>": "Update a listing",
            "DELETE /listings/<id>": "Delete a listing"
        }
    })


@app.route("/listings", methods=["POST"])
def create_listing():
    data = request.get_json()
    if not data or not all(k in data for k in ("title", "description", "owner")):
        return jsonify({"error": "Missing required fields: title, description, owner"}), 400

    listing_id = str(uuid.uuid4())
    listing = {
        "id": listing_id,
        "title": data["title"],
        "description": data["description"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "owner": data["owner"],
    }
    listings[listing_id] = listing
    return jsonify(listing), 201


@app.route("/listings", methods=["GET"])
def get_listings():
    return jsonify(list(listings.values()))


@app.route("/listings/<listing_id>", methods=["GET"])
def get_listing(listing_id):
    listing = listings.get(listing_id)
    if not listing:
        return jsonify({"error": "Listing not found"}), 404
    return jsonify(listing)


@app.route("/listings/<listing_id>", methods=["PUT"])
def update_listing(listing_id):
    listing = listings.get(listing_id)
    if not listing:
        return jsonify({"error": "Listing not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    for field in ("title", "description", "owner"):
        if field in data:
            listing[field] = data[field]

    listings[listing_id] = listing
    return jsonify(listing)


@app.route("/listings/<listing_id>", methods=["DELETE"])
def delete_listing(listing_id):
    if listing_id not in listings:
        return jsonify({"error": "Listing not found"}), 404

    deleted = listings.pop(listing_id)
    return jsonify(deleted)


if __name__ == "__main__":
    app.run(debug=True)
