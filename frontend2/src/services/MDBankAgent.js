export class MDBankAgent {
    constructor(url, agentName) {
        this.url = url;
        this.agentName = agentName;
    }

    async run(message) {
        try {
            const response = await fetch(this.url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: message,
                    session_id: "123",
                    client_id: "123",
                    agent: this.agentName,
                }),
            });

            if (!response.ok) {
                const text = await response.text();
                console.error("Erro backend:", text);
                throw new Error("Erro na API");
            }
            const data = await response.json();
            return {
                messages: [{ role: "assistant", content: data?.resposta || "Sem resposta" }],
            };
        } catch (err) {
            console.error("ERRO COMPLETO:", err);
            return {
                messages: [{ role: "assistant", content: "Erro ao chamar agente" }],
            };
        }
    }
}