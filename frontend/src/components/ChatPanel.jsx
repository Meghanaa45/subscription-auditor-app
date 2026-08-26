import React, { useEffect, useRef, useState } from "react";
import { askAuditor } from "../api/client.js";

export default function ChatPanel({ auditId, agentConfigured }) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Ask me about what I found - which subscriptions cost the most, which ones raised prices, or what you might want to cancel.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, loading]);

  async function handleSend(text) {
    const question = (text ?? input).trim();
    if (!question || loading) return;
    const nextMessages = [...messages, { role: "user", content: question }];
    setMessages(nextMessages);
    setInput("");
    setError(null);
    setLoading(true);
    try {
      const history = nextMessages.slice(0, -1).map(({ role, content }) => ({ role, content }));
      const { answer } = await askAuditor(auditId, question, history);
      setMessages((prev) => [...prev, { role: "assistant", content: answer }]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const suggestions = ["What should I cancel first?", "Which prices went up?", "What's my biggest expense?"];

  return (
    <div className="chat-panel">
      <div className="chat-panel__heading">Ask the auditor</div>

      {!agentConfigured && (
        <div className="chat-panel__notice">
          The chat assistant isn't configured yet. Add your Azure OpenAI credentials to the
          backend's <code>.env</code> file to enable it.
        </div>
      )}

      <div className="chat-panel__messages" ref={scrollRef}>
        {messages.map((m, i) => (
          <div key={i} className={`chat-bubble chat-bubble--${m.role}`}>
            {m.content}
          </div>
        ))}
        {loading && <div className="chat-bubble chat-bubble--assistant chat-bubble--loading">thinking&hellip;</div>}
        {error && <div className="chat-panel__error">{error}</div>}
      </div>

      <div className="chat-panel__suggestions">
        {suggestions.map((s) => (
          <button key={s} onClick={() => handleSend(s)} disabled={!agentConfigured || loading}>
            {s}
          </button>
        ))}
      </div>

      <form
        className="chat-panel__input-row"
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={agentConfigured ? "Ask a question\u2026" : "Chat disabled until Azure OpenAI is configured"}
          disabled={!agentConfigured || loading}
        />
        <button type="submit" disabled={!agentConfigured || loading}>
          Ask
        </button>
      </form>
    </div>
  );
}
