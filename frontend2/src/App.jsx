import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { StateProvider } from "./StateContext";
import ChatPage from "./ChatPage";
import StateUtilPage from "./StateUtilPage";

export default function App() {
    return (
        <StateProvider>
            <Router>
                <Routes>
                    <Route path="/" element={<ChatPage />} />
                    <Route path="/state-util" element={<StateUtilPage />} />
                </Routes>
            </Router>
        </StateProvider>
    );
}