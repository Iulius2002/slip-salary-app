import { useEffect, useState } from "react";
import { api } from "../api";

export default function Dashboard() {
  const [me, setMe] = useState<any>(null);

  useEffect(() => {
    api
      .get("/auth/me")
      .then((res) => setMe(res.data))
      .catch(() => {
        localStorage.removeItem("token");
        window.location.href = "/";
      });
  }, []);

  const logout = () => {
    localStorage.removeItem("token");
    window.location.href = "/";
  };

  const goManager = () => {
    window.location.href = "/manager";
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-2xl mx-auto">
        <header className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <button
            onClick={logout}
            className="bg-red-500 text-white px-3 py-2 rounded hover:bg-red-600"
          >
            Logout
          </button>
        </header>

        {me ? (
          <div className="space-y-4">
            <p className="text-gray-700">
              Welcome, <strong>{me.first_name} {me.last_name}</strong> ({me.email})
            </p>

            {me.role === "manager" ? (
              <button
                onClick={goManager}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
              >
                Go to Manager Dashboard
              </button>
            ) : (
              <p className="text-gray-600 text-sm">
                You are logged in as an employee. No manager actions available.
              </p>
            )}
          </div>
        ) : (
          <p>Loading your profile...</p>
        )}
      </div>
    </div>
  );
}
