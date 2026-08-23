import React from 'react';
import './MessageBubble.css';

export function MessageBubble({ message, isUser }) {
  const { text, timestamp, products, status } = message;

  if (isUser) {
    return (
      <div className="message-wrapper user">
        <div className="message-bubble user-bubble">
          <p className="message-text">{text}</p>
          {timestamp && <span className="message-time">{timestamp}</span>}
        </div>
      </div>
    );
  }

  return (
    <div className="message-wrapper ai">
      <div className="ai-avatar-container">
        <div className="ai-avatar">🤖</div>
      </div>
      <div className="message-bubble ai-bubble">
        <p className="message-text">{text}</p>
        
        {products && products.length > 0 && (
          <div className="products-container">
            {products.map((product, idx) => (
              <div key={idx} className="product-in-message">
                <span className="product-icon">📦</span>
                <div className="product-info">
                  <p className="product-name">{product.name}</p>
                  <p className="product-price">₹{product.price}</p>
                </div>
                {product.inStock ? (
                  <span className="badge badge-success">In Stock</span>
                ) : (
                  <span className="badge badge-danger">Out of Stock</span>
                )}
              </div>
            ))}
          </div>
        )}

        {status && (
          <div className={`status-bar ${status.type}`}>
            {status.icon} {status.message}
          </div>
        )}

        {timestamp && <span className="message-time">{timestamp}</span>}
      </div>
    </div>
  );
}
