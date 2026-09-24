import React, { useState } from 'react';
import axios from 'axios';

function ChatBox() {
  const [message, setMessage] = useState('');
  const [output, setOutput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!message.trim() || loading) return;
    setLoading(true);
    setOutput('');
    try {
      const res = await axios.post('http://localhost:8000/api/chat/', {
        message: message,
      });
      setOutput(res.data.reply);
    } catch (err) {
      setOutput('Error: ' + (err.response?.data?.error || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div style={{ maxWidth: 700, margin: '2rem auto' }}>
      <h2>Ask the LLM</h2>

      <textarea
        rows={3}
        style={{ width: '100%', padding: 8, fontFamily: 'inherit' }}
        placeholder="Type your request... (Enter to send, Shift+Enter for newline)"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={loading}
      />

      <button
        onClick={sendMessage}
        disabled={loading || !message.trim()}
        style={{ marginTop: 8, padding: '8px 16px' }}
      >
        {loading ? 'Thinking...' : 'Send'}
      </button>

      <h3 style={{ marginTop: 24 }}>Response</h3>
      <div
        style={{
          whiteSpace: 'pre-wrap',     // preserves newlines from the LLM
          overflowY: 'auto',          // makes it scrollable
          maxHeight: 400,
          border: '1px solid #ccc',
          borderRadius: 6,
          padding: 12,
          background: '#fafafa',
          fontFamily: 'monospace',
        }}
      >
        {output || (loading ? 'Waiting for response...' : 'No response yet.')}
      </div>
    </div>
  );
}

export default ChatBox;