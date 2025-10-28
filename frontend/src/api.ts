import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

export const api = axios.create({
  baseURL,
});

// Attach Authorization + Idempotency-Key on each POST
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers = config.headers ?? {};
    config.headers["Authorization"] = `Bearer ${token}`;
  }
  // Add a random Idempotency-Key for non-idempotent methods
  if ((config.method ?? "get").toLowerCase() === "post") {
    const key = (crypto && "randomUUID" in crypto)
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    config.headers = config.headers ?? {};
    config.headers["Idempotency-Key"] = key;
  }
  return config;
});
