import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models import Asset, Tag, Reading
from schemas import CanonicalReadingRequest

logger = logging.getLogger(__name__)


def _normalize_key(value: str) -> str:
    return value.strip()


def _get_or_create_asset(db: Session, asset_code: str) -> Asset:
    asset_code = _normalize_key(asset_code)

    asset = db.query(Asset).filter(Asset.code == asset_code).first()
    if asset:
        return asset

    asset = Asset(
        code=asset_code,
        name=f"Auto-created asset {asset_code}",
        assettype="auto",
    )
    db.add(asset)
    db.flush()
    logger.info("Auto-created asset code=%s id=%s", asset.code, asset.id)
    return asset


def _get_or_create_tag(db: Session, asset: Asset, canonical: CanonicalReadingRequest) -> Tag:
    tag_code = _normalize_key(canonical.tagid)

    tag = db.query(Tag).filter(Tag.code == tag_code).first()
    if tag:
        return tag

    tag = Tag(
        code=tag_code,
        assetid=asset.id,
        name=canonical.tagname,
        datatype=canonical.datatype.value if hasattr(canonical.datatype, "value") else str(canonical.datatype),
        unit=canonical.unit,
    )
    db.add(tag)
    db.flush()
    logger.info("Auto-created tag code=%s id=%s assetid=%s", tag.code, tag.id, tag.assetid)
    return tag


def _compute_final_value(tag: Tag, canonical: CanonicalReadingRequest) -> Optional[float]:
    if canonical.value is not None:
        return float(canonical.value)

    if canonical.valueraw is not None:
        scale = float(tag.scale or 1.0)
        offset = float(tag.offset or 0.0)
        return float(canonical.valueraw) * scale + offset

    return None


def ingest_reading(db: Session, canonical: CanonicalReadingRequest) -> Optional[Reading]:
    """
    Ingest one canonical reading.

    Important mapping:
    - canonical.tagid: external tag code from PLC/canonical payload
    - Tag.code: external tag code in DB
    - Tag.id: internal DB UUID primary key
    - Reading.tagid: foreign key to Tag.id

    This keeps DB primary keys stable and internal, while allowing external systems
    to send business identifiers.
    """
    canonical.assetid = _normalize_key(canonical.assetid)
    canonical.tagid = _normalize_key(canonical.tagid)

    logger.info(
        "Ingest start asset_code=%s tag_code=%s timestamp=%s sequence=%s",
        canonical.assetid,
        canonical.tagid,
        canonical.timestamp,
        canonical.sequence,
    )

    try:
        asset = _get_or_create_asset(db, canonical.assetid)
        tag = _get_or_create_tag(db, asset, canonical)

        # Optional safety: if tag already exists but belongs to a different asset,
        # fail fast instead of silently reassigning.
        if str(tag.assetid) != str(asset.id):
            raise ValueError(
                f"Tag code '{tag.code}' already exists but belongs to assetid={tag.assetid}, "
                f"not assetid={asset.id}"
            )

        last_reading = (
            db.query(Reading)
            .filter(Reading.tagid == tag.id)
            .order_by(Reading.sequence.desc())
            .first()
        )

        if (
            last_reading is not None
            and last_reading.sequence is not None
            and canonical.sequence <= last_reading.sequence
        ):
            logger.warning(
                "Out-of-order reading skipped tag_code=%s tag_id=%s current_sequence=%s last_sequence=%s",
                tag.code,
                tag.id,
                canonical.sequence,
                last_reading.sequence,
            )
            return None

        existing = (
            db.query(Reading)
            .filter(Reading.tagid == tag.id, Reading.time == canonical.timestamp)
            .first()
        )
        if existing is not None:
            logger.warning(
                "Duplicate reading skipped tag_code=%s tag_id=%s time=%s",
                tag.code,
                tag.id,
                canonical.timestamp,
            )
            return None

        final_value = _compute_final_value(tag, canonical)

        reading = Reading(
            tagid=tag.id,
            time=canonical.timestamp,
            valuenumeric=final_value,
            valuetext=None,
            valueraw=canonical.valueraw,
            quality=canonical.quality.value if hasattr(canonical.quality, "value") else str(canonical.quality),
            source=canonical.source,
            sequence=canonical.sequence,
            metadata=canonical.metadata or {},
        )

        db.add(reading)
        db.commit()
        db.refresh(reading)

        logger.info(
            "Reading ingested successfully external_tag_code=%s db_tag_id=%s reading_time=%s value=%s",
            tag.code,
            tag.id,
            reading.time,
            reading.valuenumeric,
        )
        return reading

    except Exception:
        db.rollback()
        logger.exception(
            "Ingestion failed asset_code=%s tag_code=%s timestamp=%s",
            canonical.assetid,
            canonical.tagid,
            canonical.timestamp,
        )
        raise


def ingest_readings_batch(db: Session, readings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Ingest a batch of canonical readings.

    Returns a result summary. One bad message does not stop the whole batch.
    """
    results: Dict[str, Any] = {
        "success": 0,
        "failed": 0,
        "errors": [],
    }

    for msg in readings:
        try:
            canonical = CanonicalReadingRequest(**msg)
            reading = ingest_reading(db, canonical)
            if reading is not None:
                results["success"] += 1
        except Exception as exc:
            results["failed"] += 1
            results["errors"].append(
                {
                    "tagid": msg.get("tagid"),
                    "timestamp": msg.get("timestamp"),
                    "error": str(exc),
                }
            )

    return results