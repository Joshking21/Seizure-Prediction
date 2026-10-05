from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from datetime import datetime
from typing import Optional, List

from app.schemas.prediction import (
    EEGWindowRequest, PredictionResponse,
    BatchEEGRequest, BatchPredictionResponse,
    FileUploadPredictionResponse, SampleDatasetItem,
)
from app import inference
from app.dataset_parser import (
    parse_uploaded_dataset,
    generate_sample_eeg,
    CANONICAL_CHANNELS,
)

router = APIRouter(prefix="/predict", tags=["Prediction"])


@router.post("/window", response_model=PredictionResponse)
async def predict_single_window(request: EEGWindowRequest):
    if not inference.is_ready():
        raise HTTPException(status_code=503, detail="Model not loaded.")

    try:
        result = inference.predict_window(request.eeg_data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

    return PredictionResponse(
        patient_id=request.patient_id or "unknown",
        timestamp=request.timestamp or datetime.utcnow().isoformat(),
        probability=result["probability"],
        prediction=result["prediction"],
        alert_level=result["alert_level"],
        confidence=result["confidence"],
        processing_ms=result["processing_ms"],
        model_version="1.0.0",
    )


@router.post("/batch", response_model=BatchPredictionResponse)
async def predict_batch(request: BatchEEGRequest):
    if not inference.is_ready():
        raise HTTPException(status_code=503, detail="Model not loaded.")

    if not request.windows:
        raise HTTPException(status_code=422, detail="No windows provided.")

    results = []
    counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}

    for i, window in enumerate(request.windows):
        try:
            r = inference.predict_window(window)
            counts[r["alert_level"]] += 1
            results.append(PredictionResponse(
                patient_id=request.patient_id or "unknown",
                timestamp=datetime.utcnow().isoformat(),
                probability=r["probability"],
                prediction=r["prediction"],
                alert_level=r["alert_level"],
                confidence=r["confidence"],
                processing_ms=r["processing_ms"],
                model_version="1.0.0",
            ))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed on window {i}: {e}")

    return BatchPredictionResponse(
        patient_id=request.patient_id or "unknown",
        n_windows=len(results),
        predictions=results,
        summary=counts,
    )


@router.post("/upload", response_model=FileUploadPredictionResponse)
async def upload_dataset_file(
    file: Optional[UploadFile] = File(None),
    patient_id: Optional[str] = Form("CHB01"),
    max_windows: Optional[int] = Form(30),
):
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file attached.")

    if not inference.is_ready():
        raise HTTPException(status_code=503, detail="Model not loaded.")

    try:
        content = await file.read()
        windows, meta = parse_uploaded_dataset(
            file_bytes=content,
            filename=file.filename or "recording.edf",
            max_windows=max_windows or 30,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse uploaded file: {e}")

    if not windows:
        raise HTTPException(status_code=422, detail="No valid windows extracted.")

    results: List[PredictionResponse] = []
    counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    probs = []

    for i, win in enumerate(windows):
        try:
            r = inference.predict_window(win.tolist())
            counts[r["alert_level"]] += 1
            probs.append(r["probability"])
            results.append(PredictionResponse(
                patient_id=patient_id or "CHB01",
                timestamp=datetime.utcnow().isoformat(),
                probability=r["probability"],
                prediction=r["prediction"],
                alert_level=r["alert_level"],
                confidence=r["confidence"],
                processing_ms=r["processing_ms"],
                model_version="1.0.0",
            ))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Inference error on window {i}: {e}")

    avg_prob = float(sum(probs) / len(probs)) if probs else 0.0
    if avg_prob >= 0.75:
        overall_risk = "HIGH"
    elif avg_prob >= 0.50:
        overall_risk = "MEDIUM"
    else:
        overall_risk = "LOW"

    sample_wave = windows[0].tolist() if len(windows) > 0 else None

    return FileUploadPredictionResponse(
        filename=meta["filename"],
        format=meta["format"],
        patient_id=patient_id or "CHB01",
        sampling_rate=meta["sampling_rate"],
        total_duration_sec=meta["total_duration_sec"],
        total_windows=meta["total_windows"],
        summary=counts,
        overall_risk=overall_risk,
        average_probability=round(avg_prob, 4),
        predictions=results,
        sample_waveform=sample_wave,
        channels=meta.get("channels", CANONICAL_CHANNELS),
    )


@router.get("/sample-datasets", response_model=List[SampleDatasetItem])
async def list_sample_datasets():
    return [
        SampleDatasetItem(
            id="chb01_preictal",
            name="CHB-MIT Subject 01 (Pre-Ictal Period)",
            description="Pre-seizure recording interval.",
            patient_id="CHB01",
            format="EEG 18-ch (256 Hz)",
            duration_sec=20.0,
            expected_state="PRE-ICTAL",
        ),
        SampleDatasetItem(
            id="chb01_interictal",
            name="CHB-MIT Subject 01 (Inter-Ictal Baseline)",
            description="Inter-seizure baseline recording interval.",
            patient_id="CHB01",
            format="EEG 18-ch (256 Hz)",
            duration_sec=20.0,
            expected_state="INTER-ICTAL",
        ),
    ]


@router.post("/sample-datasets/{sample_id}/run", response_model=FileUploadPredictionResponse)
async def run_sample_dataset(sample_id: str, patient_id: Optional[str] = "CHB01"):
    if not inference.is_ready():
        raise HTTPException(status_code=503, detail="Model not loaded.")

    state = "preictal" if "preictal" in sample_id.lower() else "interictal"
    windows = generate_sample_eeg(state=state, n_windows=4)

    results = []
    counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    probs = []

    for i, win in enumerate(windows):
        r = inference.predict_window(win.tolist())
        counts[r["alert_level"]] += 1
        probs.append(r["probability"])
        results.append(PredictionResponse(
            patient_id=patient_id or "CHB01",
            timestamp=datetime.utcnow().isoformat(),
            probability=r["probability"],
            prediction=r["prediction"],
            alert_level=r["alert_level"],
            confidence=r["confidence"],
            processing_ms=r["processing_ms"],
            model_version="1.0.0",
        ))

    avg_prob = float(sum(probs) / len(probs)) if probs else 0.0
    overall_risk = "HIGH" if avg_prob >= 0.75 else ("MEDIUM" if avg_prob >= 0.50 else "LOW")

    return FileUploadPredictionResponse(
        filename=f"{sample_id}.edf",
        format="edf",
        patient_id=patient_id or "CHB01",
        sampling_rate=256,
        total_duration_sec=len(windows) * 5.0,
        total_windows=len(windows),
        summary=counts,
        overall_risk=overall_risk,
        average_probability=round(avg_prob, 4),
        predictions=results,
        sample_waveform=windows[0].tolist(),
        channels=CANONICAL_CHANNELS,
    )
