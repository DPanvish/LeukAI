"""
MongoDB connection manager using Motor (async driver).
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

_client: AsyncIOMotorClient = None
_db: AsyncIOMotorDatabase = None


async def connect_to_mongo():
    """Open the MongoDB connection pool."""
    global _client, _db
    _client = AsyncIOMotorClient(settings.MONGODB_URL)
    _db = _client[settings.MONGODB_DB_NAME]

    # Seed a default admin user if the collection is empty
    from app.core.security import hash_password

    users_col = _db["users"]
    if await users_col.count_documents({}) == 0:
        await users_col.insert_one(
            {
                "username": "admin",
                "password": hash_password("admin123"),
                "full_name": "Dr. Admin",
                "role": "admin",
            }
        )
    print(f"[OK] Connected to MongoDB: {settings.MONGODB_DB_NAME}")


async def close_mongo_connection():
    """Close the MongoDB connection pool."""
    global _client
    if _client:
        _client.close()
    print("[OK] MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """Return the active database handle."""
    return _db
