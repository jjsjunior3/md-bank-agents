import { Link } from "react-router-dom";
import { useAppState } from "./StateContext";

export default function AppLayout({ children }) {
    const { stateVisible, setStateVisible, state } = useAppState();

    return (
        <div className="h-screen flex flex-col bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white">
            <header className="p-4 border-b border-gray-700 flex justify-between items-center">
                <h1 className="font-bold text-lg">MDBank AI</h1>
                <div className="flex items-center gap-4">
                    <nav className="flex items-center gap-2">
                        <Link to="/" className="text-sm hover:underline">Chat</Link>
                        <Link to="/state-util" className="text-sm hover:underline">Conversa</Link>
                    </nav>
                    <button
                        className="text-sm px-2 py-1 bg-gray-700 rounded hover:bg-gray-600"
                        onClick={() => setStateVisible(!stateVisible)}
                    >
                        {stateVisible ? "Fechar State" : "Abrir State"}
                    </button>
                </div>
            </header>

            <div className="flex flex-1 overflow-hidden">
                <main className="flex-1 flex flex-col overflow-hidden">{children}</main>

                {stateVisible && (
                    <aside className="w-80 bg-gray-800 border-l border-gray-700 p-4 flex flex-col gap-2 overflow-y-auto transition-all duration-300">
                        <h2 className="font-bold text-lg mb-2">State Compartilhado</h2>
                        <pre className="text-sm bg-gray-900 p-2 rounded flex-1 overflow-auto">
                            {JSON.stringify(state, null, 2)}
                        </pre>
                    </aside>
                )}
            </div>
        </div>
    );
}