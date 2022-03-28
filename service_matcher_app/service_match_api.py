import os
import time
from starlette.responses import Response
from starlette.status import HTTP_200_OK
from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List
from service_matcher.service_matcher import ServiceMatcher
from service_matcher.models import *


class ServiceMatchAPI():
    """
    A class used to provide an API for bot and frontend to fetch data and recommendation from

    Args
    ----------
    service_matcher : ServiceMatcher (default None)
        Matcher class which handles the actual logic of recommendations


    Methods
    -------
    get_all_services()
        Get all services from the database

    get_all_services_filtered( serviceQuery: Optional[ServiceQuery] )
        Get all services filtered with conditions
        
    get_service( service_id: str )
        Get a service with ID
        
    get_all_service_channels()
        Get all service channels from the database
    
    get_service_channels_by_service_id( service_id: str )
        Gt all service channels of given service ID
    
    get_service_classes()
        Get all service classes existing in the data

    get_service_intent_recommendations( serviceRecommendIntentQuery: ServiceRecommendIntentQuery )
        Get service recommendations based on intent name

    get_service_intent_and_options_recommendations( serviceRecommendIntentAndOptionsQuery: ServiceRecommendIntentAndOptionsQuery )
        Get service recommendations based on intent name and options attached to intent in the database
    
    get_service_recommendations_by_conversation( conversation_id: str, serviceRecommendConversationQuery: Optional[ServiceRecommendConversationQuery] )
        Get service recommendations based on conversation
    
    get_service_recommendations( serviceRecommendQuery: ServiceRecommendQuery )
        Get service recommendations based on free text
    
    get_service_class_recommendations_by_conversation( conversation_id: str, serviceClassRecommendConversationQuery: ServiceClassRecommendConversationQuery )
        Get service class recommendations based on conversation
    
    get_service_class_recommendations( serviceClassRecommendQuery: ServiceClassRecommendQuery )
        Get service class recommendations based on free text

    """

    def __init__(self, service_matcher: Optional[ServiceMatcher] = None) -> None:
        self.app = FastAPI(
            title="Service Matcher API",
            description="API docs for the Service Matcher",
            version="1.0",
            redoc_url=None,
            root_path=os.environ.get("FAST_API_ROOT_PATH")
        )
        if service_matcher is None:
            self.service_matcher = ServiceMatcher()
        else:
            self.service_matcher = service_matcher

        @self.app.get("/",
                      tags=["Health"],
                      summary="Health check",
                      description="Check if this service is live and usable",
                      status_code=200)
        def health_check() -> None:
            return Response(status_code=200)
        
        @self.app.get("/syncVectors",
                      tags=["Synchronize"],
                      summary="Synchronize service matcher vectors",
                      description="An endpoint for processor to synchronize vectors in memory",
                      status_code=200)
        def sync_desc_vectors() -> None:
            self.service_matcher.update_desc_vectors()
            return Response(status_code=200)

        @self.app.get("/services",
                      tags=["Data"],
                      summary="Get all services",
                      description="Get all services and all info related to them from the database, optionally translate missing texts of service names and descriptions")
        def get_all_services(translate_missing_texts: bool = False) -> list:
            return self.service_matcher.get_all_services(translate_missing_texts = translate_missing_texts)
        
        @self.app.post("/servicesFiltered",
                      tags=["Data"],
                      summary="Get all services filtered by service classes, municipalities or life events")
        def get_all_services_filtered(serviceQuery: Optional[ServiceQuery] = ServiceQuery()) -> list:
            """
            ServiceQuery has the following fields:
            
            - **include_channels**: Include service channel data related to service or not
            - **municipalities**: Limit to municipalities given in a list of municipality names
            - **life_events**: Limit to life event codes given in a list
            - **service_classes**: Limit to service class codes given in a list
            - **limit_k**: Maximum number of services to give
            - **priorization**: With class search prioritize national or local, default local
            - **translate_missing_texts**: Show machine translations of services' English and Swedish texts if actual translations are missing', default False
            """
            return self.service_matcher.get_all_services_filtered(serviceQuery)

        @self.app.get("/services/{service_id}",
                      tags=["Data"],
                      summary="Get a service by ID",
                      description="Get a service and all info related to it by service ID, optionally translate missing texts of service names and descriptions")
        def get_service(service_id: str, translate_missing_texts: bool = False) -> Service:        
            service = self.service_matcher.get_service(service_id = service_id, translate_missing_texts = translate_missing_texts)
            if service is None:
                raise HTTPException(
                    status_code=404, detail="Service not found")
            else:
                return service

        @self.app.get("/serviceChannels",
                      tags=["Data"],
                      summary="Get all service channels",
                      description="Get all service channels and all info related to them from the database")
        def get_all_service_channels() -> list:
            return self.service_matcher.get_all_service_channels()

        @self.app.get("/serviceChannels/{service_id}",
                      tags=["Data"],
                      summary="Get a service channels by service ID",
                      description="Get service channels and all info related to it by service ID")
        def get_service_channels_by_service_id(service_id: str) -> list:
            channels = self.service_matcher.get_service_channels_by_service_id(service_id)
            if channels is None:
                raise HTTPException(
                    status_code=404, detail="Service not found")
            else:
                return channels
            
        @self.app.get("/serviceClasses",
                      tags=["Data"],
                      summary="Get all service classes",
                      description="Get all service classes and all info related to them from the database")
        def get_service_classes() -> list:
            return self.service_matcher.get_all_service_classes()

        @self.app.post("/services/recommendByConversation/{conversation_id}", tags=["Service recommendations"],
                      summary="Get service recommendations by conversation")
        def get_service_recommendations_by_conversation(conversation_id: str, serviceRecommendConversationQuery: Optional[ServiceRecommendConversationQuery] = ServiceRecommendConversationQuery()) -> list:
            """
            Path parameters:
            - **conversation_id**: ID of conversation               
                
            ServiceRecommendConversationQuery has the following fields:

            - **mode**: The strategy how to recommend, accepts values search, intent, conversation and infer. Search does a free text search based on search_text type field from slots, conversation uses the whole conversation history as text search, intent uses latest intents to find services, infer tries to infer current state and uses one of the 3 earlier methodsbased on state.
            - **municipalities**: Limit to municipalities given in a list of municipality names
            - **life_events**: Limit to life event codes given in a list
            - **service_classes**: Limit to service class codes given in a list
            - **top_k**: Number of recommendations
            - **score_threshold**: Only return results with higher or equal match score to the threshold
            - **text_recommender**: The strategy for free text search, accepts values all, nlp, lexical. All uses all available strategies combined, nlp uses only NPL semantic search, and lexical only uses classical lexical text search
            - **language**: The language of the free text search text
            - **translate_missing_texts**: Show machine translations of services' English and Swedish texts if actual translations are missing', default False
            """
            return self.service_matcher.get_service_recommendations_by_conversation(conversation_id, serviceRecommendConversationQuery)

        @self.app.post("/services/recommendByIntent", tags=["Service recommendations"],
                      summary="Get service recommendations by intent name")
        def get_service_intent_recommendations(serviceRecommendIntentQuery: ServiceRecommendIntentQuery) -> list:
            """
            ServiceRecommendIntentQuery has the following fields:
                
            - **intent**: Intent name    
            - **municipalities**: Limit to municipalities given in a list of municipality names
            - **life_events**: Limit to life event codes given in a list
            - **service_classes**: Limit to service class codes given in a list
            - **translate_missing_texts**: Show machine translations of services' English and Swedish texts if actual translations are missing', default False
            """
            return self.service_matcher.get_service_recommendations_by_intent(serviceRecommendIntentQuery)

        @self.app.post("/services/recommendByIntentAndOptions", tags=["Service recommendations"],
                      summary="Get service recommendations by intent name and options defined to the intent in the database")
        def get_service_intent_and_options_recommendations(serviceRecommendIntentAndOptionsQuery: ServiceRecommendIntentAndOptionsQuery) -> list:
            """
            ServiceRecommendIntentAndOptionsQuery has the following fields:
                
            - **intent**: Intent name    
            - **municipalities**: Limit to municipalities given in a list of municipality names
            - **life_events**: Limit to life event codes given in a list
            - **service_classes**: Limit to service class codes given in a list, overwrite db definition with this
            - **limit_k**: Max number of recommendations given by text search in addition to intent recommendations
            - **score_threshold**: Only return additional text results with higher or equal match score to the threshold
            - **need_text**: Free text to use for text recomendation, overwrite db definition with this
            - **text_recommender**: The strategy for free text search, accepts values all, nlp, lexical. All uses all available strategies combined, nlp uses only NPL semantic search, and lexical only uses classical lexical text search
            - **language**: The language of the free text search text
            - **priorization**: With class search prioritize national or local, default local
            - **translate_missing_texts**: Show machine translations of services' English and Swedish texts if actual translations are missing', default False
            """
            return self.service_matcher.get_service_recommendations_by_intent_and_options(serviceRecommendIntentAndOptionsQuery)

        @self.app.post("/services/recommend", tags=["Service recommendations"],
                      summary="Get service recommendations by conversation by text query")
        def get_service_recommendations(serviceRecommendQuery: ServiceRecommendQuery) -> list:
            """
            ServiceRecommendQuery has the following fields:
                
            - **need_text**: Free text query      
            - **municipalities**: Limit to municipalities given in a list of municipality names
            - **life_events**: Limit to life event codes given in a list
            - **service_classes**: Limit to service class codes given in a list
            - **top_k**: Number of recommendations
            - **score_threshold**: Only return results with higher or equal match score to the threshold
            - **text_recommender**: The strategy for free text search, accepts values all, nlp, lexical. All uses all available strategies combined, nlp uses only NPL semantic search, and lexical only uses classical lexical text search
            - **language**: The language of the need text
            - **translate_missing_texts**: Show machine translations of services' English and Swedish texts if actual translations are missing', default False
            """
            return self.service_matcher.get_service_recommendations(serviceRecommendQuery)

        @self.app.post("/serviceClasses/recommendByConversation/{conversation_id}", tags=["Service class recommendations"],
                      summary="Get service class recommendations by conversation")
        def get_service_class_recommendations_by_conversation(conversation_id: str, serviceClassRecommendConversationQuery: ServiceClassRecommendConversationQuery) -> list:
            """
            Path parameters:
            - **conversation_id**: ID of conversation               
                
            ServiceClassRecommendConversationQuery has the following fields:
        
            - **top_k**: Number of recommendations
            """
            return self.service_matcher.get_service_class_recommendations_by_conversation(conversation_id, serviceClassRecommendConversationQuery)

        @self.app.post("/serviceClasses/recommend", tags=["Service class recommendations"],
                      summary="Get service class recommendations by conversation by text query")
        def get_service_class_recommendations(serviceClassRecommendQuery: ServiceClassRecommendQuery) -> list:
            """
            ServiceClassRecommendQuery has the following fields:
        
            - **need_text**: Free text search
            - **top_k**: Number of recommendations
            """
            return self.service_matcher.get_service_class_recommendations(serviceClassRecommendQuery)

            
