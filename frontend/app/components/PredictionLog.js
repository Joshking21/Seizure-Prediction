"use client";

import { useState, useMemo } from "react";
import AlertBadge from "./AlertBadge";

export default function PredictionLog({ predictions = [] }) {
  const [filter, setFilter] = useState("ALL");

  const filtered = useMemo(() => {
    if (filter === "ALL") return predictions;
    return predictions.filter(
      (p) => (p.alert_level || "").toUpperCase() === filter
    );
  }, [predictions, filter]);

  const exportCSV = () => {
    if (!predictions.length) return;

    const headers = ["#", "Timestamp", "Patient", "Probability", "Prediction", "Alert", "Latency (ms)"];
    const rows = predictions.map((p, i) => [
      i + 1,
      p.timestamp || "—",
      p.patient_id || "—",
      p.probability?.toFixed(4) || "—",
      p.prediction || "—",
      p.alert_level || "—",
      p.processing_ms?.toFixed(1) || "—",
    ]);

    const csv = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `predictions_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div>
      <div className="log-header">
        <div className="log-filters">
          {["ALL", "LOW", "MEDIUM", "HIGH"].map((f) => (
            <button
              key={f}
              className={`filter-chip ${filter === f ? "active" : ""}`}
              onClick={() => setFilter(f)}
            >
              {f}
            </button>
          ))}
        </div>
        <button className="btn btn-outline btn-sm" onClick={exportCSV}>
          📥 Export CSV
        </button>
      </div>

      {filtered.length === 0 ? (
        <div className="empty-state" style={{ padding: "32px" }}>
          <p style={{ fontSize: "0.8rem" }}>
            {predictions.length === 0
              ? "No predictions recorded yet."
              : `No ${filter} predictions found.`}
          </p>
        </div>
      ) : (
        <div className="log-table-wrapper">
          <table className="log-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Timestamp</th>
                <th>Patient</th>
                <th>Probability</th>
                <th>Prediction</th>
                <th>Alert</th>
                <th>Latency</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((p, i) => (
                <tr key={i}>
                  <td className="mono">{predictions.indexOf(p) + 1}</td>
                  <td className="mono" style={{ fontSize: "0.72rem" }}>
                    {p.timestamp
                      ? new Date(p.timestamp).toLocaleTimeString()
                      : "—"}
                  </td>
                  <td>{p.patient_id || "—"}</td>
                  <td className="mono" style={{
                    color: p.probability >= 0.75
                      ? "var(--accent-red)"
                      : p.probability >= 0.5
                        ? "var(--accent-amber)"
                        : "var(--accent-green)",
                    fontWeight: 600,
                  }}>
                    {(p.probability * 100).toFixed(1)}%
                  </td>
                  <td>{p.prediction || "—"}</td>
                  <td><AlertBadge level={p.alert_level} /></td>
                  <td className="mono">
                    {p.processing_ms ? `${p.processing_ms.toFixed(1)}ms` : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
