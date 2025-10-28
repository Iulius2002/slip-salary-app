import { useEffect, useState } from "react";
import { api } from "../api";
import axios from "axios";

type User = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: "manager" | "employee";
};

type RunResult = {
  endpoint: string;
  ok?: boolean;
  error?: string;
  payload?: any;
};

export default function Manager() {
  const [me, setMe] = useState<User | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [results, setResults] = useState<RunResult[]>([]);
  const [archives, setArchives] = useState<{ csv: any[]; pdf: any[] }>({ csv: [], pdf: [] });

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      window.location.href = "/";
      return;
    }

    api
      .get("/auth/me")
      .then((res) => {
        if (res.data.role !== "manager") {
          alert("Managers only.");
          localStorage.removeItem("token");
          window.location.href = "/";
          return;
        }
        setMe(res.data);
        // load archives
        api.get("/archives").then((a) => setArchives(a.data)).catch(() => {});
      })
      .catch(() => {
        localStorage.removeItem("token");
        window.location.href = "/";
      });
  }, []);

  const run = async (endpoint: string, path: string) => {
    setBusy(endpoint);
    try {
      const res = await api.post(path, {});
      setResults((prev) => [{ endpoint, ok: true, payload: res.data }, ...prev]);
      // refresh archives after actions that may create/archive files
      api.get("/archives").then((a) => setArchives(a.data)).catch(() => {});
    } catch (err: any) {
      const msg = axios.isAxiosError(err) ? err.response?.data?.detail || err.message : String(err);
      setResults((prev) => [{ endpoint, ok: false, error: msg }, ...prev]);
    } finally {
      setBusy(null);
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    window.location.href = "/";
  };

  const refreshArchives = async () => {
    const a = await api.get("/archives");
    setArchives(a.data);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-3xl mx-auto">
        <header className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold">Manager Dashboard</h1>
            <p className="text-sm text-gray-600">Logged in as: {me?.email} ({me?.role})</p>
          </div>
          <button onClick={logout} className="bg-red-500 text-white px-3 py-2 rounded">Logout</button>
        </header>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
          <button
            onClick={() => run("createAggregatedEmployeeData", "/createAggregatedEmployeeData")}
            disabled={busy !== null}
            className="bg-blue-600 text-white p-3 rounded hover:bg-blue-700 disabled:opacity-60"
          >
            {busy === "createAggregatedEmployeeData" ? "Working…" : "Create CSV"}
          </button>

          <button
            onClick={() => run("sendAggregatedEmployeeData", "/sendAggregatedEmployeeData")}
            disabled={busy !== null}
            className="bg-indigo-600 text-white p-3 rounded hover:bg-indigo-700 disabled:opacity-60"
          >
            {busy === "sendAggregatedEmployeeData" ? "Sending…" : "Send CSV (MailHog)"}
          </button>

          <button
            onClick={() => run("createPdfForEmployees", "/createPdfForEmployees")}
            disabled={busy !== null}
            className="bg-emerald-600 text-white p-3 rounded hover:bg-emerald-700 disabled:opacity-60"
          >
            {busy === "createPdfForEmployees" ? "Generating…" : "Create PDFs"}
          </button>

          <button
            onClick={() => run("sendPdfToEmployees", "/sendPdfToEmployees")}
            disabled={busy !== null}
            className="bg-teal-600 text-white p-3 rounded hover:bg-teal-700 disabled:opacity-60"
          >
            {busy === "sendPdfToEmployees" ? "Sending…" : "Send PDFs (MailHog)"}
          </button>
        </div>

        {/* Archives Panel */}
        <div className="bg-white rounded shadow p-4 mb-6">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold">Archives</h2>
            <div className="space-x-2">
              <button onClick={refreshArchives} className="text-sm bg-gray-200 px-2 py-1 rounded">Refresh</button>
              <a
                className="text-sm bg-gray-200 px-2 py-1 rounded"
                href="http://127.0.0.1:8000/archives/browse_public"
                target="_blank"
                rel="noreferrer"
              >
                Open Archives Browser
              </a>
              <a
                className="text-sm bg-gray-200 px-2 py-1 rounded"
                href="http://localhost:8025"
                target="_blank"
                rel="noreferrer"
              >
                Open MailHog
              </a>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h3 className="font-medium mb-2">CSV</h3>
              {archives.csv.length === 0 ? (
                <p className="text-sm text-gray-600">No archived CSV yet.</p>
              ) : (
                <ul className="space-y-1">
                  {archives.csv.map((f: any, idx: number) => (
                    <li key={idx} className="text-sm">
                      <a className="text-blue-600 underline" href={`http://127.0.0.1:8000${f.url}`} target="_blank" rel="noreferrer">
                        {f.name}
                      </a>{" "}
                      <span className="text-gray-500">— {f.modified} — {f.size_bytes} B</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div>
              <h3 className="font-medium mb-2">PDF</h3>
              {archives.pdf.length === 0 ? (
                <p className="text-sm text-gray-600">No archived PDF yet.</p>
              ) : (
                <ul className="space-y-1">
                  {archives.pdf.map((f: any, idx: number) => (
                    <li key={idx} className="text-sm">
                      <a className="text-blue-600 underline" href={`http://127.0.0.1:8000${f.url}`} target="_blank" rel="noreferrer">
                        {f.name}
                      </a>{" "}
                      <span className="text-gray-500">— {f.modified} — {f.size_bytes} B</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>

        {/* Run results */}
        <div className="bg-white rounded shadow p-4">
          <h2 className="font-semibold mb-3">Run results</h2>
          {results.length === 0 ? (
            <p className="text-sm text-gray-600">No runs yet.</p>
          ) : (
            <ul className="space-y-3">
              {results.map((r, idx) => (
                <li key={idx} className="border rounded p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-xs">{r.endpoint}</span>
                    <span className={`text-xs ${r.ok ? "text-emerald-700" : "text-red-600"}`}>
                      {r.ok ? "OK" : "ERROR"}
                    </span>
                  </div>
                  <pre className="text-xs overflow-auto bg-gray-50 p-2 rounded">
                    {JSON.stringify(r.ok ? r.payload : { error: r.error }, null, 2)}
                  </pre>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
