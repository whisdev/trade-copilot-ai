// In dev: /api (Vite proxy). In prod: set VITE_API_URL to backend URL (e.g. http://localhost:8000)
const API = import.meta.env.VITE_API_URL || '/api';

export async function getChats() {
  const r = await fetch(`${API}/chats`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function createChat({ social, channel_type, username }) {
  const r = await fetch(`${API}/chats`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ social, channel_type, username }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function getChat(chatId) {
  const r = await fetch(`${API}/chats/${chatId}`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function getMessages(chatId) {
  const r = await fetch(`${API}/chats/${chatId}/messages`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function sendMessage(chatId, content) {
  const r = await fetch(`${API}/chats/${chatId}/send`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function updateChat(chatId, { username }) {
  const r = await fetch(`${API}/chats/${chatId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function deleteChat(chatId) {
  const r = await fetch(`${API}/chats/${chatId}`, { method: 'DELETE' });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}
