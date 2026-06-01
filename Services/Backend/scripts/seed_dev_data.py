from datetime import datetime, timedelta, timezone
import math
import random
import uuid
import os

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from models import Asset, Tag, Reading

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASEURL environment variable is not set")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_or_create_asset(session, code, name, location, asset_type, plcid):
    existing = session.execute(
        select(Asset).where(Asset.code == code)
    ).scalar_one_or_none()

    if existing:
        return existing

    asset = Asset(
        code=code,
        name=name,
        location=location,
        assettype=asset_type,
        plcid=plcid,
        description=f"{name} seeded for PLC demo data",
        isactive=True,
        metadata={}
    )
    session.add(asset)
    session.flush()
    return asset


def get_or_create_tag(
    session,
    asset,
    code,
    name,
    unit,
    datatype,
    scale,
    offset,
    sourcepath,
    sourcetype,
    minvalue,
    maxvalue,
    aggregationmethod="AVERAGE"
):
    existing = session.execute(
        select(Tag).where(Tag.code == code)
    ).scalar_one_or_none()

    if existing:
        return existing

    tag = Tag(
        assetid=asset.id,
        code=code,
        name=name,
        unit=unit,
        datatype=datatype,
        scale=scale,
        offset=offset,
        sourcepath=sourcepath,
        sourcetype=sourcetype,
        minvalue=minvalue,
        maxvalue=maxvalue,
        aggregationmethod=aggregationmethod,
        isactive=True,
        metadata={}
    )
    session.add(tag)
    session.flush()
    return tag


def quality_for_index(i):
    if i % 173 == 0:
        return "BAD"
    if i % 37 == 0:
        return "UNCERTAIN"
    return "GOOD"


def clamp(value, low, high):
    return max(low, min(high, value))


def make_signal(tag_code, i, minutes_from_start):
    t = minutes_from_start

    if "MOTOR01_SPEED" in tag_code:
        base = 1480 + 40 * math.sin(t / 18) + random.uniform(-8, 8)
        raw = int(base / 0.05)
        return base, raw

    if "MOTOR01_CURRENT" in tag_code:
        base = 32 + 4 * math.sin(t / 14) + random.uniform(-1.2, 1.2)
        raw = int(base / 0.01)
        return base, raw

    if "MOTOR01_TEMP" in tag_code:
        base = 68 + 6 * math.sin(t / 55) + (t / 1200) + random.uniform(-0.4, 0.4)
        raw = int(base / 0.1)
        return base, raw

    if "PUMP01_FLOW" in tag_code:
        base = 96 + 12 * math.sin(t / 20) + random.uniform(-2, 2)
        raw = int(base / 0.1)
        return base, raw

    if "PUMP01_PRESSURE" in tag_code:
        base = 5.8 + 0.5 * math.sin(t / 25) + random.uniform(-0.08, 0.08)
        raw = int(base / 0.01)
        return base, raw

    if "PUMP01_VIBRATION" in tag_code:
        base = 1.8 + 0.35 * abs(math.sin(t / 10)) + random.uniform(-0.05, 0.05)
        raw = int(base / 0.001)
        return base, raw

    if "TANK01_LEVEL" in tag_code:
        cycle = (t % 360) / 360
        base = 45 + 25 * math.sin(cycle * 2 * math.pi) + random.uniform(-0.7, 0.7)
        raw = int(base / 0.1)
        return base, raw

    if "TANK01_TEMP" in tag_code:
        base = 29 + 2.5 * math.sin(t / 80) + random.uniform(-0.2, 0.2)
        raw = int(base / 0.1)
        return base, raw

    if "TANK01_PH" in tag_code:
        base = 7.1 + 0.15 * math.sin(t / 45) + random.uniform(-0.03, 0.03)
        raw = int(base / 0.01)
        return base, raw

    return 0.0, 0


def seed():
    session = SessionLocal()
    try:
        asset_motor = get_or_create_asset(
            session, "MOTOR01", "Primary Motor", "Line A", "motor", "PLC001"
        )
        asset_pump = get_or_create_asset(
            session, "PUMP01", "Circulation Pump", "Line B", "pump", "PLC001"
        )
        asset_tank = get_or_create_asset(
            session, "TANK01", "Mixing Tank", "Area C", "tank", "PLC002"
        )

        tags = [
            get_or_create_tag(session, asset_motor, "MOTOR01_SPEED", "Motor Speed", "rpm", "FLOAT", 0.05, 0.0, "ns=2;s=Motor01.Speed", "OPCUA", 0, 3000),
            get_or_create_tag(session, asset_motor, "MOTOR01_CURRENT", "Motor Current", "A", "FLOAT", 0.01, 0.0, "ns=2;s=Motor01.Current", "OPCUA", 0, 100),
            get_or_create_tag(session, asset_motor, "MOTOR01_TEMP", "Bearing Temperature", "C", "FLOAT", 0.1, 0.0, "ns=2;s=Motor01.Temp", "OPCUA", 0, 150),

            get_or_create_tag(session, asset_pump, "PUMP01_FLOW", "Pump Flow Rate", "m3/h", "FLOAT", 0.1, 0.0, "ns=2;s=Pump01.Flow", "OPCUA", 0, 200),
            get_or_create_tag(session, asset_pump, "PUMP01_PRESSURE", "Pump Discharge Pressure", "bar", "FLOAT", 0.01, 0.0, "ns=2;s=Pump01.Pressure", "OPCUA", 0, 20),
            get_or_create_tag(session, asset_pump, "PUMP01_VIBRATION", "Pump Vibration", "mm/s", "FLOAT", 0.001, 0.0, "ns=2;s=Pump01.Vibration", "OPCUA", 0, 20),

            get_or_create_tag(session, asset_tank, "TANK01_LEVEL", "Tank Level", "%", "FLOAT", 0.1, 0.0, "ns=2;s=Tank01.Level", "OPCUA", 0, 100),
            get_or_create_tag(session, asset_tank, "TANK01_TEMP", "Tank Temperature", "C", "FLOAT", 0.1, 0.0, "ns=2;s=Tank01.Temp", "OPCUA", 0, 100),
            get_or_create_tag(session, asset_tank, "TANK01_PH", "Tank pH", "pH", "FLOAT", 0.01, 0.0, "ns=2;s=Tank01.pH", "OPCUA", 0, 14),
        ]

        session.commit()

        end_time = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        start_time = end_time - timedelta(hours=24)
        interval = timedelta(minutes=1)

        reading_rows = []
        sequence_map = {str(tag.id): 1 for tag in tags}

        current_time = start_time
        i = 0
        while current_time <= end_time:
            minutes_from_start = int((current_time - start_time).total_seconds() // 60)

            for tag in tags:
                value, raw = make_signal(tag.code, i, minutes_from_start)
                value = clamp(value, float(tag.minvalue or value), float(tag.maxvalue or value))
                quality = quality_for_index(i)

                reading = Reading(
                    tagid=tag.id,
                    time=current_time,
                    valuenumeric=None if tag.datatype == "STRING" else float(value),
                    valuetext=None,
                    valueraw=raw,
                    quality=quality,
                    source="plcprimary",
                    sequence=sequence_map[str(tag.id)],
                    metadata={
                        "seeded": True,
                        "asset_code": next(
                            a.code for a in [asset_motor, asset_pump, asset_tank] if a.id == tag.assetid
                        ),
                        "tag_code": tag.code,
                        "scale_applied": True,
                        "generator": "seed_sync.py"
                    }
                )
                reading_rows.append(reading)
                sequence_map[str(tag.id)] += 1

            if len(reading_rows) >= 5000:
                session.bulk_save_objects(reading_rows)
                session.commit()
                print(f"Inserted {len(reading_rows)} readings batch ending at {current_time.isoformat()}")
                reading_rows = []

            current_time += interval
            i += 1

        if reading_rows:
            session.bulk_save_objects(reading_rows)
            session.commit()
            print(f"Inserted final batch of {len(reading_rows)} readings")

        total_assets = session.execute(select(Asset)).scalars().all()
        total_tags = session.execute(select(Tag)).scalars().all()
        total_readings = session.execute(select(Reading)).scalars().all()

        print(f"Assets: {len(total_assets)}")
        print(f"Tags: {len(total_tags)}")
        print(f"Readings: {len(total_readings)}")
        print("Seed completed successfully.")

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()