"use client";

import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine,
} from "recharts";

export default function PredictionHistory({ predictions = [] }) {
  const chartData = predictions.map((p, i) => ({
    idx: i + 1,
    probability: (p.probability * 100).toFixed(1),
    alert: p.alert_level,
  }));

  if (!chartData.length) {
    return (
      <div className="empty-state">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M3 3v18h18" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M7 16l4-6 4 2 5-8" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <p>Prediction history will appear here as you run predictions.</p>
      </div>
    );
  }

  return (
    <div className="history-chart-wrapper">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 5 }}>
          <defs>
            <linearGradient id="probGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="rgba(255,255,255,0.05)"
            vertical={false}
          />
          <XAxis
            dataKey="idx"
            tick={{ fill: "#64748b", fontSize: 10 }}
            tickLine={false}
            axisLine={{ stroke: "rgba(255,255,255,0.08)" }}
            label={{ value: "Prediction #", position: "insideBottomRight", offset: -5, style: { fill: "#64748b", fontSize: 10 } }}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fill: "#64748b", fontSize: 10 }}
            tickLine={false}
            axisLine={{ stroke: "rgba(255,255,255,0.08)" }}
            label={{ value: "%", angle: -90, position: "insideLeft", style: { fill: "#64748b", fontSize: 10 } }}
          />
          <Tooltip
            contentStyle={{
              background: "#1a1f35",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: "8px",
              fontSize: "0.75rem",
              color: "#f1f5f9",
            }}
            formatter={(val) => [`${val}%`, "Probability"]}
          />
          {/* Threshold lines */}
          <ReferenceLine y={75} stroke="#ef4444" strokeDasharray="4 4" strokeOpacity={0.5} />
          <ReferenceLine y={50} stroke="#f59e0b" strokeDasharray="4 4" strokeOpacity={0.5} />
          <Area
            type="monotone"
            dataKey="probability"
            stroke="#3b82f6"
            strokeWidth={2}
            fill="url(#probGrad)"
            dot={{ r: 3, fill: "#3b82f6", strokeWidth: 0 }}
            activeDot={{ r: 5, fill: "#3b82f6", stroke: "#fff", strokeWidth: 2 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
