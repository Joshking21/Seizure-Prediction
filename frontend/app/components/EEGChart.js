"use client";

import { useMemo } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from "recharts";

const CHANNEL_COLORS = [
  "#3b82f6", "#06b6d4", "#8b5cf6", "#10b981",
  "#f59e0b", "#ef4444", "#ec4899", "#14b8a6",
];

const DISPLAY_CHANNELS = 4;
const DOWNSAMPLE = 8;

export default function EEGChart({ eegData }) {
  const chartData = useMemo(() => {
    if (!eegData || eegData.length === 0) return [];

    const nSamples = eegData[0]?.length || 0;
    const points = [];

    for (let i = 0; i < nSamples; i += DOWNSAMPLE) {
      const point = { sample: i };
      for (let ch = 0; ch < Math.min(eegData.length, DISPLAY_CHANNELS); ch++) {
        point[`ch${ch + 1}`] = (eegData[ch][i] * 1e6).toFixed(2);
      }
      points.push(point);
    }

    return points;
  }, [eegData]);

  if (!chartData.length) {
    return (
      <div className="empty-state">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M3 12h2l3-9 4 18 3-9h2l3-6 2 6h2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <p>No EEG data yet. Load a dataset sample to begin.</p>
      </div>
    );
  }

  return (
    <div className="eeg-chart-wrapper">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="rgba(255,255,255,0.05)"
            vertical={false}
          />
          <XAxis
            dataKey="sample"
            tick={{ fill: "#64748b", fontSize: 10 }}
            tickLine={false}
            axisLine={{ stroke: "rgba(255,255,255,0.08)" }}
            label={{ value: "Samples", position: "insideBottomRight", offset: -5, style: { fill: "#64748b", fontSize: 10 } }}
          />
          <YAxis
            tick={{ fill: "#64748b", fontSize: 10 }}
            tickLine={false}
            axisLine={{ stroke: "rgba(255,255,255,0.08)" }}
            label={{ value: "uV", angle: -90, position: "insideLeft", style: { fill: "#64748b", fontSize: 10 } }}
          />
          <Tooltip
            contentStyle={{
              background: "#1a1f35",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: "8px",
              fontSize: "0.75rem",
              color: "#f1f5f9",
            }}
          />
          {Array.from({ length: Math.min(eegData?.length || 0, DISPLAY_CHANNELS) }, (_, ch) => (
            <Line
              key={ch}
              type="monotone"
              dataKey={`ch${ch + 1}`}
              stroke={CHANNEL_COLORS[ch]}
              strokeWidth={1.2}
              dot={false}
              name={`Channel ${ch + 1}`}
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
