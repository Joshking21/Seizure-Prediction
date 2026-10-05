"""
schemas/prediction.py
Request and response models for the prediction endpoint.
Pydantic validates all incoming and outgoing data automatically.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class EEGWindowRequest(BaseModel):
    """
    Raw EEG window sent from the dashboard or device.

    eeg_data: 2D list of shape (n_channels, n_samples)
               n_channels = 18
               n_samples  = 1280  (5 seconds at 256 Hz)

    Example (truncated):
    {
      "eeg_data": [[0.001, -0.002, ...], [0.003, 0.001, ...], ...],
      "patient_id": "CHB01",
      "timestamp": "2026-07-06T02:38:22"
    }
    """
    eeg_data:   List[List[float]] = Field(
        ...,
        description="EEG signal: shape (n_channels, n_samples)"
    )
    patient_id: Optional[str] = Field(default="unknown",
                                      description="Patient identifier")
    timestamp:  Optional[str] = Field(default=None,
                                      description="ISO timestamp of the window")


class PredictionResponse(BaseModel):
    """
    Prediction result returned to the dashboard.
    """
    patient_id:    str
    timestamp:     str
    probability:   float = Field(..., description="P(pre-ictal) in [0, 1]")
    prediction:    str   = Field(..., description="INTER-ICTAL or PRE-ICTAL")
    alert_level:   str   = Field(..., description="LOW, MEDIUM, or HIGH")
    confidence:    str   = Field(..., description="Human-readable confidence %")
    model_version: str   = Field(default="1.0.0")
    processing_ms: Optional[float] = None


class HealthResponse(BaseModel):
    status:        str
    model_loaded:  bool
    scaler_loaded: bool
    model_version: str
    uptime_seconds: float


class BatchEEGRequest(BaseModel):
    """
    Multiple EEG windows in one request (for bulk inference).
    """
    windows:    List[List[List[float]]] = Field(
        ...,
        description="List of EEG windows, each shape (n_channels, n_samples)"
    )
    patient_id: Optional[str] = "unknown"


class BatchPredictionResponse(BaseModel):
    patient_id:   str
    n_windows:    int
    predictions:  List[PredictionResponse]
    summary: dict = Field(
        description="Counts of LOW/MEDIUM/HIGH alerts across all windows"
    )


class FileUploadPredictionResponse(BaseModel):
    filename:            str
    format:              str
    patient_id:          str
    sampling_rate:       int = 256
    total_duration_sec:  float
    total_windows:       int
    summary:             dict
    overall_risk:        str
    average_probability: float
    predictions:         List[PredictionResponse]
    sample_waveform:     Optional[List[List[float]]] = None
    channels:            Optional[List[str]] = None


class SampleDatasetItem(BaseModel):
    id:          str
    name:        str
    description: str
    patient_id:  str
    format:      str
    duration_sec: float
    expected_state: str

