import { useEffect, useState } from "react";
import axios from "axios";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Manager from "./pages/Manager";

function StatusBar() {
  const [health, setHealth] = useState<any>(null);
  const baseURL = import.meta.env.VITE_API_URL;

  useEffect(() => {
    axios
      .get(`${baseURL}/health`, { headers: { "Idempotency-Key": "demo-ui-health" } })
      .then((res) => setHealth(res.data))
      .catch((err) => setHealth({ error: String(err) }));
  }, [baseURL]);

  return (
    <div style={{ padding: "0.5rem", fontSize: 12, color: "#444" }}>
      API: {baseURL} — {health?.status ? "OK" : "…checking"}
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <StatusBar />
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/manager" element={<Manager />} />
      </Routes>
    </BrowserRouter>
  );
}
