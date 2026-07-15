import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Copy, Pencil } from "lucide-react";

export default function ChatBox({ messages, setMessages, onSend, loading }) {
    const [input, setInput] = useState("");
    const endRef = useRef(null);

    function copy(text) {
        navigator.clipboard.writeText(text);
    }

    function edit(index) {
        const msg = messages[index];
        if (msg.role === "user") {
            setInput(msg.content);
            setMessages((prev) => prev.slice(0, index));
        }
    }

    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading]);

    return (
        <div className="flex flex-col flex-1 h-0">
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {messages.map((msg, i) => (
                    <div
                        key={msg.id}
                        className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                        <div
                            className={`group max-w-xl px-4 py-3 rounded-2xl shadow ${
                                msg.role === "user"
                                    ? "bg-blue-600"
                                    : "bg-gray-800 border border-gray-700"
                            }`}
                        >
                            {msg.role === "assistant" ? (
                                <ReactMarkdown remarkPlugins={[remarkGfm]} className="prose prose-invert">
                                    {msg.content}
                                </ReactMarkdown>
                            ) : (
                                msg.content
                            )}
                        </div>
                        <div className="opacity-0 group-hover:opacity-100 flex gap-2 mt-2">
                            <button onClick={() => copy(msg.content)}>
                                <Copy size={14} />
                            </button>
                            {msg.role === "user" && (
                                <button onClick={() => edit(i)}>
                                    <Pencil size={14} />
                                </button>
                            )}
                        </div>
                    </div>
                ))}
                {loading && <div className="text-gray-400">Pensando...</div>}
                <div ref={endRef} />
            </div>

            <div className="p-4 border-t border-gray-700 flex gap-2">
                <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-2"
                    onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                            e.preventDefault();
                            onSend(input);
                            setInput("");
                        }
                    }}
                />
                <button
                    onClick={() => {
                        onSend(input);
                        setInput("");
                    }}
                    className="bg-blue-600 px-4 rounded-xl"
                >
                    Enviar
                </button>
            </div>
        </div>
    );
}