from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def init_db():
    global _client, _db
    _client = AsyncIOMotorClient(settings.mongodb_url)
    _db = _client.get_default_database(default="trade_copilot")
    # Ensure indexes for common queries
    await _db.chats.create_index([("social", 1), ("channel_type", 1), ("username", 1)])
    await _db.messages.create_index([("chat_id", 1), ("created_at", 1)])


async def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db
