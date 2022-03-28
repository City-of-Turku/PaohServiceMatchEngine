from starlette.responses import Response
from starlette.status import HTTP_200_OK
from typing import Optional
from fastapi import FastAPI, HTTPException
from nlp_vectorizer.nlp_vectorizer import NlpVectorizer
from nlp_vectorizer.models import *


class NlpVectorizerAPI():
    """A class for NLP Vectorizer providing needed API endpoints with FastAPI.


    Args
    ----------
    nlp_vectorizer : NlpVectorizer (default None)
        NlpVectorizer object


    FastAPI endpoints
    -------
    vectorize(VectorizeQuery: VectorizeQuery)
        Returns vectorized text as a list

    """

    def __init__(self, nlp_vectorizer: Optional[NlpVectorizer] = None) -> None:
        self.app = FastAPI(
            title="NLP Vectorizer API",
            description="API docs for the NLP text vectorizer",
            version="1.0",
            redoc_url=None
        )
        if nlp_vectorizer is None:
            self.nlp_vectorizer = NlpVectorizer()
        else:
            self.nlp_vectorizer = nlp_vectorizer

        @self.app.get("/",
                      tags=["Health"],
                      summary="Health check",
                      description="Check if this service is live and usable",
                      status_code=200)
        def health_check() -> None:
            return Response(status_code=200)

        @self.app.post("/vectorize")
        def vectorize(vectorizeQuery: VectorizeQuery) -> VectorResponse:
            return self.nlp_vectorizer.vectorize(vectorizeQuery)

