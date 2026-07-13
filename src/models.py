from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field

EdgeRelation = Literal["supports", "depends_on"]
ClaimStatus = Literal["draft", "reviewed"]
SourceType = Literal["rct", "meta_analysis", "cohort", "review", "guideline", "news", "other"]


class Claim(BaseModel):
    id: str
    case: str
    text: str
    label: str
    explanation: Optional[str] = None
    status: ClaimStatus = "draft"
    tags: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    confidence: Optional[float] = None
    author: str
    created: date


class Edge(BaseModel):
    id: str
    relation: EdgeRelation
    from_: str = Field(alias="from")
    to: str
    provenance: list[str] = Field(default_factory=list)
    author: str
    created: date

    model_config = {"populate_by_name": True}


class Source(BaseModel):
    id: str
    type: SourceType
    title: str
    authors: str
    year: int
    venue: Optional[str] = None
    url: Optional[str] = None
