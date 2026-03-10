"""
Prediction / Upload endpoints.
POST /api/predict/upload — accept a PBS image, run inference, return results.
"""

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from datetime import datetime, timezone

from app.core.security import get_current_user
from app.core.database import get_database
from app.utils.image_processing import validate_image, bytes_to_pil
from app.services.ml_service import run_inference

router = APIRouter(prefix="/api/predict", tags=["Prediction"])


@router.post("/upload")
async def upload_and_predict(
    file: UploadFile = File(...),
    patient_name: str = Form(""),
    patient_id: str = Form(""),
    notes: str = Form(""),
    current_user: dict = Depends(get_current_user),
):
    """
    Accept a multipart/form-data upload of a PBS image.
    Runs AlexNet inference + Grad-CAM, stores results in MongoDB,
    and returns the classification with heatmap.
    """
    file_bytes = await file.read()
    filename = file.filename or "upload.png"

    # ── Validate ─────────────────────────────────────────
    if not validate_image(file_bytes, filename):
        raise HTTPException(
            status_code=400,
            detail="Invalid file. Allowed: jpg, jpeg, png, bmp, tiff (max 10 MB).",
        )

    # ── Inference ────────────────────────────────────────
    pil_img = bytes_to_pil(file_bytes)
    result = run_inference(pil_img)

    # ── Persist to MongoDB ───────────────────────────────
    db = get_database()
    record = {
        "patient_name": patient_name,
        "patient_id": patient_id,
        "image_filename": filename,
        "image_base64": result["image_base64"],
        "heatmap_base64": result["heatmap_base64"],
        "classification": result["classification"],
        "confidence": result["confidence"],
        "all_probabilities": result["all_probabilities"],
        "notes": notes,
        "created_by": current_user["username"],
        "created_at": datetime.now(timezone.utc),
    }
    insert_result = await db["inferences"].insert_one(record)

    return {
        "id": str(insert_result.inserted_id),
        "image_filename": filename,
        "image_base64": result["image_base64"],
        "heatmap_base64": result["heatmap_base64"],
        "classification": result["classification"],
        "confidence": result["confidence"],
        "all_probabilities": result["all_probabilities"],
        "created_at": record["created_at"].isoformat(),
    }
