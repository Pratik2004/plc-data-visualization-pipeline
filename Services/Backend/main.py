from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_
from fastapi.middleware.cors import CORSMiddleware
from db import get_db
from models import Reading, Tag, Asset
from schemas import BulkReadingsRequest
from ingestion import ingest_readings_batch
from typing import Optional
from datetime import datetime

def parse_iso_datetime(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {value}")
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

@app.get("/api/v1/readings")
def get_readings(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    pagesize: int = Query(50, ge=1, le=1000),
    sortby: str = Query("time"),
    sortorder: str = Query("DESC"),
    tagids: Optional[str] = Query(None),
    assetids: Optional[str] = Query(None),
    quality: Optional[str] = Query(None),
    fromtime: Optional[str] = Query(None),
    totime: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    sort_columns = {
        "time": Reading.time,
        "valuenumeric": Reading.valuenumeric,
        "quality": Reading.quality,
    }

    if sortby not in sort_columns:
        raise HTTPException(status_code=400, detail=f"Invalid sortby: {sortby}")

    if sortorder.upper() not in {"ASC", "DESC"}:
        raise HTTPException(status_code=400, detail=f"Invalid sortorder: {sortorder}")
    
    query = (
        db.query(
            Reading.id.label("reading_id"),
            Reading.tagid.label("tag_id"),
            Reading.time,
            Reading.valuenumeric,
            Reading.quality,
            Reading.source,
            Tag.code.label("tag_code"),
            Tag.name.label("tag_name"),
            Tag.unit.label("tag_unit"),
            Asset.id.label("asset_id"),
            Asset.code.label("asset_code"),
            Asset.name.label("asset_name"),
        )
        .join(Tag, Reading.tagid == Tag.id)
        .join(Asset, Tag.assetid == Asset.id)
    )

    if tagids:
        tagid_list = [item.strip() for item in tagids.split(",") if item.strip()]
        query = query.filter(Reading.tagid.in_(tagid_list))

    if assetids:
        assetid_list = [item.strip() for item in assetids.split(",") if item.strip()]
        query = query.filter(Tag.assetid.in_(assetid_list))

    if quality:
        quality_list = [item.strip().upper() for item in quality.split(",") if item.strip()]
        query = query.filter(Reading.quality.in_(quality_list))

    if fromtime:
        from_dt = parse_iso_datetime(fromtime)
        query = query.filter(Reading.time >= from_dt)

    if totime:
        to_dt = parse_iso_datetime(totime)
        query = query.filter(Reading.time <= to_dt)

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Tag.code.ilike(search_term),
                Tag.name.ilike(search_term),
                Asset.code.ilike(search_term),
                Asset.name.ilike(search_term),
            )
        )
    totalcount = query.count()
    sort_column = sort_columns[sortby]

    if sortorder.upper() == "ASC":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())   

    offset = (page - 1) * pagesize
    rows = query.offset(offset).limit(pagesize).all() 
    totalpages = (totalcount + pagesize - 1) // pagesize

    readings_data = [
        {
            "id": row.reading_id,
            "tag": {
                "id": str(row.tag_id),
                "code": row.tag_code,
                "name": row.tag_name,
                "unit": row.tag_unit,
            },
            "asset": {
                "id": str(row.asset_id),
                "code": row.asset_code,
                "name": row.asset_name,
            },
            "time": row.time.isoformat() if row.time else None,
            "value": float(row.valuenumeric) if row.valuenumeric is not None else None,
            "quality": row.quality,
            "source": row.source,
        }
        for row in rows
    ]

    return {
        "status": "success",
        "data": {
            "totalcount": totalcount,
            "page": page,
            "pagesize": pagesize,
            "totalpages": totalpages,
            "readings": readings_data,
        },
    }