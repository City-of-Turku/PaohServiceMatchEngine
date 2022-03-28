from nlp_vectorizer_api import *
from fastapi import FastAPI

nlpvec = NlpVectorizerAPI()
app = nlpvec.app
