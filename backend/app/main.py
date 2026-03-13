from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.config import settings
from app.database import get_db, init_db
from app.crud import create_chat, get_chats, get_chat_by_id, get_messages, add_message, delete_chat, update_chat_username
from app.llm import chat_completion, score_attractiveness


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Chatting App API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Schemas ---
class ChatCreate(BaseModel):
    social: str
    channel_type: str
    username: str


class ChatItem(BaseModel):
    id: str
    social: str
    channel_type: str
    username: str


class MessageItem(BaseModel):
    id: str
    role: str
    content: str
    attract_score: int | None


class ChatUpdate(BaseModel):
    username: str


class SendMessageRequest(BaseModel):
    content: str


class SendMessageResponse(BaseModel):
    assistant_message: str
    attract_score: int


# --- Routes ---
@app.get("/chats", response_model=list[ChatItem])
async def list_chats(db: AsyncIOMotorDatabase = Depends(get_db)):
    chats = await get_chats(db)
    return chats


@app.post("/chats", response_model=ChatItem)
async def new_chat(body: ChatCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    chat = await create_chat(db, body.social, body.channel_type, body.username)
    return chat


@app.get("/chats/{chat_id}", response_model=ChatItem)
async def get_chat(chat_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    chat = await get_chat_by_id(db, chat_id)
    if not chat:
        raise HTTPException(404, "Chat not found")
    return chat


@app.patch("/chats/{chat_id}", response_model=ChatItem)
async def update_chat(chat_id: str, body: ChatUpdate, db: AsyncIOMotorDatabase = Depends(get_db)):
    if not body.username or not body.username.strip():
        raise HTTPException(400, "Username cannot be empty")
    chat = await update_chat_username(db, chat_id, body.username.strip())
    if not chat:
        raise HTTPException(404, "Chat not found")
    return chat


@app.delete("/chats/{chat_id}")
async def remove_chat(chat_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    chat = await get_chat_by_id(db, chat_id)
    if not chat:
        raise HTTPException(404, "Chat not found")
    deleted = await delete_chat(db, chat_id)
    if not deleted:
        raise HTTPException(500, "Failed to delete chat")
    return {"ok": True}


@app.get("/chats/{chat_id}/messages", response_model=list[MessageItem])
async def list_messages(chat_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    chat = await get_chat_by_id(db, chat_id)
    if not chat:
        raise HTTPException(404, "Chat not found")
    messages = await get_messages(db, chat_id)
    return messages


@app.post("/chats/{chat_id}/send", response_model=SendMessageResponse)
async def send_message(
    chat_id: str,
    body: SendMessageRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    chat = await get_chat_by_id(db, chat_id)
    if not chat:
        raise HTTPException(404, "Chat not found")
    await add_message(db, chat_id, "user", body.content)
    messages = await get_messages(db, chat_id)
    history = [{"role": m["role"], "content": m["content"]} for m in messages]
    try:
        assistant_content = await chat_completion(
            history, chat["social"], chat["channel_type"]
        )
        score = await score_attractiveness(body.content, assistant_content)
    except ValueError as e:
        raise HTTPException(503, str(e))
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(
                503,
                "OpenAI API key invalid. Set OPENAI_API_KEY in backend/.env (get one at https://platform.openai.com/api-keys)",
            )
        raise HTTPException(503, f"Open AI API error: {e.response.text[:200]}")
    await add_message(db, chat_id, "assistant", assistant_content, attract_score=score)
    return SendMessageResponse(assistant_message=assistant_content, attract_score=score)
