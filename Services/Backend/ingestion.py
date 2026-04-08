import logging
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session

from models import Asset, Tag, Reading
from schemas import CanonicalReadingRequest

logger = logging.getLogger(__name__)

def ingest_reading(db: Session, canonical: CanonicalReadingRequest) -> Optional[Reading]:
    # Find or create asset
    asset = db.query(Asset).filter(Asset.code == canonical.assetid).first()
    if not asset:
        asset = Asset(
            code=canonical.assetid,
            name=f"Auto-created asset {canonical.assetid}",
            assettype="auto"
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)

    # Find or create tag
    tag = db.query(Tag).filter(Tag.code == canonical.tagid).first()
    if not tag:
        tag = Tag(
            code=canonical.tagid,
            assetid=asset.id,
            name=canonical.tagname,
            datatype=canonical.datatype.value,
            unit=canonical.unit
        )
        db.add(tag)
        db.commit()
        db.refresh(tag)

    last_reading = (
        db.query(Reading)
        .filter(Reading.tagid == tag.id)
        .order_by(Reading.sequence.desc())
        .first()
    )

    if last_reading and canonical.sequence <= last_reading.sequence:
        logger.warning(
            "Out-of-order reading detected: current sequence %s <= last %s. Skipping.",
            canonical.sequence,
            last_reading.sequence,
        )
        return None

    existing = (
        db.query(Reading)
        .filter(Reading.tagid == tag.id)
        .filter(Reading.time == canonical.timestamp)
        .first()
    )
    if existing:
        logger.warning("Duplicate reading skipped tagid=%s time=%s", canonical.tagid, canonical.timestamp)
        return None

    if canonical.valueraw is not None:
        scaled_value = float(canonical.valueraw) * float(tag.scale or 1.0) + float(tag.offset or 0.0)
    else:
        scaled_value = canonical.value

    reading = Reading(
        tagid=tag.id,
        time=canonical.timestamp,
        valuenumeric=scaled_value,
        valuetext=None,
        valueraw=canonical.valueraw,
        quality=canonical.quality.value,
        source=canonical.source,
        sequence=canonical.sequence,
        metadata=canonical.metadata,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading

def ingest_readings_batch(db: Session, readings: List[Dict[str, Any]]) -> Dict[str, Any]:
    results = {"success": 0, "failed": 0, "errors": []}

    for msg in readings:
        try:
            canonical = CanonicalReadingRequest(**msg)
            reading = ingest_reading(db, canonical)
            if reading is not None:
                results["success"] += 1
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({"tagid": msg.get("tagid"), "error": str(e)})
            db.rollback()

    return results