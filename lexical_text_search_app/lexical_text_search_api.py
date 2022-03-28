from starlette.responses import Response
from starlette.status import HTTP_200_OK
from typing import Optional
from fastapi import FastAPI, HTTPException
from lexical_text_search.lexical_text_search import LexicalTextSearch
from lexical_text_search.models import *


class LexicalTextSearchAPI():
    """A class for Lexical Text Search providing needed API endpoints with FastAPI.


    Args
    ----------
    lexical_text_search : LexicalTextSearch (default None)
        LexicalTextSearch object


    FastAPI endpoints
    -------
    searchServices(ServiceSearchQuery: ServiceSearchQuery)
        Returns list of found services

    """

    def __init__(self, lexical_text_search: Optional[LexicalTextSearch] = None) -> None:
        self.app = FastAPI(
            title="Lexical Text Search API",
            description="API docs for the Lexical Text Search service",
            version="1.0",
            redoc_url=None
        )
        if lexical_text_search is None:
            self.lexical_text_search = LexicalTextSearch()
        else:
            self.lexical_text_search = lexical_text_search

        @self.app.get("/",
                      tags=["Health"],
                      summary="Health check",
                      description="Check if this service is live and usable",
                      status_code=200)
        def health_check() -> None:
            return Response(status_code=200)

        @self.app.get("/syncServices",
                      tags=["Synchronize"],
                      summary="Synchronize Lexical text search services",
                      description="An endpoint for processor to synchronize services in memory")
        def sync_services() -> None:
            return self.lexical_text_search.update_services()

        @self.app.post("/createBM25", tags=["Create BM25 model"],
                       summary="Create BM25 model",
                       description="An endpoint for configuring BM25 model parameters if wanted to change the defaults used at the startup. This method is automatically called at the startup with default values so it is not neccessary to rerun it.")
        def create_bm25(CreateBM25: CreateBM25) -> list:
            """
            CreateBM25 has the following fields:

            - **ngram_min**: Min number of ngrams for each supported language (fi, en, sv). Set to 0 to disable ngrams and only use whole words for BM25.
            - **ngram_max**: Max number of ngrams for each supported language (fi, en, sv). Set to 0 to disable ngrams and only use whole words for BM25.
            - **bm25_k1**: Float number for BM25 k1 parameter     
            - **bm25_b**: Float number for BM25 b parameter 

            """
            return self.lexical_text_search.create_bm25(CreateBM25)

        @self.app.post("/searchServices", tags=["Service search"],
                       summary="Get services by text query")
        def search_services(serviceSearchQuery: ServiceSearchQuery) -> list:
            """
            ServiceSearchQuery has the following fields:

            - **text**: Free text query
            - **language**: Language of the text 
            - **top_k**: Number of recommendations. Set to 0 to get all services.
            """
            return self.lexical_text_search.search_services(serviceSearchQuery)
