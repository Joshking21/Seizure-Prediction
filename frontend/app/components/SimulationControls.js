"use client";

import { useState } from "react";

export default function SimulationControls({
  onGenerateSingle,
  onSimulateSession,
  loading,
  patientId,
  onPatientIdChange,
}) {
  const [mode, setMode] = useState("random");

  return (
    <div className="card slide-up" style={{ animationDelay: "0.2s" }}>
      <div className="card-title">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 20V10M18 20V4M6 20v-4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        Simulation Controls
      </div>

      <div className="controls-row">
        {/* Patient ID */}
        <div className="input-group">
          <label className="input-label" htmlFor="patient-id">Patient ID</label>
          <input
            id="patient-id"
            className="input-field"
            type="text"
            placeholder="e.g. CHB01"
            value={patientId}
            onChange={(e) => onPatientIdChange(e.target.value)}
          />
        </div>

        {/* Signal Mode */}
        <div className="input-group">
          <label className="input-label" htmlFor="signal-mode">Signal Type</label>
          <select
            id="signal-mode"
            className="input-field"
            value={mode}
            onChange={(e) => setMode(e.target.value)}
          >
            <option value="random">Random</option>
            <option value="normal">Normal (Inter-ictal)</option>
            <option value="preictal">Pre-ictal (Spikes)</option>
          </select>
        </div>

        {/* Actions */}
        <div className="input-group" style={{ justifyContent: "flex-end" }}>
          <label className="input-label">&nbsp;</label>
          <div style={{ display: "flex", gap: "8px" }}>
            <button
              className="btn btn-primary"
              onClick={() => onGenerateSingle(mode)}
              disabled={loading}
            >
              {loading ? (
                <span className="btn-loading">⏳</span>
              ) : (
                <span>⚡</span>
              )}
              Predict Window
            </button>
            <button
              className="btn btn-outline"
              onClick={() => onSimulateSession(mode)}
              disabled={loading}
            >
              <span>📊</span>
              Simulate Session
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
