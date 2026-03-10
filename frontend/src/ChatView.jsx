import { useState, useEffect, useRef } from 'react';
import { getMessages, sendMessage } from './api';

export default function ChatView({ chat, onChatsRefresh }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [lastScore, setLastScore] = useState(null);
  const [error, setError] = useState('');
  const [copiedId, setCopiedId] = useState(null);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (!chat?.id) return;
    let cancelled = false;
    getMessages(chat.id).then((data) => {
      if (!cancelled) setMessages(data);
    }).catch((err) => {
      if (!cancelled) setError(err.message);
    });
    setLastScore(null);
    return () => { cancelled = true; };
  }, [chat?.id]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea to show all content without scrollbar
  useEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = 'auto';
    const maxH = typeof window !== 'undefined' ? window.innerHeight * 0.6 : 500;
    el.style.height = Math.min(el.scrollHeight, maxH) + 'px';
  }, [input]);

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend(e);
    }
  }

  async function handleSend(e) {
    e?.preventDefault?.();
    if (!input.trim() || loading || !chat?.id) return;
    const content = input.trim();
    setInput('');
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
    }
    setLoading(true);
    setError('');
    setLastScore(null);
    try {
      const res = await sendMessage(chat.id, content);
      setLastScore(res.attract_score);
      const updated = await getMessages(chat.id);
      setMessages(updated);
      onChatsRefresh?.();
    } catch (err) {
      setError(err.message || 'Send failed');
      setInput(content);
    } finally {
      setLoading(false);
    }
  }

  /** Copy message content excluding <think>...</think> and Score: X/100 parts */
  function getCopyableContent(content, attractScore) {
    let text = String(content || '');
    text = text.replace(/<think>[\s\S]*?<\/think>/gi, '').trim();
    if (attractScore != null) {
      text = text.replace(/\n*Score:\s*\d+\s*\/\s*100\s*/gi, '').trim();
    }
    return text.trim() || '';
  }

  function handleCopyMessage(msgId, content, attractScore) {
    const copyable = getCopyableContent(content, attractScore);
    if (!copyable) return;
    navigator.clipboard.writeText(copyable).then(() => {
      setCopiedId(msgId);
      setTimeout(() => setCopiedId(null), 1500);
    }).catch(() => {});
  }

  if (!chat) {
    return (
      <div className="chat-placeholder">
        <p>Select a chat or add a new user to start.</p>
      </div>
    );
  }

  return (
    <div className="chat-view">
      <div className="chat-header">
        <span className="chat-meta">
          {chat.social} · {chat.channel_type} · {chat.username}
        </span>
        {lastScore !== null && (
          <div className="attract-score" title="How likely this reply is to attract collaboration">
            Attract score: <strong>{lastScore}</strong>/100
          </div>
        )}
      </div>
      <div className="messages">
        {messages.map((m) => (
          <div key={m.id} className={`message message-${m.role} ${copiedId === m.id ? 'message-copied' : ''}`}>
            <div className="message-header">
              <span className="message-role">{m.role}</span>
              {getCopyableContent(m.content, m.attract_score) && (
                <button
                  type="button"
                  className={`message-copy ${copiedId === m.id ? 'copied' : ''}`}
                  onClick={() => handleCopyMessage(m.id, m.content, m.attract_score)}
                  title="Copy message (excludes think & score)"
                  aria-label="Copy message"
                >
                  {copiedId === m.id ? (
                    <svg className="message-copy-icon" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                  ) : (
                    <svg className="message-copy-icon" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                    </svg>
                  )}
                </button>
              )}
            </div>
            <p className="message-content">{m.content}</p>
            {m.role === 'assistant' && m.attract_score != null && (
              <span className="message-score">Score: {m.attract_score}/100</span>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      {error && <p className="chat-error">{error}</p>}
      <form className="chat-form" onSubmit={handleSend}>
        <textarea
          ref={inputRef}
          className="chat-form-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message..."
          disabled={loading}
          rows={2}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          {loading ? 'Sending…' : 'Send'}
        </button>
      </form>
    </div>
  );
}
