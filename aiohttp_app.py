from aiohttp import web
import json
import uuid
from datetime import datetime, timezone

# Хранение объявлений в памяти: {id: {title, description, created_at, owner}}
listings = {}


async def index(request: web.Request) -> web.Response:
    return web.jsonify({
        "message": "Listing API",
        "endpoints": {
            "POST /listings": "Create a listing",
            "GET /listings": "Get all listings",
            "GET /listings/<id>": "Get a single listing",
            "PUT /listings/<id>": "Update a listing",
            "DELETE /listings/<id>": "Delete a listing"
        }
    })


async def create_listing(request: web.Request) -> web.Response:
    data = await request.json()
    if not data or not all(k in data for k in ("title", "description", "owner")):
        return web.jsonify({"error": "Missing required fields: title, description, owner"}), 400

    listing_id = str(uuid.uuid4())
    listing = {
        "id": listing_id,
        "title": data["title"],
        "description": data["description"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "owner": data["owner"],
    }
    listings[listing_id] = listing
    return web.jsonify(listing), 201


async def get_listings(request: web.Request) -> web.Response:
    return web.jsonify(list(listings.values()))


async def get_listing(request: web.Request) -> web.Response:
    listing_id = request.match_info["listing_id"]
    listing = listings.get(listing_id)
    if not listing:
        return web.jsonify({"error": "Listing not found"}), 404
    return web.jsonify(listing)


async def update_listing(request: web.Request) -> web.Response:
    listing_id = request.match_info["listing_id"]
    listing = listings.get(listing_id)
    if not listing:
        return web.jsonify({"error": "Listing not found"}), 404

    data = await request.json()
    if not data:
        return web.jsonify({"error": "No data provided"}), 400

    for field in ("title", "description", "owner"):
        if field in data:
            listing[field] = data[field]

    listings[listing_id] = listing
    return web.jsonify(listing)


async def delete_listing(request: web.Request) -> web.Response:
    listing_id = request.match_info["listing_id"]
    if listing_id not in listings:
        return web.jsonify({"error": "Listing not found"}), 404

    deleted = listings.pop(listing_id)
    return web.jsonify(deleted)


async def init_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_post("/listings", create_listing)
    app.router.add_get("/listings", get_listings)
    app.router.add_get("/listings/{listing_id}", get_listing)
    app.router.add_put("/listings/{listing_id}", update_listing)
    app.router.add_delete("/listings/{listing_id}", delete_listing)
    return app


if __name__ == "__main__":
    app = init_app()
    web.run_app(app, host="localhost", port=8080, debug=True)
