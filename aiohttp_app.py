from aiohttp import web
import uuid
import aiosqlite
from datetime import datetime, timezone

DB_PATH = "listings.db"


async def init_db(app: web.Application) -> None:
    """Создание таблицы при запуске приложения."""
    app["db"] = await aiosqlite.connect(DB_PATH)
    await app["db"].execute(
        """
        CREATE TABLE IF NOT EXISTS listings (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL,
            owner TEXT NOT NULL
        )
        """
    )
    await app["db"].commit()


async def cleanup_db(app: web.Application) -> None:
    """Закрытие подключения при остановке."""
    await app["db"].close()


async def index(request: web.Request) -> web.Response:
    return web.json_response({
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
        return web.json_response(
            {"error": "Missing required fields: title, description, owner"},
            status=400
        )

    listing_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    db: aiosqlite.Connection = request.app["db"]
    await db.execute(
        "INSERT INTO listings (id, title, description, created_at, owner) VALUES (?, ?, ?, ?, ?)",
        (listing_id, data["title"], data["description"], created_at, data["owner"])
    )
    await db.commit()

    return web.json_response(
        {
            "id": listing_id,
            "title": data["title"],
            "description": data["description"],
            "created_at": created_at,
            "owner": data["owner"],
        },
        status=201
    )


async def get_listings(request: web.Request) -> web.Response:
    db: aiosqlite.Connection = request.app["db"]
    cursor = await db.execute("SELECT id, title, description, created_at, owner FROM listings")
    rows = await cursor.fetchall()

    listings = [
        {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "created_at": row[3],
            "owner": row[4],
        }
        for row in rows
    ]
    return web.json_response(listings)


async def get_listing(request: web.Request) -> web.Response:
    listing_id = request.match_info["listing_id"]
    db: aiosqlite.Connection = request.app["db"]

    cursor = await db.execute(
        "SELECT id, title, description, created_at, owner FROM listings WHERE id = ?",
        (listing_id,)
    )
    row = await cursor.fetchone()

    if not row:
        return web.json_response({"error": "Listing not found"}, status=404)

    return web.json_response({
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "created_at": row[3],
        "owner": row[4],
    })


async def update_listing(request: web.Request) -> web.Response:
    listing_id = request.match_info["listing_id"]
    db: aiosqlite.Connection = request.app["db"]

    cursor = await db.execute(
        "SELECT id, title, description, created_at, owner FROM listings WHERE id = ?",
        (listing_id,)
    )
    row = await cursor.fetchone()

    if not row:
        return web.json_response({"error": "Listing not found"}, status=404)

    data = await request.json()
    if not data:
        return web.json_response({"error": "No data provided"}, status=400)

    title = data.get("title", row[1])
    description = data.get("description", row[2])
    owner = data.get("owner", row[4])

    await db.execute(
        "UPDATE listings SET title = ?, description = ?, owner = ? WHERE id = ?",
        (title, description, owner, listing_id)
    )
    await db.commit()

    return web.json_response({
        "id": listing_id,
        "title": title,
        "description": description,
        "created_at": row[3],
        "owner": owner,
    })


async def delete_listing(request: web.Request) -> web.Response:
    listing_id = request.match_info["listing_id"]
    db: aiosqlite.Connection = request.app["db"]

    cursor = await db.execute(
        "SELECT id, title, description, created_at, owner FROM listings WHERE id = ?",
        (listing_id,)
    )
    row = await cursor.fetchone()

    if not row:
        return web.json_response({"error": "Listing not found"}, status=404)

    await db.execute("DELETE FROM listings WHERE id = ?", (listing_id,))
    await db.commit()

    return web.json_response({
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "created_at": row[3],
        "owner": row[4],
    })


async def init_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_post("/listings", create_listing)
    app.router.add_get("/listings", get_listings)
    app.router.add_get("/listings/{listing_id}", get_listing)
    app.router.add_put("/listings/{listing_id}", update_listing)
    app.router.add_delete("/listings/{listing_id}", delete_listing)

    app.on_startup.append(init_db)
    app.on_cleanup.append(cleanup_db)

    return app


if __name__ == "__main__":
    app = init_app()
    web.run_app(app, host="localhost", port=8080, debug=True)
