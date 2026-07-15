export default function AgentSelector({ selected, onSelect }) {
    const agents = [
        { id: "conta", label: "Conta" },
        { id: "cartao", label: "Cartão" },
        { id: "supervisor", label: "Supervisor" },
    ];

    return (
        <div>
            <h2 className="font-semibold mb-2 text-gray-700">Agentes</h2>
            <div className="flex flex-col gap-2">
                {agents.map((agent) => (
                    <button
                        key={agent.id}
                        onClick={() => onSelect(agent.id)}
                        className={`text-left px-3 py-2 rounded-lg transition ${
                            selected === agent.id
                                ? "bg-blue-600 text-white"
                                : "bg-gray-100 hover:bg-gray-200"
                        }`}
                    >
                        {agent.label}
                    </button>
                ))}
            </div>
        </div>
    );
}