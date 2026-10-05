"use client";

import { useEffect, useState } from "react";
import { fetchHealth } from "../../lib/api";

export default function StatusBar() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;

    async function poll() {
      try {
        const data = await fetchHealth();
        if (active) { setHealth(data); setError(false); }
      } catch {
        if (active) { setHealth(null); setError(true); }
      }
    }

    poll();
    const id = setInterval(poll, 10_000);
    return () => { active = false; clearInterval(id); };
  }, []);

  const connected = health && !error;

  const items = [
    {
      icon: "🧠",
      iconClass: connected && health.model_loaded ? "green" : "red",
      label: "Model",
      value: connected && health.model_loaded ? "Loaded" : "Offline",
      valueClass: connected && health.model_loaded ? "ok" : "error",
    },
    {
      icon: "⚖️",
      iconClass: connected && health.scaler_loaded ? "green" : "red",
      label: "Scaler",
      value: connected && health.scaler_loaded ? "Loaded" : "Offline",
      valueClass: connected && health.scaler_loaded ? "ok" : "error",
    },
    {
      icon: "🔌",
      iconClass: connected ? "green" : "red",
      label: "Server Status",
      value: connected ? health.status?.toUpperCase() : "Disconnected",
      valueClass: connected ? "ok" : "error",
    },
    {
      icon: "⏱️",
      iconClass: "blue",
      label: "Uptime",
      value: connected
        ? formatUptime(health.uptime_seconds)
        : "—",
      valueClass: "",
    },
  ];

  return (
    <div className="status-bar fade-in">
      {items.map((item, i) => (
        <div className="status-item" key={i}>
          <div className={`status-icon ${item.iconClass}`}>
            {item.icon}
          </div>
          <div>
            <div className="status-label">{item.label}</div>
            <div className={`status-value ${item.valueClass}`}>
              {item.value}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function formatUptime(seconds) {
  if (!seconds) return "—";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}
