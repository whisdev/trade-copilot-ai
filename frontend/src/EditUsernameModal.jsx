import { useState, useEffect } from 'react';

export default function EditUsernameModal({ chat, onClose, onSubmit }) {
  const [username, setUsername] = useState(chat?.username ?? '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    setUsername(chat?.username ?? '');
    setError('');
  }, [chat]);

  async function handleSubmit(e) {
    e.preventDefault();
    const trimmed = username.trim();
    if (!trimmed) {
      setError('Username is required');
      return;
    }
    if (trimmed === chat?.username) {
      onClose();
      return;
    }
    setError('');
    setLoading(true);
    try {
      await onSubmit(trimmed);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to update username');
    } finally {
      setLoading(false);
    }
  }

  if (!chat) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Edit username</h2>
          <button type="button" className="modal-close" onClick={onClose}>×</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>{chat.social} · {chat.channel_type}</label>
            <p className="form-hint">Current: {chat.username}</p>
          </div>
          <div className="form-group form-group-username">
            <label>New username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. johndoe"
              autoFocus
            />
          </div>
          {error && <p className="form-error">{error}</p>}
          <div className="modal-actions">
            <button type="button" onClick={onClose}>Cancel</button>
            <button type="submit" disabled={loading || !username.trim()}>
              {loading ? 'Saving…' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
