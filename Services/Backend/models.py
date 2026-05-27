from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Float, DateTime, Boolean, ForeignKey, Text, Index, Column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
#from db import Base

class Base(DeclarativeBase):
    pass


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    assettype: Mapped[str | None] = mapped_column(String(50), nullable=True)
    plcid: Mapped[str | None] = mapped_column(String(100), nullable=True)
    asset_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)

    isactive: Mapped[bool] = mapped_column(Boolean, default=True)
    createdat: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updatedat: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tags: Mapped[list["Tag"]] = relationship(back_populates="asset", cascade="all, delete-orphan")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    assetid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    datatype: Mapped[str | None] = mapped_column(String(50), nullable=True)  # FLOAT, INT32, BOOLEAN, STRING
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)

    scale: Mapped[float] = mapped_column(Float, default=1.0)
    offset: Mapped[float] = mapped_column(Float, default=0.0)

    sourcepath: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sourcetype: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g., MODBUSHOLDING
    sourceaddress: Mapped[int | None] = mapped_column(Integer, nullable=True)

    minvalue: Mapped[float | None] = mapped_column(Float, nullable=True)
    maxvalue: Mapped[float | None] = mapped_column(Float, nullable=True)

    aggregationmethod: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tag_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)

    isactive: Mapped[bool] = mapped_column(Boolean, default=True)
    createdat: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updatedat: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    asset: Mapped["Asset"] = relationship(back_populates="tags")
    readings: Mapped[list["Reading"]] = relationship(back_populates="tag", cascade="all, delete-orphan")

class Reading(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tagid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)
    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    valuenumeric: Mapped[float | None] = mapped_column(Float, nullable=True)
    valuetext: Mapped[str | None] = mapped_column(Text, nullable=True)
    valueraw: Mapped[int | None] = mapped_column(Integer, nullable=True)

    quality: Mapped[str | None] = mapped_column(String(20), nullable=True)   # GOOD/UNCERTAIN/BAD
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)   # plcprimary, etc.
    sequence: Mapped[int | None] = mapped_column(Integer, nullable=True)

    reading_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    tag: Mapped["Tag"] = relationship(back_populates="readings")    
    __table_args__ = (
        Index("idx_readings_tag_time", "tagid", "time", unique=True),
        Index("idx_readings_time", "time"),
    )

class TagLatest(Base):
    __tablename__ = "taglatest"

    tagid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valuenumeric: Mapped[float | None] = mapped_column(Float, nullable=True)
    valuetext: Mapped[str | None] = mapped_column(Text, nullable=True)
    quality: Mapped[str | None] = mapped_column(String(20), nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sequence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updatedat: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

