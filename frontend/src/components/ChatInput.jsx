import React, { useState } from 'react';
import './ChatInput.css';

export function ChatInput({ onSendMessage, isLoading }) {
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  return (
    <form className="chat-input-form" onSubmit={handleSubmit}>
      <div className="chat-input-wrapper">
        <textarea
          className="chat-input"
          placeholder="Ask me anything... e.g., 'Find me a blue shirt under 500 rupees'"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
          disabled={isLoading}
          rows="2"
        />
      </div>
      <button
        type="submit"
        className="send-btn"
        disabled={!input.trim() || isLoading}
        title={isLoading ? 'Waiting for response...' : 'Send message'}
      >
        {isLoading ? '⏳' : '📤'}
      </button>
    </form>
  );
}
