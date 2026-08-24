import React, { useState, useEffect, useRef } from 'react';
import { MessageBubble } from './MessageBubble';
import { ChatInput } from './ChatInput';
import './ChatWindow.css';

const API_BASE = 'http://localhost:5000';

// Log to console to verify component is loaded
console.log('ChatWindow component loaded, API_BASE:', API_BASE);

// Generate or get session ID for conversation tracking
function getOrCreateSessionId() {
  const storageKey = 'razorpay_session_id';
  let sessionId = localStorage.getItem(storageKey);
  if (!sessionId) {
    sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem(storageKey, sessionId);
  }
  return sessionId;
}

export function ChatWindow() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => getOrCreateSessionId());
  const messagesEndRef = useRef(null);

  // Scroll to bottom
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'auto' });
    }
  }, [messages]);

  // Initial greeting
  useEffect(() => {
    const greeting = {
      id: 'greeting',
      text: "👋 Hi! I'm your shopping agent. I can help you find products, check prices, and complete purchases. What are you looking for today?",
      isUser: false,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages([greeting]);
    
    // Ensure scroll to top on initial load
    setTimeout(() => {
      if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({ behavior: 'auto' });
      }
    }, 0);
  }, []);

  const handleSendMessage = async (userMessage) => {
    // Add user message
    const userMsg = {
      id: `user-${Date.now()}`,
      text: userMessage,
      isUser: true,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      // Call backend chat endpoint with session ID
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          budget: null,  // Could be extracted from message later
          session_id: sessionId  // Send session ID for context tracking
        })
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();

      // Add AI response
      const aiMsg = {
        id: `ai-${Date.now()}`,
        text: data.reply || "I couldn't process that request. Please try again.",
        isUser: false,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        products: data.products || [],
        status: data.status || null,
        action: data.tool_calls ? { type: 'payment_ready' } : null
      };
      
      setMessages(prev => [...prev, aiMsg]);
      
      // If this is an order ready for payment, trigger Razorpay
      if (data.tool_calls && data.tool_calls.includes('initiate_purchase')) {
        setTimeout(() => {
          initiateRazorpayPayment(data.reply, sessionId);
        }, 1000);
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMsg = {
        id: `error-${Date.now()}`,
        text: `Sorry, I encountered an error: ${error.message}. Please try again.`,
        isUser: false,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const initiateRazorpayPayment = async (orderSummary, sessionId) => {
    try {
      // Step 1: Create Razorpay order (don't need to pass product_id, it comes from session)
      const createOrderRes = await fetch(`${API_BASE}/purchase/create-order`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_id: null,  // Will be fetched from session on backend
          session_id: sessionId
        })
      });

      if (!createOrderRes.ok) {
        throw new Error('Failed to create Razorpay order');
      }

      const orderData = await createOrderRes.json();
      
      if (orderData.error) {
        addBotMessage(`Payment error: ${orderData.message}`);
        return;
      }

      // In demo mode, skip Razorpay popup and show success
      if (orderData.mode === "demo") {
        const confirmationMsg = `🎉 **PAYMENT SUCCESSFUL!**

📦 **Order Details:**
• Product: **${orderData.product_name}**
• Price: ₹${orderData.product_price}
• Color: Available
• Size: Selected

💰 **Total Cost: ₹${orderData.product_price}**

✅ Order Confirmed
📞 Order ID: **${orderData.order_id}**
🚚 Expected delivery: 3-5 business days

Thank you for your purchase!`;
        addBotMessage(confirmationMsg);
        return;
      }

      // Step 2: Open Razorpay checkout (for real keys only)
      const options = {
        key: orderData.key_id,
        amount: orderData.amount,
        currency: orderData.currency,
        order_id: orderData.order_id,
        name: 'Razorpay Agent Catalog',
        description: `${orderData.product_name} - ₹${orderData.product_price}`,
        theme: { color: '#2DD4BF' },
        handler: async function (response) {
          // Step 3: Verify payment signature
          const verifyRes = await fetch(`${API_BASE}/purchase/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
              session_id: sessionId
            })
          });

          const verifyData = await verifyRes.json();
          
          if (verifyData.status === 'success') {
            const confirmationMsg = `🎉 **PAYMENT SUCCESSFUL!**

📦 **Order Details:**
• Product: **${orderData.product_name}**
• Price: ₹${orderData.product_price}
• Color: Available
• Size: Selected

💰 **Total Cost: ₹${orderData.product_price}**

✅ Order Confirmed
📞 Order ID: **${response.razorpay_order_id}**
🚚 Expected delivery: 3-5 business days

Thank you for your purchase!`;
            addBotMessage(confirmationMsg);
          } else {
            addBotMessage(`❌ Payment verification failed. Please try again.`);
          }
        },
        modal: {
          ondismiss: function () {
            addBotMessage(`Payment cancelled. You can try again.`);
          }
        }
      };

      const rzp = new window.Razorpay(options);
      rzp.open();
    } catch (error) {
      console.error('Razorpay error:', error);
      addBotMessage(`Error initiating payment: ${error.message}`);
    }
  };

  const addBotMessage = (text) => {
    const botMsg = {
      id: `bot-${Date.now()}`,
      text: text,
      isUser: false,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages(prev => [...prev, botMsg]);
  };

  return (
    <div className="chat-window">
      <div className="messages-container">
        {messages.map(msg => (
          <MessageBubble
            key={msg.id}
            message={msg}
            isUser={msg.isUser}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>
      <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
    </div>
  );
}
