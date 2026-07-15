import { createContext, useContext, useState } from "react";

const StateContext = createContext(null);

export function StateProvider({ children }) {
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [state, setState] = useState({});
    const [stateVisible, setStateVisible] = useState(false);

    function updateState(newState) {
        setState((prev) => ({ ...prev, ...newState }));
    }

    return (
        <StateContext.Provider
            value={{
                messages,
                setMessages,
                loading,
                setLoading,
                state,
                updateState,
                stateVisible,
                setStateVisible,
            }}
        >
            {children}
        </StateContext.Provider>
    );
}

export function useAppState() {
    const ctx = useContext(StateContext);
    if (!ctx) {
        throw new Error("useAppState precisa estar dentro de <StateProvider>");
    }
    return ctx;
}