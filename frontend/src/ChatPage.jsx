import React, { useState, useEffect, useRef } from "react";

const API_BASE = "http://localhost:5050/api/chat";

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef(null);

  // Fetch chat history on mount
  useEffect(() => {
    fetch(`${API_BASE}/history`)
      .then((res) => res.json())
      .then((data) => setMessages(data.messages || []));
  }, []);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    setSending(true);

    // Add user message optimistically
    setMessages((msgs) => [...msgs, { role: "user", content: input }]);

    try {
      const res = await fetch(`${API_BASE}/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });
      const data = await res.json();
      if (data.reply) {
        setMessages((msgs) => [...msgs, { role: "bot", content: data.reply }]);
      }
    } catch {
      setMessages((msgs) => [
        ...msgs,
        { role: "bot", content: "Lỗi gửi tin nhắn." },
      ]);
    }
    setInput("");
    setSending(false);
  };

  return (
    <div style={{ maxWidth: 600, margin: "40px auto", border: "1px solid #eee", borderRadius: 8, padding: 16, background: "#fafbfc" }}>
      <h2>Chat</h2>
      <div
        style={{
          minHeight: 300,
          maxHeight: 400,
          overflowY: "auto",
          background: "#fff",
          border: "1px solid #ddd",
          borderRadius: 4,
          padding: 12,
          marginBottom: 12,
        }}
      >
        {messages.map((msg, idx) => (
          <div
            key={idx}
            style={{
              textAlign: msg.role === "user" ? "right" : "left",
              margin: "8px 0",
            }}
          >
            <span
              style={{
                display: "inline-block",
                background: msg.role === "user" ? "#e6f7ff" : "#f5f5f5",
                color: "#222",
                borderRadius: 16,
                padding: "8px 16px",
                maxWidth: "80%",
                wordBreak: "break-word",
              }}
            >
              {msg.content}
            </span>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <form onSubmit={handleSend} style={{ display: "flex", gap: 8 }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Nhập tin nhắn..."
          style={{ flex: 1, padding: 8, borderRadius: 4, border: "1px solid #ccc" }}
          disabled={sending}
        />
        <button type="submit" disabled={sending || !input.trim()}>
          Gửi
        </button>
      </form>
    </div>
  );
}
