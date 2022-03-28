import os
import sys
sys.path.append('service_matcher_app')
import json
import unittest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from service_matcher_app.service_matcher import *
from service_matcher_app.service_matcher.service_matcher import ServiceMatcher
from service_matcher_app.service_match_api import ServiceMatchAPI
import nest_asyncio
nest_asyncio.apply()


NLP_VECTORIZER_JSON_RESPONSE_SUCCESS = {"vector": [123, 123, 123, 123]}
LEXICAL_TEXT_SEARCH_JSON_RESPONSE_SUCCESS = {"services": [{"id": "C1", "score": 0.2 }, {"id": "C2", "score": 0.1 } ]}
JSON_RESPONSE_ERROR = {
    "detail": [
        {
            "loc": [
                "body",
                48
            ],
            "msg": "Expecting value: line 4 column 1 (char 48)",
            "type": "value_error.jsondecode",
            "ctx": {
                    "msg": "Expecting value",
                    "doc": "{\n  \"text\": \"string\"}",
                    "pos": 48,
                    "lineno": 4,
                    "colno": 1
            }
        }
    ]
}

# This method will be used by the mock to replace requests.post to NLP vectorizer API
def mocked_requests_post(*args, **kwargs):

    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

        def text(self):
            return json.dumps(self.json_data)

    if args[0] == 'request_success/vectorize':
        return MockResponse(NLP_VECTORIZER_JSON_RESPONSE_SUCCESS, 200)
    elif args[0] == 'request_error/vectorizerecommend':
        return MockResponse(JSON_RESPONSE_ERROR, 400)
    if args[0] == 'request_success/searchServices':
        return MockResponse(LEXICAL_TEXT_SEARCH_JSON_RESPONSE_SUCCESS, 200)
    elif args[0] == 'request_error/searchServices':
        return MockResponse(JSON_RESPONSE_ERROR, 400)

class FastAPITest(unittest.TestCase):
    
    def setUp(self):
        with open('test/example_service_data.json') as json_file:
            self.test_service_data = json.load(json_file)
        with open('test/example_service_channel_data.json') as json_file:
            self.test_service_channel_data = json.load(json_file)
        self.mongo_client_instance = MagicMock()
        self.mongo_client_instance.service_db = MagicMock()
        self.mongo_client_instance.service_db.services = MagicMock()
        self.mongo_client_instance.service_db.services.find = MagicMock()
        self.mongo_client_instance.service_db.services.find.return_value = self.test_service_data
        self.mongo_client_instance.service_db.classifications = MagicMock()
        self.mongo_client_instance.service_db.classifications.find = MagicMock()
        self.mongo_client_instance.service_db.classifications.find.return_value = [{"id": self.test_service_data[0]["id"], "service_class_codes": ["P20.1"], "municipality_codes": ["853"], "life_event_codes": ["KE6"]}]
        self.mongo_client_instance.service_db.service_vectors = MagicMock()
        self.mongo_client_instance.service_db.service_vectors.find = MagicMock()
        self.mongo_client_instance.service_db.service_vectors.find.return_value = [{"id": self.test_service_data[0]["id"], "vector": [111, 111, 111, 111], "service_class_codes": ["P20.1"], "municipality_codes": ["853"], "life_event_codes": ["KE6"]}]
        self.mongo_client_instance.service_db.service_class_vectors = MagicMock()
        self.mongo_client_instance.service_db.service_class_vectors.find = MagicMock()
        self.mongo_client_instance.service_db.service_class_vectors.find.return_value = [{"code": "P1", "vector": [111, 111, 111, 111], "name": "TESTI LUOKKA"}, {"code": "P20.1", "vector": [111, 111, 111, 111], "name": "TESTI LUOKKA"}, {"code": "P11.2", "vector": [111, 111, 111, 111], "name": "TESTI LUOKKA"}, {"code": "P19", "vector": [111, 111, 111, 111], "name": "TESTI LUOKKA"}]
        self.mongo_client_instance.service_db.channels = MagicMock()
        self.mongo_client_instance.service_db.channels.find = MagicMock()
        self.mongo_client_instance.service_db.channels.find.return_value = self.test_service_channel_data
        self.mongo_client_instance.service_db.municipalities = MagicMock()
        self.mongo_client_instance.service_db.municipalities.find = MagicMock()
        self.mongo_client_instance.service_db.municipalities.find.return_value = [{"id": "853", "name": {"fi": "Turku", "en": "Turku", "sv": "Åbo"}}]
        
        self.conversation_id = "C1"
        self.conversation_id2 = "C1"
        self.mongo_client_instance.bf = MagicMock()
        self.mongo_client_instance.bf.activity = MagicMock()
        self.mongo_client_instance.bf.conversations = MagicMock()
        self.mongo_client_instance.bf.core_policies = MagicMock()
        self.mongo_client_instance.bf.activity.find = MagicMock()
        self.mongo_client_instance.bf.conversations.find = MagicMock()
        self.mongo_client_instance.bf.core_policies.find = MagicMock()
        self.mongo_client_instance.bf.activity.find.return_value = [{"text": "Tekstiä"}, {"text": "Toinen teksti"}]
        self.mongo_client_instance.bf.conversations.find.side_effect = [[{"_id": self.conversation_id, "intents": ["p1_greet"], "tracker": {"slots": {"municipality": "Turku"}, "events": [{"parse_data":{"intent": {"name":"p1_greet"}}}]}}],
                                                                        [{"_id": self.conversation_id2, "intents": ["ke6_something"], "tracker": {"slots": {"municipality": "Turku"}, "events": [{"parse_data":{"intent": {"name":"ke6_something"}}}]}}],
                                                                        [{"_id": self.conversation_id2, "intents": ["ke6_xyz"], "tracker": {"slots": {"municipality": "Turku"}, "events": [{"parse_data":{"intent": {"name":"ke6_xyz"}}}]}}],
                                                                        [{"_id": self.conversation_id2, "intents": ["service_search"], "tracker": {"slots": {"municipality": "Turku"}, "events":[{"parse_data": {"intent": {"name":"service_search"}}}, {"event": "action", "name": "service_search_form"}] }}], #Tässä ongelma
                                                                        [{"_id": self.conversation_id2, "intents": ["service_search"], "tracker": {"slots": {"municipality": "Turku", "service_search_text": ""}, "events":[{"parse_data":{"intent": {"name":"service_search"}}}, {"event": "action", "name": "service_search_form"}] }}],
                                                                        [{"_id": self.conversation_id2, "intents": ["service_search"], "tracker": {"slots": {"municipality": "Turku", "service_search_text": "Some free text"}, "events":[{"parse_data":{"intent": {"name":"service_search"}}}, {"event": "action", "name": "service_search_form"},{"event": "active_loop", "name":"service_search_form"}] }}],
                                                                        [{"_id": self.conversation_id2, "intents": ["service_search"], "tracker": {"slots": {"municipality": "Turku", "service_search_text": "Some free text"}, "events":[{"parse_data":{"intent": {"name":"service_search"}}}, {"event": "action", "name": "service_search_form"},{"event": "active_loop", "name":"service_search_form"}] }}],
                                                                        [{"_id": self.conversation_id2, "intents": ["service_search"], "tracker": {"slots": {"service_search_text": "Some free text"}, "events":[{"event": "reset_slots"}, {"parse_data":{"intent": {"name":"service_search"}}}, {"event": "action", "name": "service_search_form"},{"event": "active_loop", "name":"service_search_form"}, {"event": "active_loop", "name": None}] }}],
                                                                        [{"_id": self.conversation_id2, "intents": ["service_search"], "tracker": {"slots": {"service_search_text": "Some free text"}, "events":[{"parse_data":{"intent": {"name":"service_search"}}}, {"event": "action", "name": "service_search_form"},{"event": "active_loop", "name":"service_search_form"}, {"parse_data":{"intent": {"name":"p20.1_any_intent_to_reject_excecution"}}}, {"event": "action_execution_rejected", "name": "service_search_form"}] }}],
                                                                        [{"_id": self.conversation_id2, "intents": ["service_search"], "tracker": {"slots": {"service_search_text": "Some free text"}, "events":[{"parse_data":{"intent": {"name":"service_search"}}}, {"event": "action", "name": "service_search_form"},{"event": "active_loop", "name":"service_search_form"}, {"parse_data":{"intent": {"name":"p20.1_any_intent_to_reject_excecution"}}}, {"event": "action_execution_rejecte" }] }}],
                                                                        [{"_id": self.conversation_id2, "intents": ["sports_service_search"], "tracker": {"slots": {"library_service_search_text": "Some free text"}, "events":[{"parse_data":{"intent": {"name":"sports_service_search"}}}, {"event": "action", "name": "sports_service_search_form"},{"event": "active_loop", "name":"sports_service_search_form"}] }}],
                                                                        [{"_id": self.conversation_id2, "intents": ["sports_service_search"], "tracker": {"slots": {"sports_service_search_text": "Some free text"}, "events":[{"parse_data":{"intent": {"name":"sports_service_search"}}}, {"event": "action", "name": "sports_service_search_form"},{"event": "active_loop", "name":"sports_service_search_form"}] }}],
                                                                        [{"_id": self.conversation_id2, "intents": ["sports_service_search"], "tracker": {"slots": {"sports_service_search_text": "Some free text"}, "events":[{"event": "reset_slots"}, {"parse_data":{"intent": {"name":"sports_service_search"}}}, {"event": "action", "name": "sports_service_search_form"},{"event": "active_loop", "name":"sports_service_search_form"}, {"event": "active_loop", "name": None}] }}],
                                                                        [{"_id": self.conversation_id2, "intents": ["sports_service_search"], "tracker": {"slots": {"sports_service_search_text": "Some free text"}, "events":[{"parse_data":{"intent": {"name":"sports_service_search"}}}, {"event": "action", "name": "sports_service_search_form"},{"event": "active_loop", "name":"sports_service_search_form"}, {"parse_data":{"intent": {"name":"p20.1_any_intent_to_reject_excecution"}}}, {"event": "action_execution_rejected", "name": "sports_service_search_form"}] }}],
                                                                        [{"_id": self.conversation_id2, "intents": ["sports_service_search", "ke6_something"], "tracker": {"slots": {"sports_service_search_text": "Some free text"}, "events":[{"parse_data":{"intent": {"name":"sports_service_search"}}}, {"event": "action", "name": "sports_service_search_form"},{"event": "active_loop", "name":"sports_service_search_form"}, {"parse_data":{"intent": {"name":"p20.1_any_intent_to_reject_excecution"}}}, {"event": "action_execution_rejected", "name": "sports_service_search_form"}, {"parse_data":{"intent": {"name":"ke6_something"}}}] }}],
                                                                        [{"_id": self.conversation_id2, "intents": ["sports_service_search", "ke6_something"], "tracker": {"slots": {"sports_service_search_text": "Some free text"}, "events":[{"parse_data":{"intent": {"name":"sports_service_search"}}}, {"event": "action", "name": "sports_service_search_form"},{"event": "active_loop", "name":"sports_service_search_form"}, {"parse_data":{"intent": {"name":"ke6_something"}}}, {"event": "action_execution_rejected", "name": "sports_service_search_form"}] }}],
                                                                        [{"_id": self.conversation_id2, "intents": ["ke6_something", "service_search"], "tracker": {"slots": {"sports_service_search_text": "Some free text"}, "events":[{"parse_data":{"intent": {"name":"ke6_something"}}}, {"parse_data":{"intent": {"name":"sports_service_search"}}}, {"event": "action", "name": "sports_service_search_form"},{"event": "active_loop", "name":"sports_service_search_form"}, {"parse_data":{"intent": {"name":"p20.1_any_intent_to_reject_excecution"}}}, {"event": "action_execution_rejected", "name": "sports_service_search_form"}] }}],
                                                                        [{"_id": self.conversation_id2, "intents": ["ke6_something", "service_search"], "tracker": {"slots": {"sports_service_search_text": "Some free text"}, "events":[{"parse_data":{"intent": {"name":"ke6_something"}}}, {"parse_data":{"intent": {"name":"sports_service_search"}}}, {"event": "action", "name": "sports_service_search_form"},{"event": "active_loop", "name":"sports_service_search_form"}, {"parse_data":{"intent": {"name":"p19_something"}}}, {"event": "action_execution_rejected", "name": "sports_service_search_form"}] }}]]
        self.mongo_client_instance.bf.core_policies.find.return_value = [{"policies": "policies:\n  - name: TEDPolicy\n    epochs: 10\n    max_history: 8\n  - name: RulePolicy\n  - name: AugmentedMemoizationPolicy\n  - name: rasa_addons.core.policies.BotfrontDisambiguationPolicy\n    fallback_trigger: 0.40\n    disambiguation_trigger: '$0 < 2 * $1'\n    n_suggestions: 2 # default value\n    excluded_intents:\n      - ^chitchat\\..*\n      - feedback_positive\n      - feedback_negative\n      - yes\n      - no"}]
        self.mongo_client_instance.service_db.intent_to_services = MagicMock()
        self.mongo_client_instance.service_db.intent_to_services.find = MagicMock()
        self.mongo_client_instance.service_db.intent_to_services.find.return_value = [{"intent": "p1_greet", "services": [self.test_service_data[0]["id"]]}, {"intent": "ke6_something", "services": [self.test_service_data[0]["id"]]}, {"intent": "ke7_something", "services": [self.test_service_data[0]["id"]], "intent_text": "Intentiä kuvaava teksti", "intent_service_classes": ["P20.1"]}]
        self.mongo_client_instance.service_db.translations = MagicMock()
        self.mongo_client_instance.service_db.translations.find = MagicMock()
        self.mongo_client_instance.service_db.translations.find.return_value = [{"source_language":"fi", "target_language":"en", "source_text": "Ampumarata", "target_text": "Shooting range"}, {"source_language":"fi", "target_language":"en", "source_text": "Ampumaradalla tarkoitetaan sisällä olevaa tilaa tai ulkona olevaa aluetta, joka on ampuma-aseella maaliin ampumista varten.\n\nVähäisellä ampumaradalla tarkoitetaan ampumarataa, jolla on tarkoitettu ammuttavaksi enintään 10 000 laukausta vuodessa.\n\nLuvan ampumaradan perustamiseen ja ylläpitämiseen antaa ja peruuttaa Poliisihallitus. Myös ampumaratailmoitus tehdään Poliisihallitukselle.", "target_text": "Desc Translation"}, {"source_language":"fi", "target_language":"en", "source_text": "Ampumaradan perustaminen ja ylläpitäminen on luvanvaraista. Vähäisestä ampumaradasta on tehtävä ampumaratailmoitus.", "target_text": "Summ Translation"}]
        
        self.service_matcher = ServiceMatcher(self.mongo_client_instance)
        self.service_match_api = ServiceMatchAPI(self.service_matcher)

        self.test_client = TestClient(self.service_match_api.app)

    def test_health_check(self):
        response = self.test_client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_get_all_services(self):
        response = self.test_client.get("/services")
        self.assertEqual(response.status_code, 200)
        
    @patch('requests.post', side_effect=mocked_requests_post)
    def test_get_all_services_filtered(self, mock_post):
        response = self.test_client.post("/servicesFiltered", json = {"service_classes": []})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        
        response = self.test_client.post("/servicesFiltered")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        
    def test_get_existing_service(self):
        response = self.test_client.get(f"/services/{self.test_service_data[0]['id']}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], self.test_service_data[0]['id'])

    def test_get_nonexisting_service(self):
        response = self.test_client.get("/services/1000")
        self.assertEqual(response.status_code, 404)
        
    def test_get_all_service_channels(self):
        response = self.test_client.get("/serviceChannels")
        self.assertEqual(response.status_code, 200)

    def test_get_service_channels_by_service_id(self):
        response = self.test_client.get(f"/serviceChannels/{self.test_service_channel_data[0]['serviceIds'][0]}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.test_service_channel_data[0]['serviceIds'][0], response.json()[0]['serviceIds'])

    def test_get_all_service_classes(self):
        response = self.test_client.get("/serviceClasses")
        self.assertEqual(response.status_code, 200)    
      
    @patch('requests.post', side_effect=mocked_requests_post)
    def test_get_service_recommendations_by_conversation(self, mock_post):
        response = self.test_client.post(f"/services/recommendByConversation/{self.conversation_id}", json = {"mode": "infer"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['service']['id'], self.test_service_data[0]['id'])
        
        response = self.test_client.post(f"/services/recommendByConversation/{self.conversation_id2}", json = {"mode": "infer"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['service']['id'], self.test_service_data[0]['id'])
        
        response = self.test_client.post(f"/services/recommendByConversation/{self.conversation_id2}", json = {"mode": "infer"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

        response = self.test_client.post(f"/services/recommendByConversation/{self.conversation_id2}", json = {"mode": "infer"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

        response = self.test_client.post(f"/services/recommendByConversation/{self.conversation_id2}", json = {"mode": "infer"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)
        
        response = self.test_client.post(f"/services/recommendByConversation/{self.conversation_id2}", json = {"mode": "infer"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['service']['id'], self.test_service_data[0]['id'])

        response = self.test_client.post(f"/services/recommendByConversation/{self.conversation_id2}", json = {"mode": "infer"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['service']['id'], self.test_service_data[0]['id'])
        
        response = self.test_client.post(f"/services/recommendByConversation/{self.conversation_id2}", json = {"mode": "infer"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['service']['id'], self.test_service_data[0]['id'])
        
        response = self.test_client.post(f"/services/recommendByConversation/{self.conversation_id2}", json = {"mode": "infer"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['service']['id'], self.test_service_data[0]['id'])
        
        response = self.test_client.post(f"/services/recommendByConversation/{self.conversation_id2}", json = {"mode": "infer"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['service']['id'], self.test_service_data[0]['id'])

        response = self.test_client.post(f"/services/recommendByConversation/{self.conversation_id2}", json = {"mode": "infer"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)
        
        response = self.test_client.post(f"/services/recommendByConversation/{self.conversation_id2}", json = {"mode": "infer"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['service']['id'], self.test_service_data[0]['id'])

        response = self.test_client.post(f"/services/recommendByConversation/{self.conversation_id2}", json = {"mode": "infer"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['service']['id'], self.test_service_data[0]['id'])

        response = self.test_client.post(f"/services/recommendByConversation/{self.conversation_id2}", json = {"mode": "infer"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['service']['id'], self.test_service_data[0]['id'])
        
        response = self.test_client.post(f"/services/recommendByConversation/{self.conversation_id2}", json = {"mode": "infer"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['service']['id'], self.test_service_data[0]['id'])
        
        response = self.test_client.post(f"/services/recommendByConversation/{self.conversation_id2}", json = {"mode": "infer"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['service']['id'], self.test_service_data[0]['id'])
        
        response = self.test_client.post(f"/services/recommendByConversation/{self.conversation_id2}", json = {"mode": "infer"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['service']['id'], self.test_service_data[0]['id'])
        
        response = self.test_client.post(f"/services/recommendByConversation/{self.conversation_id2}", json = {"mode": "infer"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

    @patch('requests.post', side_effect=mocked_requests_post)
    def test_recommend_services_by_conversation(self, mock_post):
        os.environ['NLP_VECTORIZER_HOST'] = 'request_success'
        response = self.test_client.post("/services/recommendByIntent", json={"intent": "p1_greet"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]['service']['id'], self.test_service_data[0]['id'])
        
        response = self.test_client.post("/services/recommendByIntent", json={"intent": "ke6_something"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]['service']['id'], self.test_service_data[0]['id'])

        response = self.test_client.post("/services/recommendByIntent", json={"intent": "p2_greet"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)
        
        response = self.test_client.post("/services/recommendByIntent", json={"intent": "p1_greet", "municipalities": ['Turku']})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]['service']['id'], self.test_service_data[0]['id'])
        
        response = self.test_client.post("/services/recommendByIntent", json={"intent": "p1_greet", "municipalities": ['Naantali']})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)
        
    @patch('requests.post', side_effect=mocked_requests_post)
    def test_recommend_services(self, mock_post):
        os.environ['NLP_VECTORIZER_HOST'] = 'request_success'
        response = self.test_client.post("/services/recommend", json={"need_text": "Jotain", "municipalities": ['Turku']})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]['service']['id'], self.test_service_data[0]['id'])
       
    @patch('requests.post', side_effect=mocked_requests_post)
    def test_recommend_service_classes(self, mock_post):
        os.environ['NLP_VECTORIZER_HOST'] = 'request_success'
        response = self.test_client.post("/serviceClasses/recommend", json={"need_text": "Jotain"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]['service_class_code'], "P1")
        

    @patch('requests.post', side_effect=mocked_requests_post)
    def test_recommend_service_classes_by_conversation(self, mock_post):
        os.environ['NLP_VECTORIZER_HOST'] = 'request_success'
        response = self.test_client.post("/serviceClasses/recommendByConversation/{self.conversation_id}", json={})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]['service_class_code'], "P1")

if __name__ == '__main__':
    unittest.main()
