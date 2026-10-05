"use client";

export default function AlertBadge({ level = "LOW" }) {
  const normalized = (level || "LOW").toUpperCase();
  const classMap = {
    LOW: "low",
    MEDIUM: "medium",
    HIGH: "high",
  };

  const iconMap = {
    LOW: "✓",
    MEDIUM: "⚠",
    HIGH: "⚡",
  };

  return (
    <span className={`alert-badge ${classMap[normalized] || "low"}`}>
      <span>{iconMap[normalized] || "•"}</span>
      {normalized}
    </span>
  );
}
