import { useEffect, useRef, useState } from "react";
import { Send, Sparkles, RotateCcw } from "lucide-react";
import { aiAdminAsk, clearAdminChat } from "../../api/endpoints";

const SUGGESTIONS = [
  "What's today's revenue?",
  "What stock do I need to refill and can I afford it?",
  "How is the clinic doing this month?",
  "Which patients missed their follow-up?",
  "Can I afford to hire another staff member?",
];

export default function AssistantPanel() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinking]);

  const send = async (text) => {
    const question = (text ?? input).trim();
    if (!question || thinking) return;

    setMessages((m) => [...m, { role: "user", text: question }]);
    setInput("");
    setThinking(true);

    try {
      const res = await aiAdminAsk(question);
      setMessages((m) => [...m, { role: "ai", text: res.data.answer }]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        {
          role: "ai",
          text: err.response?.data?.detail || "Something went wrong.",
          error: true,
        },
      ]);
    } finally {
      setThinking(false);
    }
  };

  const reset = async () => {
    try {
      await clearAdminChat();
    } catch {}
    setMessages([]);
  };

  return (
    <div className="rounded-xl border border-gray-200 bg-white">
      <div className="flex items-center justify-between border-b border-gray-200 px-5 py-3">
        <div className="flex items-center gap-2">
          <Sparkles size={16} className="text-blue-600" />
          <h2 className="text-sm font-semibold text-gray-900">
            Clinic assistant
          </h2>
        </div>
        {messages.length > 0 && (
          <button
            onClick={reset}
            className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-900"
          >
            <RotateCcw size={14} />
            New conversation
          </button>
        )}
      </div>

      {/* MESSAGES */}
      <div className="h-[28rem] space-y-4 overflow-y-auto px-5 py-4">
        {messages.length === 0 && (
          <div className="py-8 text-center">
            <p className="mb-4 text-sm text-gray-500">
              Ask anything about your clinic — revenue, stock, patients, staff.
            </p>
            <div className="mx-auto flex max-w-lg flex-wrap justify-center gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="rounded-full border border-gray-300 px-3 py-1.5 text-xs text-gray-700 hover:bg-gray-50"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div
            key={i}
            className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm ${
                m.role === "user"
                  ? "bg-gray-900 text-white"
                  : m.error
                  ? "bg-red-50 text-red-700"
                  : "bg-gray-50 text-gray-900"
              }`}
            >
              <p className="whitespace-pre-wrap">{m.text}</p>
            </div>
          </div>
        ))}

        {thinking && (
          <div className="flex justify-start">
            <div className="rounded-2xl bg-gray-50 px-4 py-2.5 text-sm text-gray-500">
              Checking your clinic data…
            </div>
          </div>
        )}

        <div ref={endRef} />
      </div>

      {/* INPUT */}
      <div className="border-t border-gray-200 p-4">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder="Ask about revenue, stock, patients…"
            disabled={thinking}
            className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-gray-900 disabled:bg-gray-50"
          />
          <button
            onClick={() => send()}
            disabled={thinking || !input.trim()}
            className="rounded-lg bg-gray-900 px-4 py-2 text-white hover:bg-gray-800 disabled:opacity-40"
          >
            <Send size={16} />
          </button>
        </div>
        <p className="mt-2 text-xs text-gray-400">
          Answers come from your clinic's own data. Verify before acting on them.
        </p>
      </div>
    </div>
  );
}