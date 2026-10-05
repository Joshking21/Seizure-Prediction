"use client";

export default function StatsPanel({ predictions = [] }) {
  const total = predictions.length;
  const avgProb = total > 0
    ? predictions.reduce((s, p) => s + p.probability, 0) / total
    : 0;
  const avgLatency = total > 0
    ? predictions.reduce((s, p) => s + (p.processing_ms || 0), 0) / total
    : 0;

  const alertCounts = { LOW: 0, MEDIUM: 0, HIGH: 0 };
  predictions.forEach((p) => {
    const level = (p.alert_level || "LOW").toUpperCase();
    if (alertCounts[level] !== undefined) alertCounts[level]++;
  });

  const stats = [
    {
      value: total,
      label: "Total Predictions",
      color: "var(--accent-blue)",
    },
    {
      value: `${(avgProb * 100).toFixed(1)}%`,
      label: "Avg Probability",
      color: avgProb >= 0.5 ? "var(--accent-amber)" : "var(--accent-green)",
    },
    {
      value: `${avgLatency.toFixed(0)}ms`,
      label: "Avg Latency",
      color: "var(--accent-purple)",
    },
    {
      value: alertCounts.HIGH,
      label: "High Alerts",
      color: alertCounts.HIGH > 0 ? "var(--accent-red)" : "var(--accent-green)",
    },
  ];

  // Alert distribution bar
  const barTotal = Math.max(total, 1);

  return (
    <div>
      <div className="stats-grid">
        {stats.map((s, i) => (
          <div className="stat-card" key={i}>
            <div className="stat-value" style={{ color: s.color }}>{s.value}</div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </div>

      {total > 0 && (
        <div style={{ marginTop: "16px" }}>
          <div className="input-label" style={{ marginBottom: "8px" }}>
            Alert Distribution
          </div>
          <div style={{
            display: "flex",
            height: "8px",
            borderRadius: "4px",
            overflow: "hidden",
            background: "var(--bg-elevated)",
          }}>
            <div style={{
              width: `${(alertCounts.LOW / barTotal) * 100}%`,
              background: "var(--accent-green)",
              transition: "width 0.5s ease",
            }} />
            <div style={{
              width: `${(alertCounts.MEDIUM / barTotal) * 100}%`,
              background: "var(--accent-amber)",
              transition: "width 0.5s ease",
            }} />
            <div style={{
              width: `${(alertCounts.HIGH / barTotal) * 100}%`,
              background: "var(--accent-red)",
              transition: "width 0.5s ease",
            }} />
          </div>
          <div style={{
            display: "flex",
            justifyContent: "space-between",
            marginTop: "6px",
            fontSize: "0.68rem",
            color: "var(--text-muted)",
          }}>
            <span>🟢 Low: {alertCounts.LOW}</span>
            <span>🟡 Medium: {alertCounts.MEDIUM}</span>
            <span>🔴 High: {alertCounts.HIGH}</span>
          </div>
        </div>
      )}
    </div>
  );
}
