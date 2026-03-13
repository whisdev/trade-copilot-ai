from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


def _doc_to_chat(doc: dict) -> dict:
    if not doc:
        return None
    return {
        "id": str(doc["_id"]),
        "social": doc["social"],
        "channel_type": doc["channel_type"],
        "username": doc["username"],
    }


def _doc_to_message(doc: dict) -> dict:
    if not doc:
        return None
    return {
        "id": str(doc["_id"]),
        "role": doc["role"],
        "content": doc["content"],
        "attract_score": doc.get("attract_score"),
    }


async def create_chat(db: AsyncIOMotorDatabase, social: str, channel_type: str, username: str) -> dict:
    now = datetime.utcnow()
    doc = {
        "social": social,
        "channel_type": channel_type,
        "username": username,
        "created_at": now,
        "updated_at": now,
    }
    r = await db.chats.insert_one(doc)
    doc["_id"] = r.inserted_id
    return _doc_to_chat(doc)


async def get_chats(db: AsyncIOMotorDatabase) -> list[dict]:
    cursor = db.chats.find().sort([("social", 1), ("channel_type", 1), ("username", 1)])
    return [_doc_to_chat(d) async for d in cursor]


async def get_chat_by_id(db: AsyncIOMotorDatabase, chat_id: str) -> dict | None:
    try:
        oid = ObjectId(chat_id)
    except Exception:
        return None
    doc = await db.chats.find_one({"_id": oid})
    return _doc_to_chat(doc)


async def get_messages(db: AsyncIOMotorDatabase, chat_id: str) -> list[dict]:
    try:
        oid = ObjectId(chat_id)
    except Exception:
        return []
    cursor = db.messages.find({"chat_id": oid}).sort("created_at", 1)
    return [_doc_to_message(d) async for d in cursor]


async def update_chat_username(db: AsyncIOMotorDatabase, chat_id: str, username: str) -> dict | None:
    try:
        oid = ObjectId(chat_id)
    except Exception:
        return None
    r = await db.chats.find_one_and_update(
        {"_id": oid},
        {"$set": {"username": username.strip(), "updated_at": datetime.utcnow()}},
        return_document=True,
    )
    return _doc_to_chat(r) if r else None


async def delete_chat(db: AsyncIOMotorDatabase, chat_id: str) -> bool:
    try:
        oid = ObjectId(chat_id)
    except Exception:
        return False
    await db.messages.delete_many({"chat_id": oid})
    r = await db.chats.delete_one({"_id": oid})
    return r.deleted_count > 0


async def add_message(
    db: AsyncIOMotorDatabase,
    chat_id: str,
    role: str,
    content: str,
    attract_score: int | None = None,
) -> dict:
    try:
        oid = ObjectId(chat_id)
    except Exception:
        raise ValueError("Invalid chat_id")
    doc = {
        "chat_id": oid,
        "role": role,
        "content": content,
        "attract_score": attract_score,
        "created_at": datetime.utcnow(),
    }
    r = await db.messages.insert_one(doc)
    doc["_id"] = r.inserted_id
    return _doc_to_message(doc)
