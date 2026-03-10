"""
Patient history endpoints.
GET /api/patients/history  — fetch all past inferences.
GET /api/patients/{id}     — fetch a single inference record.
GET /api/patients/stats    — dashboard stats.
"""

from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from app.core.security import get_current_user
from app.core.database import get_database

router = APIRouter(prefix="/api/patients", tags=["Patients"])


def _serialize(doc: dict) -> dict:
    """Convert Mongo document for JSON serialization."""
    doc["_id"] = str(doc["_id"])
    if "created_at" in doc:
        doc["created_at"] = doc["created_at"].isoformat()
    return doc


@router.get("/history")
async def get_history(
    skip: int = 0,
    limit: int = 50,
    search: str = "",
    current_user: dict = Depends(get_current_user),
):
    db = get_database()
    query = {}
    if search:
        query["$or"] = [
            {"patient_name": {"$regex": search, "$options": "i"}},
            {"patient_id": {"$regex": search, "$options": "i"}},
            {"classification": {"$regex": search, "$options": "i"}},
        ]

    cursor = (
        db["inferences"]
        .find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    records = [_serialize(doc) async for doc in cursor]
    total = await db["inferences"].count_documents(query)

    return {"total": total, "records": records}


@router.get("/stats")
async def get_stats(current_user: dict = Depends(get_current_user)):
    db = get_database()
    total = await db["inferences"].count_documents({})
    benign = await db["inferences"].count_documents({"classification": "Benign"})
    malignant = total - benign

    cursor = db["inferences"].find().sort("created_at", -1).limit(5)
    recent = []
    async for doc in cursor:
        recent.append(
            {
                "id": str(doc["_id"]),
                "patient_name": doc.get("patient_name", ""),
                "classification": doc["classification"],
                "confidence": doc["confidence"],
                "created_at": doc["created_at"].isoformat()
                if "created_at" in doc
                else "",
            }
        )

    return {
        "total_scans": total,
        "benign_count": benign,
        "malignant_count": malignant,
        "recent_scans": recent,
    }


@router.get("/{record_id}")
async def get_record(
    record_id: str,
    current_user: dict = Depends(get_current_user),
):
    db = get_database()
    try:
        doc = await db["inferences"].find_one({"_id": ObjectId(record_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid record ID format")

    if not doc:
        raise HTTPException(status_code=404, detail="Record not found")

    return _serialize(doc)
