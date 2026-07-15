// PromptSuggestions.jsx
export default function PromptSuggestions({ onSelect }) {
    const suggestions = [
        "Quero abrir uma conta",
        "Consultar saldo",
        "Solicitar cartão",
        "Falar com atendente",
    ];

    return (
        <div className="flex flex-col items-center justify-center h-full text-gray-400 gap-4">
            <h2 className="text-xl">Como posso ajudar?</h2>
            <div className="grid grid-cols-2 gap-3">
                {suggestions.map((s, i) => (
                    <button key={i} onClick={() => onSelect(s)} className="bg-gray-800 px-4 py-2 rounded-xl hover:bg-gray-700">
                        {s}
                    </button>
                ))}
            </div>
        </div>
    );
}