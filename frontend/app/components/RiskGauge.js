"use client";

export default function RiskGauge({ probability = 0 }) {
  const pct = Math.max(0, Math.min(probability * 100, 100));

  // Gauge geometry: arc from 180° to 0° (left to right semicircle)
  const cx = 110, cy = 120, r = 85;
  const circumference = Math.PI * r; // half-circle
  const offset = circumference - (pct / 100) * circumference;

  // Color based on risk
  let color, label;
  if (pct >= 75) {
    color = "#ef4444";
    label = "HIGH RISK";
  } else if (pct >= 50) {
    color = "#f59e0b";
    label = "MEDIUM RISK";
  } else {
    color = "#10b981";
    label = "LOW RISK";
  }

  return (
    <div className="gauge-container">
      <svg className="gauge-svg" viewBox="0 0 220 140">
        {/* Background arc */}
        <path
          className="gauge-bg"
          d={describeArc(cx, cy, r, 180, 360)}
          fill="none"
          stroke="#1e293b"
          strokeWidth="14"
          strokeLinecap="round"
        />
        {/* Filled arc */}
        <path
          d={describeArc(cx, cy, r, 180, 360)}
          fill="none"
          stroke={color}
          strokeWidth="14"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{
            transition: "stroke-dashoffset 0.8s cubic-bezier(0.4, 0, 0.2, 1), stroke 0.5s ease",
            filter: `drop-shadow(0 0 8px ${color}80)`,
          }}
        />
        {/* Center text */}
        <text
          x={cx}
          y={cy - 10}
          textAnchor="middle"
          fill={color}
          style={{
            fontSize: "2.2rem",
            fontWeight: 800,
            fontFamily: "'JetBrains Mono', monospace",
          }}
        >
          {pct.toFixed(1)}%
        </text>
        <text
          x={cx}
          y={cy + 16}
          textAnchor="middle"
          fill="#94a3b8"
          style={{ fontSize: "0.7rem", fontWeight: 600, letterSpacing: "0.08em" }}
        >
          SEIZURE PROBABILITY
        </text>
      </svg>
      <div className="gauge-label" style={{ color, fontWeight: 700 }}>
        {label}
      </div>
    </div>
  );
}

// Helper to draw an SVG arc path
function describeArc(cx, cy, r, startAngle, endAngle) {
  const startRad = (startAngle * Math.PI) / 180;
  const endRad = (endAngle * Math.PI) / 180;

  const x1 = cx + r * Math.cos(startRad);
  const y1 = cy + r * Math.sin(startRad);
  const x2 = cx + r * Math.cos(endRad);
  const y2 = cy + r * Math.sin(endRad);

  const largeArc = endAngle - startAngle > 180 ? 1 : 0;

  return `M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`;
}
