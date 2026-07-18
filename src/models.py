from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field

EdgeRelation = Literal["supports", "depends_on"]
ClaimStatus = Literal["draft", "reviewed"]
SourceType = Literal["rct", "meta_analysis", "cohort", "review", "guideline", "news", "other"]
SourceFunding = Literal["industry", "independent", "government", "mixed", "unknown"]


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
    funding: SourceFunding
    bias_note: Optional[str] = None


class Case(BaseModel):
    """Case-level metadata -- currently just the neutral question the case
    explores. Deliberately separate from the root claims themselves: a root
    is one side's *answer* ("Eggs are healthy"), not the shared *question*
    both sides are answering ("What are the health impacts of eggs as a
    human food source?") -- the latter can't be mechanically derived from
    the former, so unlike hierarchy/cruxes/coverage this is authored, not
    computed."""

    question: str
