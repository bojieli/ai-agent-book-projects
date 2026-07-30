import { useState } from "react";

// ===========================================================================
// 基础 chatbot 界面。
// 这是一个"可被自然语言定制"的最小 React 应用：
//   - 标题文案、按钮文字等 UI 文本都写在这里（Agent 可按需求改文案）；
//   - 颜色、字体、布局等样式集中在 theme.css（Agent 可按需求改样式）。
// 用户在对话中说"把发送按钮改成蓝色 / 换成等宽字体 / 标题改成 XXX"，
// Agent 会定位并修改这些源码文件，Vite HMR 让改动即时生效。
// ===========================================================================

// UI 文案（Agent 定制"文案"需求时修改这里）
const HEADER_TITLE = "智能助手";
const HEADER_SUBTITLE = "有什么可以帮你的吗？";
const SEND_BUTTON_LABEL = "发送";

export default function App() {
  const [messages, setMessages] = useState([
    { role: "assistant", text: "你好！我是你的智能助手，随时为你服务。" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;
    setMessages((m) => [...m, { role: "user", text }]);
    setInput("");
    setLoading(true);
    try {
      const resp = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await resp.json();
      setMessages((m) => [...m, { role: "assistant", text: data.reply }]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        { role: "assistant", text: "（后端未连接，这是本地占位回复）" },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1 className="header-title">{HEADER_TITLE}</h1>
        <p className="header-subtitle">{HEADER_SUBTITLE}</p>
      </header>

      <main className="chat-window">
        {messages.map((m, i) => (
          <div key={i} className={`bubble bubble-${m.role}`}>
            {m.text}
          </div>
        ))}
        {loading && <div className="bubble bubble-assistant">思考中…</div>}
      </main>

      <footer className="composer">
        <input
          className="composer-input"
          value={input}
          placeholder="输入消息…"
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
        />
        <button className="send-button" onClick={handleSend}>
          {SEND_BUTTON_LABEL}
        </button>
      </footer>
    </div>
  );
}
