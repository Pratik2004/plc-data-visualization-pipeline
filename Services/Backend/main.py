from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi.middleware.cors import CORSMiddleware
from db import get_db
from models import Asset
from schemas import BulkReadingsRequest
from ingestion import ingest_readings_batch

app = FastAPI(
    title="PLC Data Pipeline API",
    version="1.0.0",
    description="Local-first PLC data ingestion and visualization",
)

# CORS is required so the React UI can call the API from another port later.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "PLC Data Pipeline API v1.0"}

@app.get("/health")
def health():
    return {"status": "ok", "service": "backend"}

@app.post("/test-asset")
def create_test_asset(db: Session = Depends(get_db)):
    """Test endpoint: create an asset."""
    import uuid
    unique_code = f"TEST_{uuid.uuid4().hex[:8].upper()}"
    new_asset = Asset(
        code=unique_code,
        name="Test Asset",
        assettype="test"
    )
    db.add(new_asset)
    db.commit()
    db.refresh(new_asset)
    return {"id": str(new_asset.id), "code": new_asset.code}

@app.post("/api/v1/bulk-readings")
def post_bulk_readings(req: BulkReadingsRequest, db: Session = Depends(get_db)):
    print("DEBUG full request =", req.model_dump())

    for item in req.readings:
        print("DEBUG incoming tagid =", item.tagid)
        print("DEBUG incoming value =", item.value)
        print("DEBUG incoming valueraw =", item.valueraw)
        print("DEBUG incoming sequence =", item.sequence)
    results = ingest_readings_batch(db, [r.model_dump() for r in req.readings])

    return {
        "status": "success" if results["failed"] == 0 else "partial",
        "data": results,
    }


@app.get("/test-assets")
def list_test_assets(db: Session = Depends(get_db)):
    """Test endpoint: list assets."""
    assets = db.query(Asset).all()
    return [{"id": str(a.id), "code": a.code, "name": a.name} for a in assets]

@app.get("/api/v1/tags/{tagid}/latest")
def gettaglatest(tagid: str, db: Session = Depends(get_db)):
    from models import Taglatest, Tag

    latest = db.query(Taglatest).filter(Taglatest.tagid == tagid).first()

    if not latest:
        return {"status": "error", "message": "No data for this tag"}

    tag = db.query(Tag).filter(Tag.id == tagid).first()

    return {
        "status": "success",
        "data": {
            "tagid": str(latest.tagid),
            "tagname": tag.name if tag else "Unknown",
            "unit": tag.unit if tag else "",
            "currentvalue": latest.valuenumeric,
            "quality": latest.quality,
            "lastupdated": latest.updatedat.isoformat() if latest.updatedat else None,
            "source": latest.source,
            "time": latest.time.isoformat() if latest.time else None
        }
    }