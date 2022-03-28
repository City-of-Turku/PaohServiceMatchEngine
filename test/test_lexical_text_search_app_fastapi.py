import os
import sys
sys.path.append('lexical_text_search_app')
import json
import unittest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from lexical_text_search_app.lexical_text_search import *
from lexical_text_search_app.lexical_text_search.db import LexicalTextSearchDB
from lexical_text_search_app.lexical_text_search.lexical_text_search import LexicalTextSearch
from lexical_text_search_app.lexical_text_search_api import LexicalTextSearchAPI
import nest_asyncio
import numpy as np
nest_asyncio.apply()


class FastAPITest(unittest.TestCase):
    
    def setUp(self):
        with open('test/example_service_data.json') as json_file:
            test_service_data = json.load(json_file)        

        mongo_client_instance = MagicMock()
        mongo_client_instance.service_db = MagicMock()
        mongo_client_instance.service_db.services = MagicMock()
        mongo_client_instance.service_db.services.find = MagicMock()
        mongo_client_instance.service_db.services.find.return_value = test_service_data
        
        mongo_client_instance.service_db.translations = MagicMock()
        mongo_client_instance.service_db.translations.find = MagicMock()
        mongo_client_instance.service_db.translations.find.return_value = []

        db = LexicalTextSearchDB(mongo_client_instance)
    
        self.lexical_text_search = LexicalTextSearch(db=db)
        self.lexical_text_search.db = db
        self.lexical_text_search_api = LexicalTextSearchAPI(self.lexical_text_search)

        self.test_client = TestClient(self.lexical_text_search_api.app)

    def test_health_check(self):
        response = self.test_client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_create_ngrams(self):
        text1 = "Text to ngramize"
        ngrams1 = self.lexical_text_search._create_ngrams(text1, 3, 3)
        self.assertEqual(len(ngrams1), 14)
        text2 = "Onelongwordwithoutspaces"
        ngrams2 = self.lexical_text_search._create_ngrams(text2, 4, 5)
        self.assertEqual(len(ngrams2), 41)

    def test_clean_text(self):
        text1 = "Text with point."
        cleant_text1 = self.lexical_text_search._clean_text(text1)
        self.assertEqual(cleant_text1, "text with point")
        text2 = "Text with comma, some more text"
        cleant_text2 = self.lexical_text_search._clean_text(text2)
        self.assertEqual(cleant_text2, "text with comma some more text")
        text3 = "Vuokra-asunnot"
        cleant_text3 = self.lexical_text_search._clean_text(text3)
        self.assertEqual(cleant_text3, "vuokra asunnot")
        text4 = "2 €"
        cleant_text4 = self.lexical_text_search._clean_text(text4)
        self.assertEqual(cleant_text4, "2 €")

    def test_tokenize_text(self):
        text1 = "Text to ngramize"
        tokens1 = self.lexical_text_search._tokenize_text(text1, 'en')
        self.assertEqual(len(tokens1), 12)
        text2 = "Word Word"
        tokens2 = self.lexical_text_search._tokenize_text(text2, 'en')
        self.assertEqual(len(tokens2), 4)
        text3 = "Word word"
        tokens3 = self.lexical_text_search._tokenize_text(text3, 'en')
        self.assertEqual(len(tokens3), 4)
        text4 = ""
        tokens4 = self.lexical_text_search._tokenize_text(text4, 'en')
        self.assertEqual(len(tokens4), 0)
        text5 = "and to for from"
        tokens5 = self.lexical_text_search._tokenize_text(text5, 'en')
        self.assertEqual(len(tokens5), 0)
        tokens6 = self.lexical_text_search._tokenize_text(text5, 'fi')
        self.assertEqual(len(tokens6), 4)

    def test_lexical_text_search_services(self):
        response = self.test_client.post("/searchServices", json={"text": "Jotain", "language":"fi" ,"top_k": 0})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["services"]), 2)
        self.assertTrue(response.json()["services"][0]["score"] is not None)

        response2 = self.test_client.post("/searchServices", json={"text": "Jotain", "language":"fi", "top_k": 1})
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(len(response2.json()["services"]), 1)
        
if __name__ == '__main__':
    unittest.main()
