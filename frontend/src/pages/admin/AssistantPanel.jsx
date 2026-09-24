import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  ArrowUp, Sparkles, RotateCcw, Wrench,
  TrendingUp, Package, Users, AlertCircle
} from "lucide-react";
import { aiAdminAsk, clearAdminChat } from "../../api/endpoints";

const STARTERS = [
  { icon: TrendingUp, label: "Today's revenue", q: "What's today's revenue?" },
  { icon: Package, label: "What to restock", q: "What stock do I need to refill and can I afford it?" },
  { icon: AlertCircle, label: "Anything to worry about", q: "Is there anything I should worry about today?" },
  { icon: Users, label: "Missed follow-ups", q: "Which patients missed their follow-up?" },
];

export default function AssistantPanel() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
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
      setMessages((m) => [...m, {
        role: "ai",
        text: err.response?.data?.detail || "Something went wrong reaching the assistant.",
        error: true,
      }]);
    } finally {
      setThinking(false);
      inputRef.current?.focus();
    }
  };

  const reset = async () => {
    try { await clearAdminChat(); } catch {}
    setMessages([]);
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const autoGrow = (e) => {
    setInput(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = Math.min(e.target.scrollHeight, 200) + "px";
  };

  const empty = messages.length === 0;

  return (
    <div className="flex h-[calc(100vh-13rem)] flex-col overflow-hidden rounded-2xl border border-gray-200 bg-white">
      {/* HEADER */}
      <div className="flex items-center justify-between border-b border-gray-100 px-6 py-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gray-900">
            <Sparkles size={14} className="text-white" />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-900">Clinic Assistant</p>
            <p className="text-xs text-gray-400">Reads your live clinic data</p>
          </div>
        </div>
        {!empty && (
          <button
            onClick={reset}
            className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs text-gray-500 transition hover:bg-gray-100 hover:text-gray-900"
          >
            <RotateCcw size={13} />
            New chat
          </button>
        )}
      </div>

      {/* MESSAGES */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        {empty ? (
          <div className="flex h-full flex-col items-center justify-center px-6">
            <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-gray-900">
              <Sparkles size={22} className="text-white" />
            </div>
            <h3 className="mb-1.5 text-xl font-medium text-gray-900">
              How is your clinic doing?
            </h3>
            <p className="mb-8 max-w-sm text-center text-sm text-gray-500">
              Ask about revenue, stock, patients or staff. I'll pull the
              numbers from your own records.
            </p>

            <div className="grid w-full max-w-lg grid-cols-1 gap-2 sm:grid-cols-2">
              {STARTERS.map((s) => {
                const Icon = s.icon;
                return (
                  <button
                    key={s.q}
                    onClick={() => send(s.q)}
                    className="group flex items-start gap-3 rounded-xl border border-gray-200 p-3.5 text-left transition hover:border-gray-900 hover:bg-gray-50"
                  >
                    <Icon size={16} className="mt-0.5 shrink-0 text-gray-400 group-hover:text-gray-900" />
                    <span className="text-sm text-gray-700 group-hover:text-gray-900">
                      {s.label}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="mx-auto max-w-3xl px-6 py-6">
            {messages.map((m, i) => (
              <Message key={i} message={m} />
            ))}
            {thinking && <Thinking />}
          </div>
        )}
      </div>

      {/* COMPOSER */}
      <div className="border-t border-gray-100 px-6 py-4">
        <div className="mx-auto max-w-3xl">
          <div className="relative flex items-end gap-2 rounded-2xl border border-gray-300 bg-white p-2 transition focus-within:border-gray-900">
            <textarea
              ref={inputRef}
              rows={1}
              value={input}
              onChange={autoGrow}
              onKeyDown={handleKey}
              disabled={thinking}
              placeholder="Ask about revenue, stock, patients…"
              className="max-h-[200px] flex-1 resize-none bg-transparent px-2 py-1.5 text-sm outline-none placeholder:text-gray-400 disabled:opacity-50"
            />
            <button
              onClick={() => send()}
              disabled={thinking || !input.trim()}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gray-900 text-white transition hover:bg-gray-700 disabled:bg-gray-200 disabled:text-gray-400"
            >
              <ArrowUp size={16} />
            </button>
          </div>
          <p className="mt-2 text-center text-xs text-gray-400">
            Answers come from your clinic's records. Verify before acting.
          </p>
        </div>
      </div>
    </div>
  );
}

/* ─── MESSAGE ─── */

function Message({ message }) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="mb-6 flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-br-md bg-gray-900 px-4 py-2.5">
          <p className="whitespace-pre-wrap text-sm text-white">{message.text}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mb-8 flex gap-3">
      <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-gray-100">
        <Sparkles size={13} className="text-gray-700" />
      </div>
      <div className="min-w-0 flex-1">
        {message.error ? (
          <p className="text-sm text-red-600">{message.text}</p>
        ) : (
          <Markdown text={message.text} />
        )}
      </div>
    </div>
  );
}

/* ─── THINKING ─── */

function Thinking() {
  const [step, setStep] = useState(0);
  const steps = [
    "Reading your clinic data…",
    "Checking the numbers…",
    "Putting it together…",
  ];

  useEffect(() => {
    const t = setInterval(() => setStep((s) => (s + 1) % steps.length), 2200);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="mb-8 flex gap-3">
      <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-gray-100">
        <Wrench size={13} className="animate-pulse text-gray-700" />
      </div>
      <div className="flex items-center gap-2 pt-1">
        <span className="text-sm text-gray-500">{steps[step]}</span>
        <span className="flex gap-1">
          {[0, 150, 300].map((d) => (
            <span
              key={d}
              className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400"
              style={{ animationDelay: `${d}ms` }}
            />
          ))}
        </span>
      </div>
    </div>
  );
}

/* ─── MARKDOWN ─── */

function Markdown({ text }) {
  return (
    <div className="text-sm leading-relaxed text-gray-800">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,

          strong: ({ children }) => (
            <strong className="font-semibold text-gray-900">{children}</strong>
          ),

          ul: ({ children }) => (
            <ul className="mb-3 space-y-1.5 pl-1 last:mb-0">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="mb-3 list-decimal space-y-1.5 pl-5 last:mb-0">{children}</ol>
          ),
          li: ({ children }) => (
            <li className="flex gap-2">
              <span className="mt-[0.45rem] h-1 w-1 shrink-0 rounded-full bg-gray-400" />
              <span className="min-w-0 flex-1">{children}</span>
            </li>
          ),

          h1: ({ children }) => (
            <h3 className="mb-2 mt-4 text-base font-semibold text-gray-900 first:mt-0">{children}</h3>
          ),
          h2: ({ children }) => (
            <h3 className="mb-2 mt-4 text-sm font-semibold text-gray-900 first:mt-0">{children}</h3>
          ),
          h3: ({ children }) => (
            <h4 className="mb-1.5 mt-3 text-sm font-semibold text-gray-900 first:mt-0">{children}</h4>
          ),

          table: ({ children }) => (
            <div className="mb-3 overflow-x-auto rounded-lg border border-gray-200 last:mb-0">
              <table className="w-full text-sm">{children}</table>
            </div>
          ),
          thead: ({ children }) => <thead className="bg-gray-50">{children}</thead>,
          tbody: ({ children }) => (
            <tbody className="divide-y divide-gray-100">{children}</tbody>
          ),
          th: ({ children }) => (
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-600">{children}</th>
          ),
          td: ({ children }) => (
            <td className="px-3 py-2 align-top text-gray-800">{children}</td>
          ),

          code: ({ inline, children }) =>
            inline ? (
              <code className="rounded bg-gray-100 px-1.5 py-0.5 font-mono text-[0.8em] text-gray-900">
                {children}
              </code>
            ) : (
              <code className="mb-3 block overflow-x-auto rounded-lg bg-gray-900 p-3 font-mono text-xs text-gray-100">
                {children}
              </code>
            ),

          blockquote: ({ children }) => (
            <blockquote className="mb-3 border-l-2 border-gray-300 pl-3 text-gray-600 last:mb-0">
              {children}
            </blockquote>
          ),

          hr: () => <hr className="my-4 border-gray-200" />,
        }}
      >
        {text}
      </ReactMarkdown>
    </div>
  );
}