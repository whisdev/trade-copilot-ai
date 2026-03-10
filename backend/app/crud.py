from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Chat, Message


async def create_chat(db: AsyncSession, social: str, channel_type: str, username: str) -> Chat:
    chat = Chat(social=social, channel_type=channel_type, username=username)
    db.add(chat)
    await db.flush()
    await db.refresh(chat)
    return chat


async def get_chats(db: AsyncSession) -> list[Chat]:
    r = await db.execute(select(Chat).order_by(Chat.social, Chat.channel_type, Chat.username))
    return list(r.scalars().all())


async def get_chat_by_id(db: AsyncSession, chat_id: int) -> Chat | None:
    r = await db.execute(select(Chat).where(Chat.id == chat_id))
    return r.scalar_one_or_none()


async def get_messages(db: AsyncSession, chat_id: int) -> list[Message]:
    r = await db.execute(
        select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at)
    )
    return list(r.scalars().all())


async def update_chat_username(db: AsyncSession, chat_id: int, username: str) -> Chat | None:
    chat = await get_chat_by_id(db, chat_id)
    if not chat:
        return None
    chat.username = username.strip()
    await db.flush()
    await db.refresh(chat)
    return chat


async def delete_chat(db: AsyncSession, chat_id: int) -> bool:
    await db.execute(delete(Message).where(Message.chat_id == chat_id))
    result = await db.execute(delete(Chat).where(Chat.id == chat_id))
    return result.rowcount > 0


async def add_message(
    db: AsyncSession,
    chat_id: int,
    role: str,
    content: str,
    attract_score: int | None = None,
) -> Message:
    msg = Message(chat_id=chat_id, role=role, content=content, attract_score=attract_score)
    db.add(msg)
    await db.flush()
    await db.refresh(msg)
    return msg
