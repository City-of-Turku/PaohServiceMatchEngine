from pydantic import BaseModel
from fastapi import Query
from typing import Optional
from datetime import datetime


class ServiceSearchResponse(BaseModel):
    services: list


class ServiceSearchQuery(BaseModel):
    text: str
    language: Optional[str] = Query("fi", regex="^(fi|en|sv)$")
    top_k: Optional[int] = 10


class CreateBM25(BaseModel):
    ngram_min: Optional[dict] = {'fi': 4, 'en': 2, 'sv': 1}
    ngram_max: Optional[dict] = {'fi': 4, 'en': 2, 'sv': 2}
    bm25_k1: Optional[float] = 1.5
    bm25_b: Optional[float] = 0.75


class Service(BaseModel):
    """
    A class for single service

    """
    id: str
    ptvId: Optional[str] = None
    type: Optional[str] = None
    subtype: Optional[str] = None
    organizations: list
    name: dict
    descriptions: dict
    requirement: dict
    targetGroups: dict
    serviceClasses: dict
    lifeEvents: dict
    areas: dict
    lastUpdated: datetime
