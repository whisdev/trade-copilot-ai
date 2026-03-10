import { useState, useRef, useEffect } from 'react';

const SOCIALS = [
  { value: 'discord', label: 'Discord' },
  { value: 'reddit', label: 'Reddit' },
  { value: 'twitter', label: 'Twitter' },
];
const CHANNEL_TYPES = ['channel', 'post', 'dm'];

export default function NewUserModal({ onClose, onSubmit }) {
  const [social, setSocial] = useState('discord');
  const [channelType, setChannelType] = useState('channel');
  const [username, setUsername] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [socialOpen, setSocialOpen] = useState(false);
  const socialRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(e) {
      if (socialRef.current && !socialRef.current.contains(e.target)) {
        setSocialOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!username.trim()) {
      setError('Username is required');
      return;
    }
    setError('');
    setLoading(true);
    try {
      await onSubmit({ social, channel_type: channelType, username: username.trim() });
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to create chat');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Add new user</h2>
          <button type="button" className="modal-close" onClick={onClose}>×</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="form-group" ref={socialRef}>
            <label>Social</label>
            <div className="form-social-select">
              <button
                type="button"
                className="form-social-trigger"
                onClick={() => setSocialOpen((o) => !o)}
                aria-haspopup="listbox"
                aria-expanded={socialOpen}
              >
                <span className={`form-social-avatar form-social-avatar-${social}`} aria-hidden />
                <span className="form-social-label">{SOCIALS.find((s) => s.value === social)?.label || social}</span>
                <span className="form-social-chevron">▾</span>
              </button>
              {socialOpen && (
                <div className="form-social-dropdown">
                  {SOCIALS.map((s) => (
                    <button
                      key={s.value}
                      type="button"
                      className={`form-social-option ${social === s.value ? 'selected' : ''}`}
                      onClick={() => {
                        setSocial(s.value);
                        setSocialOpen(false);
                      }}
                    >
                      <span className={`form-social-avatar form-social-avatar-${s.value}`} aria-hidden />
                      <span>{s.label}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
          <div className="form-group">
            <label>Channel type</label>
            <div className="form-select-wrapper">
              <select value={channelType} onChange={(e) => setChannelType(e.target.value)}>
              {CHANNEL_TYPES.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
              </select>
              <span className="form-select-chevron" aria-hidden>▾</span>
            </div>
          </div>
          <div className="form-group form-group-username">
            <label>Username</label>
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
            <button type="submit" disabled={loading}>
              {loading ? 'Creating…' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
