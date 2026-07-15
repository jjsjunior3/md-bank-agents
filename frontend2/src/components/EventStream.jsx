// EventStream.jsx
export default function EventStream({ events }) {
    return (
        <div className="flex-1 overflow-y-auto">
            <h2 className="font-semibold mb-2 text-gray-700">Eventos</h2>
            <div className="space-y-2 text-sm">
                {events.map((e, i) => (
                    <div key={i} className="bg-green-100 text-green-800 px-2 py-1 rounded">
                        {e.content}
                    </div>
                ))}
            </div>
        </div>
    );
}