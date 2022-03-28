from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List
from fastapi import Query


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
    nameAutoTranslated: dict

class ServiceClass(BaseModel):
    """
    A class for single service class

    """
    name: str
    code: str

class ServiceChannel(BaseModel):
    """
    A class for single service channel

    """
    id: str
    ptvId: Optional[str] = None
    type: Optional[str] = None
    areaType: Optional[str] = None
    organizationId: Optional[str] = None
    serviceIds: list
    name: dict
    descriptions: dict
    webPages: dict
    emails: dict
    phoneNumbers: dict
    areas: dict
    addresses: dict
    channelUrls: dict
    lastUpdated: datetime
    
class ServiceQuery(BaseModel):
    """
    A class for request payoad for service filtering

    """
    include_channels: Optional[bool] = False
    priorization: Optional[str] = Query("local", regex="^(local|national)$")
    municipalities: Optional[List[str]] = []
    life_events: Optional[List[str]] = []
    service_classes: Optional[List[str]] = []
    limit_k: Optional[int] = 20
    translate_missing_texts: Optional[bool] = False
   
class ServiceRecommendQuery(BaseModel):
    """
    A class for payload for free text service recommendation

    """
    need_text: str
    municipalities: Optional[List[str]] = []
    life_events: Optional[List[str]] = []
    service_classes: Optional[List[str]] = []
    top_k: Optional[int] = 20
    score_threshold: Optional[float] = 0.0
    text_recommender: Optional[str] = Query("all", regex="^(nlp|lexical|all)$")
    language: Optional[str] = Query("fi", regex="^(fi|en|sv)$")
    translate_missing_texts: Optional[bool] = False

class ServiceRecommendConversationQuery(BaseModel):
    """
    A class for payload for service recommendation based on conversation

    """
    mode: Optional[str] = Query("infer", regex="^(search|intent|conversation|infer)$")              
    municipalities: Optional[List[str]] = []
    life_events: Optional[List[str]] = []
    service_classes: Optional[List[str]] = []
    top_k: Optional[int] = 20
    score_threshold: Optional[float] = 0.0
    text_recommender: Optional[str] = Query("all", regex="^(nlp|lexical|all)$")
    language: Optional[str] = Query("fi", regex="^(fi|en|sv)$")
    translate_missing_texts: Optional[bool] = False
    
class ServiceRecommendIntentQuery(BaseModel):
    """
    A class for payload for intent based service recommendation

    """
    intent: str
    municipalities: Optional[List[str]] = []
    life_events: Optional[List[str]] = []
    service_classes: Optional[List[str]] = []
    translate_missing_texts: Optional[bool] = False

class ServiceRecommendIntentAndOptionsQuery(BaseModel):
    """
    A class for payload for intent and options based service recommendation, options can be got from database or can be overwritten in the interface

    """
    intent: str
    municipalities: Optional[List[str]] = []
    life_events: Optional[List[str]] = []
    service_classes: Optional[List[str]] = []
    score_threshold: Optional[float] = 0.0
    need_text: Optional[str] = None
    text_recommender: Optional[str] = Query("all", regex="^(nlp|lexical|all)$")
    language: Optional[str] = Query("fi", regex="^(fi|en|sv)$")
    priorization: Optional[str] = Query("local", regex="^(local|national)$")
    limit_k: Optional[int] = 20
    translate_missing_texts: Optional[bool] = False

class ServiceClassRecommendQuery(BaseModel):
    """
    A class for payload for free text service class recommendation

    """
    need_text: str
    top_k: Optional[int] = 20

class ServiceClassRecommendConversationQuery(BaseModel):
    """
    A class for payload for service class recommendation based on conversation

    """
    top_k: Optional[int] = 20
