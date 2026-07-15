// StatusPanel.jsx
export default function StatusPanel({ alerts }) {
    return (
        <div className="flex-1 overflow-y-auto">
            <h2 className="font-semibold mb-2 text-red-600">Alertas</h2>
            <div className="space-y-2 text-sm">
                {alerts.map((a, i) => (
                    <div key={i} className="bg-red-100 text-red-700 px-2 py-1 rounded">
                        {a.content}
                    </div>
                ))}
            </div>
        </div>
    );
}