import { Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import ThreadsPage from "./pages/ThreadsPage";
import AgentPage from "./pages/AgentPage";

function PrivateRoute({ children }) {
  const token = localStorage.getItem("token");
  return token ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/threads"
        element={
          <PrivateRoute>
            <ThreadsPage />
          </PrivateRoute>
        }
      />
      <Route
        path="/agent"
        element={
          <PrivateRoute>
            <AgentPage />
          </PrivateRoute>
        }
      />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
