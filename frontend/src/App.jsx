import { useState, useEffect, useCallback } from 'react';
import { getChats, createChat, deleteChat, updateChat } from './api';
import NewUserModal from './NewUserModal';
import EditUsernameModal from './EditUsernameModal';
import ChatView from './ChatView';
import './App.css';

export default function App() {
  const [chats, setChats] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [editChat, setEditChat] = useState(null);

  const refreshChats = useCallback(async () => {
    try {
      const data = await getChats();
      setChats(data);
      setError('');
    } catch (err) {
      setError(err.message || 'Failed to load chats');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshChats();
  }, [refreshChats]);

  async function handleNewUser(payload) {
    const chat = await createChat(payload);
    setChats((prev) => [chat, ...prev].sort((a, b) => {
      if (a.social !== b.social) return a.social.localeCompare(b.social);
      if (a.channel_type !== b.channel_type) return a.channel_type.localeCompare(b.channel_type);
      return a.username.localeCompare(b.username);
    }));
    setSelectedChat(chat);
    setModalOpen(false);
  }

  const SOCIAL_ORDER = ['discord', 'reddit', 'twitter'];
  const CHANNEL_ORDER = ['channel', 'post', 'dm'];

  function groupChatsBySocialAndChannel(chatList) {
    const grouped = {};
    for (const chat of chatList) {
      if (!grouped[chat.social]) grouped[chat.social] = {};
      if (!grouped[chat.social][chat.channel_type]) grouped[chat.social][chat.channel_type] = [];
      grouped[chat.social][chat.channel_type].push(chat);
    }
    return grouped;
  }

  const groupedChats = groupChatsBySocialAndChannel(chats);

  async function handleUpdateUsername(newUsername) {
    const chat = editChat;
    if (!chat) return;
    const updated = await updateChat(chat.id, { username: newUsername });
    setChats((prev) => prev.map((c) => (c.id === chat.id ? { ...c, username: updated.username } : c)).sort((a, b) => {
      if (a.social !== b.social) return a.social.localeCompare(b.social);
      if (a.channel_type !== b.channel_type) return a.channel_type.localeCompare(b.channel_type);
      return a.username.localeCompare(b.username);
    }));
    if (selectedChat?.id === chat.id) setSelectedChat({ ...selectedChat, username: updated.username });
  }

  async function handleDeleteChat(chatToDelete, e) {
    e?.stopPropagation();
    if (!confirm(`Remove ${chatToDelete.username} (${chatToDelete.social}/${chatToDelete.channel_type})?`)) return;
    try {
      await deleteChat(chatToDelete.id);
      setChats((prev) => prev.filter((c) => c.id !== chatToDelete.id));
      if (selectedChat?.id === chatToDelete.id) setSelectedChat(null);
    } catch (err) {
      alert(err.message || 'Failed to remove chat');
    }
  }

  return (
    <div className="app">
      <aside className={`sidebar ${sidebarOpen ? '' : 'sidebar-collapsed'}`}>
        <div className="sidebar-header">
          <span className="sidebar-title">Chats</span>
          <button type="button" className="btn-add" onClick={() => setModalOpen(true)}>
            + New user
          </button>
        </div>
        {loading && <p className="sidebar-loading">Loading…</p>}
        {error && <p className="sidebar-error">{error}</p>}
        <div className="chat-list">
          {[...SOCIAL_ORDER, ...Object.keys(groupedChats).filter((s) => !SOCIAL_ORDER.includes(s))].map((social) => {
            const channels = groupedChats[social];
            if (!channels) return null;
            return (
              <div key={social} className="sidebar-social-group">
                <div className="sidebar-social-header">
                  <span className={`social-avatar social-avatar-${social}`} aria-hidden />
                  <span className="sidebar-social-name">{social}</span>
                </div>
                {CHANNEL_ORDER.map((channelType) => {
                  const users = channels[channelType];
                  if (!users?.length) return null;
                  return (
                    <div key={`${social}-${channelType}`} className="sidebar-channel-group">
                      <div className="sidebar-channel-label">{channelType}</div>
                      <ul className="sidebar-user-list">
                        {users.map((chat) => (
                          <li key={chat.id} className={`chat-list-item ${selectedChat?.id === chat.id ? 'active' : ''}`}>
                            <button
                              type="button"
                              className="chat-item"
                              onClick={() => setSelectedChat(chat)}
                            >
                              {chat.username}
                            </button>
                            <button
                              type="button"
                              className="chat-item-edit"
                              onClick={(e) => { e.stopPropagation(); setEditChat(chat); }}
                              title="Edit username"
                              aria-label="Edit username"
                            >
                              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                              </svg>
                            </button>
                            <button
                              type="button"
                              className="chat-item-remove"
                              onClick={(e) => handleDeleteChat(chat, e)}
                              title="Remove user"
                              aria-label="Remove user"
                            >
                              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M18 6L6 18M6 6l12 12" />
                              </svg>
                            </button>
                          </li>
                        ))}
                      </ul>
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>
        <button
          type="button"
          className="sidebar-toggle"
          onClick={() => setSidebarOpen((o) => !o)}
          title={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
          aria-label={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
        >
          {sidebarOpen ? (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="15 18 9 12 15 6" />
            </svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          )}
        </button>
      </aside>
      <main className="main">
        <ChatView chat={selectedChat} onChatsRefresh={refreshChats} />
      </main>
      {modalOpen && (
        <NewUserModal
          onClose={() => setModalOpen(false)}
          onSubmit={handleNewUser}
        />
      )}
      {editChat && (
        <EditUsernameModal
          chat={editChat}
          onClose={() => setEditChat(null)}
          onSubmit={handleUpdateUsername}
        />
      )}
    </div>
  );
}
