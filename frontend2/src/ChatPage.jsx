import { useAppState } from "./StateContext";
import AppLayout from "./Layout";
import ChatBox from "./components/ChatBox";
import PromptSuggestions from "./components/PromptSuggestions";

export default function ChatPage() {
    const { messages, setMessages, loading, setLoading, updateState } = useAppState();

    async function sendMessage(message) {
        if (!message.trim()) return;

        const userMessage = { id: crypto.randomUUID(), role: "user", content: message };
        setMessages((prev) => [...prev, userMessage]);
        setLoading(true);

        const payload = {
            thread_id: "1",
            run_id: crypto.randomUUID(),
            messages: [
                { id: crypto.randomUUID(), role: "user", content: message, user: { id: "user-123" } },
            ],
            state: {},
            tools: [],
            context: [],
            forwardedProps: {},
        };

        const response = await fetch("http://localhost:8080/", {
            method: "POST",
            headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
            body: JSON.stringify(payload),
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let assistantMessage = "";
        const assistantId = crypto.randomUUID();

        setMessages((prev) => [...prev, { id: assistantId, role: "assistant", content: "" }]);

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split("\n");

            for (let line of lines) {
                if (!line.startsWith("data:")) continue;
                const jsonStr = line.replace("data:", "").trim();
                if (!jsonStr) continue;

                try {
                    const event = JSON.parse(jsonStr);
                    if (event.type === "TEXT_MESSAGE_CONTENT") {
                        assistantMessage += event.delta;
                        setMessages((prev) => {
                            const updated = [...prev];
                            const index = updated.findIndex((m) => m.id === assistantId);
                            if (index !== -1) updated[index].content = assistantMessage;
                            return updated;
                        });
                    }
                    if (event.type === "STATE_SNAPSHOT") {
                        updateState(event.snapshot);
}
                    if (event.type === "RUN_FINISHED") {
                        setLoading(false);
                    }
                } catch (err) {
                    console.error(err);
                }
            }
        }
        setLoading(false);
    }

    return (
        <AppLayout>
            {messages.length === 0 ? (
                <PromptSuggestions onSelect={sendMessage} />
            ) : (
                <ChatBox messages={messages} setMessages={setMessages} onSend={sendMessage} loading={loading} />
            )}
        </AppLayout>
    );
}