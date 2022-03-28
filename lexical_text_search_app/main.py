from lexical_text_search_api import *
from fastapi import FastAPI

lexical_text_search = LexicalTextSearchAPI()
app = lexical_text_search.app
