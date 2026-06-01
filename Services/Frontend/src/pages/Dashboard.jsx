import { useEffect, useState } from "react";
import client from "../api/client";

export default function Dashboard() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchHealth() {
      try {
        const response = await client.get("/health");
        setHealth(response.data);
      } catch (err) {
        setError(err.message || "Failed to connect to backend");
      } finally {
        setLoading(false);
      }
    }

    fetchHealth();
  }, []);

  if (loading) {
    return <div className="p-8 text-lg">Loading backend status...</div>;
  }

  if (error) {
    return <div className="p-8 text-red-600 font-medium">Error: {error}</div>;
  }

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="mx-auto max-w-4xl">
        <h1 className="mb-6 text-3xl font-bold text-slate-800">
          PLC Data Pipeline Dashboard
        </h1>

        <div className="rounded-lg border border-green-200 bg-green-50 p-6 shadow-sm">
          <h2 className="mb-2 text-xl font-semibold text-green-800">
            Backend Status
          </h2>
          <p className="text-green-700">
            Status: <span className="font-bold">{health?.status || "unknown"}</span>
          </p>
          <p className="text-green-700">
            Service: <span className="font-bold">{health?.service || "backend"}</span>
          </p>
        </div>
      </div>
       <div className="bg-blue-600 text-white p-4 rounded-xl shadow-lg">
        Tailwind is working
        </div>
    </div>
  );
}