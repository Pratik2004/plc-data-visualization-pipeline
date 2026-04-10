from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class QualityEnum(str, Enum):
    GOOD = "GOOD"
    UNCERTAIN = "UNCERTAIN"
    BAD = "BAD"

class DataTypeEnum(str, Enum):
    FLOAT = "FLOAT"
    INT32 = "INT32"
    BOOLEAN = "BOOLEAN"
    STRING = "STRING"

class CanonicalReadingRequest(BaseModel):
    timestamp: datetime
    tagid: str = Field(...)
    assetid: str
    tagname: str
    value: Optional[float] = None
    valueraw: Optional[int] = None
    unit: str
    datatype: DataTypeEnum
    quality: QualityEnum
    source: str
    sequence: int
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BulkReadingsRequest(BaseModel):
    readings: List[CanonicalReadingRequest]
