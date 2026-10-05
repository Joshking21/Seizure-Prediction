"use client";

import { useState, useRef } from "react";
import { uploadEEGDataset, runSampleDataset } from "../../lib/api";

export default function DatasetUploader({
  patientId,
  onPatientIdChange,
  onDatasetEvaluated,
  onStreamWindow,
  loading,
  setLoading,
  setError,
}) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingIndex, setStreamingIndex] = useState(0);
  const streamIntervalRef = useRef(null);
  const fileInputRef = useRef(null);

  const handleFileDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      validateAndSetFile(file);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (file) => {
    const ext = file.name.split(".").pop().toLowerCase();
    if (!["edf", "csv", "json"].includes(ext)) {
      setError(`Unsupported file format (.${ext}). Please upload .edf, .csv, or .json`);
      return;
    }
    setSelectedFile(file);
    setUploadResult(null);
    setError(null);
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;
    setLoading(true);
    setError(null);
    stopStreaming();

    try {
      if (selectedFile.isSample) {
        const result = await runSampleDataset(selectedFile.sampleId, patientId);
        setUploadResult(result);
        if (onDatasetEvaluated) {
          onDatasetEvaluated(result);
        }
      } else if (selectedFile instanceof File) {
        const result = await uploadEEGDataset(selectedFile, patientId, 30);
        setUploadResult(result);
        if (onDatasetEvaluated) {
          onDatasetEvaluated(result);
        }
      } else {
        setError("Please choose a valid .edf, .csv, or .json file to upload.");
      }
    } catch (err) {
      setError(err.message || "Failed to analyze dataset.");
    } finally {
      setLoading(false);
    }
  };

  const handleRunSample = async (sampleId) => {
    setLoading(true);
    setError(null);
    stopStreaming();

    try {
      const result = await runSampleDataset(sampleId, patientId);
      setUploadResult(result);
      setSelectedFile({
        name: `${sampleId}.edf (Calibrated Sample)`,
        size: 20 * 256 * 18 * 4,
        isSample: true,
        sampleId: sampleId,
      });
      if (onDatasetEvaluated) {
        onDatasetEvaluated(result);
      }
    } catch (err) {
      setError(err.message || "Failed to run sample dataset.");
    } finally {
      setLoading(false);
    }
  };

  const startStreaming = () => {
    if (!uploadResult || !uploadResult.predictions || uploadResult.predictions.length === 0) return;
    setIsStreaming(true);
    setStreamingIndex(0);

    let idx = 0;
    const total = uploadResult.predictions.length;

    // Immediately trigger first window
    if (onStreamWindow) {
      onStreamWindow(uploadResult.predictions[0], idx, uploadResult.sample_waveform);
    }

    if (streamIntervalRef.current) clearInterval(streamIntervalRef.current);

    streamIntervalRef.current = setInterval(() => {
      idx += 1;
      if (idx >= total) {
        stopStreaming();
        return;
      }
      setStreamingIndex(idx);
      if (onStreamWindow) {
        onStreamWindow(uploadResult.predictions[idx], idx, null);
      }
    }, 1200);
  };

  const stopStreaming = () => {
    if (streamIntervalRef.current) {
      clearInterval(streamIntervalRef.current);
      streamIntervalRef.current = null;
    }
    setIsStreaming(false);
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return "0 B";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(2)} MB`;
  };

  return (
    <div className="card slide-up" style={{ animationDelay: "0.2s" }}>
      <div className="card-title" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: "18px", height: "18px" }}>
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" strokeLinecap="round" strokeLinejoin="round" />
            <polyline points="17 8 12 3 7 8" strokeLinecap="round" strokeLinejoin="round" />
            <line x1="12" y1="3" x2="12" y2="15" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          Dataset & Recording Input (Pre-Trained Pipeline)
        </div>
        <div style={{ display: "flex", gap: "6px" }}>
          <span className="badge" style={{ background: "rgba(59, 130, 246, 0.15)", color: "#60a5fa", border: "1px solid rgba(59, 130, 246, 0.3)" }}>.EDF</span>
          <span className="badge" style={{ background: "rgba(16, 185, 129, 0.15)", color: "#34d399", border: "1px solid rgba(16, 185, 129, 0.3)" }}>.CSV</span>
          <span className="badge" style={{ background: "rgba(139, 92, 246, 0.15)", color: "#c084fc", border: "1px solid rgba(139, 92, 246, 0.3)" }}>.JSON</span>
        </div>
      </div>

      {/* Quick Sample Selector */}
      <div style={{ marginBottom: "16px", background: "rgba(255,255,255,0.02)", padding: "10px 14px", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
        <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "8px", display: "flex", alignItems: "center", gap: "6px" }}>
          <span>⚡ Fast Test with Pre-Trained Dataset Samples:</span>
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
          <button
            className="btn btn-outline btn-sm"
            onClick={() => handleRunSample("chb01_preictal")}
            disabled={loading}
            style={{ fontSize: "0.75rem", borderColor: "rgba(239, 68, 68, 0.4)", color: "#f87171" }}
          >
            🔴 CHB01 Pre-Ictal Sample (High Seizure Risk)
          </button>
          <button
            className="btn btn-outline btn-sm"
            onClick={() => handleRunSample("chb01_interictal")}
            disabled={loading}
            style={{ fontSize: "0.75rem", borderColor: "rgba(16, 185, 129, 0.4)", color: "#34d399" }}
          >
            🟢 CHB01 Inter-Ictal Baseline (Normal)
          </button>
        </div>
      </div>

      {/* Drag & Drop Zone */}
      <div
        className={`dataset-dropzone ${dragOver ? "dragover" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleFileDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".edf,.csv,.json"
          style={{ display: "none" }}
          onChange={handleFileSelect}
        />
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "6px" }}>
          <div style={{
            width: "42px",
            height: "42px",
            borderRadius: "50%",
            background: "rgba(59, 130, 246, 0.12)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "var(--accent-blue)",
            fontSize: "1.2rem",
          }}>
            📁
          </div>
          <div style={{ fontWeight: 500, fontSize: "0.9rem", color: "var(--text-primary)" }}>
            {selectedFile ? selectedFile.name : "Drag & drop an EEG dataset recording here"}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            {selectedFile
              ? `${formatFileSize(selectedFile.size)} • Click to choose a different file`
              : "Supports genuine CHB-MIT PhysioNet .EDF files, 18-channel CSV, or JSON recordings (256 Hz)"}
          </div>
        </div>
      </div>

      {/* Controls row */}
      <div className="controls-row" style={{ marginTop: "14px", alignItems: "flex-end" }}>
        <div className="input-group" style={{ flex: 1 }}>
          <label className="input-label" htmlFor="upload-patient-id">Subject / Patient ID</label>
          <input
            id="upload-patient-id"
            className="input-field"
            type="text"
            placeholder="e.g. CHB01"
            value={patientId}
            onChange={(e) => onPatientIdChange(e.target.value)}
          />
        </div>

        <div style={{ display: "flex", gap: "8px" }}>
          <button
            className="btn btn-primary"
            onClick={handleAnalyze}
            disabled={loading || !selectedFile}
            style={{ minWidth: "180px" }}
          >
            {loading ? (
              <>
                <span className="spinner" style={{ width: "14px", height: "14px", borderWidth: "2px" }} />
                Analyzing Dataset…
              </>
            ) : (
              <>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: "16px", height: "16px" }}>
                  <polygon points="5 3 19 12 5 21 5 3" />
                </svg>
                Run Model Inference
              </>
            )}
          </button>

          {selectedFile && (
            <button
              className="btn btn-outline"
              onClick={() => {
                setSelectedFile(null);
                setUploadResult(null);
                stopStreaming();
              }}
              disabled={loading}
              title="Clear selection"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Dataset Results Summary Card */}
      {uploadResult && (
        <div
          className="fade-in"
          style={{
            marginTop: "16px",
            padding: "14px 18px",
            background: "rgba(255, 255, 255, 0.03)",
            borderRadius: "var(--radius-md)",
            border: "1px solid var(--border-light)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px", flexWrap: "wrap", gap: "8px" }}>
            <div>
              <div style={{ fontWeight: 600, fontSize: "0.92rem", display: "flex", alignItems: "center", gap: "8px" }}>
                <span>📊 Evaluation of {uploadResult.filename}</span>
                <span
                  className="badge"
                  style={{
                    background:
                      uploadResult.overall_risk === "HIGH"
                        ? "rgba(239, 68, 68, 0.2)"
                        : uploadResult.overall_risk === "MEDIUM"
                        ? "rgba(245, 158, 11, 0.2)"
                        : "rgba(16, 185, 129, 0.2)",
                    color:
                      uploadResult.overall_risk === "HIGH"
                        ? "#f87171"
                        : uploadResult.overall_risk === "MEDIUM"
                        ? "#fbbf24"
                        : "#34d399",
                    border: `1px solid ${
                      uploadResult.overall_risk === "HIGH"
                        ? "rgba(239, 68, 68, 0.4)"
                        : uploadResult.overall_risk === "MEDIUM"
                        ? "rgba(245, 158, 11, 0.4)"
                        : "rgba(16, 185, 129, 0.4)"
                    }`,
                  }}
                >
                  Overall: {uploadResult.overall_risk} RISK
                </span>
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "2px" }}>
                Format: {uploadResult.format.toUpperCase()} • Duration: {uploadResult.total_duration_sec}s • {uploadResult.total_windows} windows evaluated
              </div>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              {!isStreaming ? (
                <button
                  className="btn btn-outline btn-sm"
                  onClick={startStreaming}
                  style={{ borderColor: "rgba(59, 130, 246, 0.5)", color: "var(--accent-blue)" }}
                >
                  ▶ Stream to Live Monitor
                </button>
              ) : (
                <button
                  className="btn btn-outline btn-sm"
                  onClick={stopStreaming}
                  style={{ borderColor: "rgba(239, 68, 68, 0.5)", color: "var(--accent-red)" }}
                >
                  ⏹ Pause Stream ({streamingIndex + 1}/{uploadResult.total_windows})
                </button>
              )}
            </div>
          </div>

          {/* Mini Stats Breakdown */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(110px, 1fr))", gap: "10px", marginTop: "10px" }}>
            <div style={{ background: "rgba(0,0,0,0.2)", padding: "8px 12px", borderRadius: "var(--radius-sm)", textAlign: "center" }}>
              <div style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>AVG PROBABILITY</div>
              <div style={{ fontSize: "1.1rem", fontWeight: 700, fontFamily: "var(--font-mono)", color: "var(--accent-cyan)" }}>
                {(uploadResult.average_probability * 100).toFixed(1)}%
              </div>
            </div>
            <div style={{ background: "rgba(0,0,0,0.2)", padding: "8px 12px", borderRadius: "var(--radius-sm)", textAlign: "center" }}>
              <div style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>LOW RISK</div>
              <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--accent-green)" }}>
                {uploadResult.summary.LOW || 0}
              </div>
            </div>
            <div style={{ background: "rgba(0,0,0,0.2)", padding: "8px 12px", borderRadius: "var(--radius-sm)", textAlign: "center" }}>
              <div style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>MEDIUM RISK</div>
              <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--accent-amber)" }}>
                {uploadResult.summary.MEDIUM || 0}
              </div>
            </div>
            <div style={{ background: "rgba(0,0,0,0.2)", padding: "8px 12px", borderRadius: "var(--radius-sm)", textAlign: "center" }}>
              <div style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>HIGH RISK (PRE-ICTAL)</div>
              <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--accent-red)" }}>
                {uploadResult.summary.HIGH || 0}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
