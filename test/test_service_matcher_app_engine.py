import os
import sys
sys.path.append('service_matcher_app')
import json
import unittest
from unittest.mock import MagicMock, patch
from service_matcher_app.service_matcher import models
from service_matcher_app.service_matcher.service_matcher import ServiceMatcher
import numpy as np


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

class ServiceMatchEngineTest(unittest.TestCase):

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
        self.conversation_id2 = "C2"
        self.mongo_client_instance.bf = MagicMock()
        self.mongo_client_instance.bf.activity = MagicMock()
        self.mongo_client_instance.bf.conversations = MagicMock()
        self.mongo_client_instance.bf.activity.find = MagicMock()
        self.mongo_client_instance.bf.core_policies = MagicMock()
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

    def test_mongo_client(self):
        self.assertTrue(self.service_matcher.db.mongo_client is not None)
        self.assertEqual(len(self.service_matcher.db.mongo_client.service_db.services.find()), 2)

    def test_get_all_services(self):
        self.assertEqual(len(self.service_matcher.get_all_services()), 2)
        self.assertEqual(len(self.service_matcher.get_all_services_filtered(models.ServiceQuery())), 1)

    def test_get_service(self):
        service_1 = self.service_matcher.get_service(self.test_service_data[0]["id"])
        self.assertEqual(service_1.id, self.test_service_data[0]["id"])
        
        service_2 = self.service_matcher.get_service(self.test_service_data[0]["id"], translate_missing_texts=True)
        self.assertEqual(service_2.name["en"], "Shooting range")
        self.assertEqual(len([desc for desc in service_2.descriptions["en"] if desc["type"] == "Description"]), 1)
        self.assertEqual([desc for desc in service_2.descriptions["en"] if desc["type"] == "Description"][0]["value"], "Desc Translation")
        self.assertEqual(len([desc for desc in service_2.descriptions["en"] if desc["type"] == "GD_Description"]), 1)
        self.assertEqual([desc for desc in service_2.descriptions["en"] if desc["type"] == "GD_Description"][0]["value"], "Desc Translation")
        self.assertEqual(len([desc for desc in service_2.descriptions["en"] if desc["type"] == "Summary"]), 1)
        self.assertEqual([desc for desc in service_2.descriptions["en"] if desc["type"] == "Summary"][0]["value"], "Summ Translation")
        self.assertEqual(len([desc for desc in service_2.descriptions["en"] if desc["type"] == "GD_Summary"]), 1)
        self.assertEqual([desc for desc in service_2.descriptions["en"] if desc["type"] == "GD_Summary"][0]["value"], "Summ Translation")
        self.assertEqual(len([desc for desc in service_2.descriptions["en"] if desc["type"] == "UserInstruction"]), 0)
        
        service_3 = self.service_matcher.get_service(self.test_service_data[0]["id"], translate_missing_texts=False)
        self.assertEqual(service_3.name["en"], None)
        self.assertEqual(len(service_3.descriptions["en"]), 0)

    def test_get_all_service_classes(self):
        self.assertEqual(len(self.service_matcher.get_all_service_classes()), 226)

    def test_get_service_desc_vectors(self):
        service_desc_vectors = self.service_matcher.db._get_service_desc_vectors()
        self.assertEqual(len(service_desc_vectors), 1)

    def test_get_service_class_vectors(self):
        service_class_vectors = self.service_matcher.db._get_service_class_vectors()
        self.assertEqual(len(service_class_vectors), 4)

    def test_get_all_service_channels(self):
        self.assertEqual(len(self.service_matcher.get_all_service_channels()), 2)

    def test_get_service_channels_by_service_id(self):
        channels = self.service_matcher.get_service_channels_by_service_id(self.test_service_channel_data[0]['serviceIds'][0])
        self.assertIn(self.test_service_channel_data[0]['serviceIds'][0], channels[0].serviceIds)
        
    def test_filter_service_data_by_municipality(self):
        
        service_1 = self.service_matcher.get_service(self.test_service_data[0]["id"])
        filtered_service = self.service_matcher.utils._filter_service_data_by_municipality(service_1, ["853"])
        self.assertEqual(len(filtered_service.areas['fi']), 1)
        
        filtered_service2 = self.service_matcher.utils._filter_service_data_by_municipality(service_1, ["853", "564"])
        self.assertEqual(len(filtered_service2.areas['fi']), 2)
        
        filtered_service3 = self.service_matcher.utils._filter_service_data_by_municipality(service_1, ["1"])
        self.assertEqual(len(filtered_service3.areas['fi']), 0)
    

    def test_filter_service_channel_data_by_municipality(self):
        
        channels = self.service_matcher.get_service_channels_by_service_id(self.test_service_channel_data[0]['id'])
        
        filtered_channel = self.service_matcher.utils._filter_service_channel_data_by_municipality(channels[0], ["853"])
        self.assertEqual(len(filtered_channel.areas['fi']), 1)
        self.assertEqual(len(filtered_channel.addresses['fi']), 2)

        filtered_channel2 = self.service_matcher.utils._filter_service_channel_data_by_municipality(channels[0], ["853", "564"])
        self.assertEqual(len(filtered_channel2.areas['fi']), 2)
        self.assertEqual(len(filtered_channel2.addresses['fi']), 3)
        
        filtered_channel3 = self.service_matcher.utils._filter_service_channel_data_by_municipality(channels[0], ["1"])
        self.assertEqual(len(filtered_channel3.areas['fi']), 0)
        self.assertEqual(len(filtered_channel3.addresses['fi']), 1)

    def test_get_policy_filters(self):
        filters = self.service_matcher.db._get_policy_filters()
        dis_filter = filters.get('disambiguation')
        self.assertEqual(dis_filter([0.6,0.1]), False)
        self.assertEqual(dis_filter([0.6,0.4]), True)
        fallback_filter = filters.get('fallback')
        self.assertEqual(fallback_filter([0.6,0.1]), False)
        self.assertEqual(fallback_filter([0.4,0.2]), False)
        self.assertEqual(fallback_filter([0.3,0.2]), True)
        
    def test_nest_form_events(self):
        events = [{"parse_data":{"intent": {"name":"random intent"}}},
                  {"parse_data":{"intent": {"name":"sports_service_search"}}}, {"event": "action", "name": "sports_service_search_form"},{"event": "active_loop", "name":"sports_service_search_form"}, {"event": "action_execution_rejected", "name": "sports_service_search_form"}, {"parse_data":{"intent": {"name":"any_intent_to reject_excecution"}}}, # Last two events of this line have been swapped as is done with rejections compared to database order
                  {"parse_data":{"intent": {"name":"ke6_something"}}},
                  {"event": "action", "name": "non_intent_form"},{"event": "active_loop", "name":"sports_service_search_form"},{"event": "active_loop", "name":None}, {"parse_data":{"intent": {"name":"disambiguation"}}}]
        nested_events = self.service_matcher.utils._nest_form_events(events)
        self.assertEqual(len(nested_events), 6)
        self.assertEqual(len(nested_events[1]['form_events']), 3)
        self.assertEqual(len(nested_events[4]['form_events']), 2) 
        
    def test_get_conversation_info(self):        
        conv_info = self.service_matcher._get_conversation_info(self.conversation_id)
        self.assertEqual(conv_info["messages"][0], "Tekstiä")
        self.assertEqual(conv_info["slots"]["municipality"], "Turku") 
        
    def test_get_municipality_ids_by_names(self):        
        mun_codes = self.service_matcher.utils._get_municipality_ids_by_names(["Turku"], self.service_matcher.db._get_all_municipalities())        
        self.assertEqual(mun_codes[0], "853")
        
        
    def test_check_life_events(self):    
        life_events1 = self.service_matcher.utils._check_life_events(["KE4"], self.service_matcher.db._get_all_life_event_codes())
        self.assertEqual(len(life_events1), 1)
        self.assertEqual(life_events1[0], "KE4")
        life_events2 = self.service_matcher.utils._check_life_events(["KE100"], self.service_matcher.db._get_all_life_event_codes())
        self.assertEqual(len(life_events2), 19)
        self.assertEqual(life_events2[0], "KE1")
        
    def test_check_service_classes(self):    
        service_classes1 = self.service_matcher.utils._check_service_classes(["P20.1"], self.service_matcher.db._get_all_service_classes())
        self.assertEqual(len(service_classes1), 1)
        self.assertEqual(service_classes1[0], "P20.1")
        service_classes1 = self.service_matcher.utils._check_service_classes(["P20.1", "nonsense"], self.service_matcher.db._get_all_service_classes())
        self.assertEqual(len(service_classes1), 1)
        self.assertEqual(service_classes1[0], "P20.1")
        service_classes1 = self.service_matcher.utils._check_service_classes(["P20.1", "P19"], self.service_matcher.db._get_all_service_classes())
        self.assertEqual(len(service_classes1), 2)
        service_classes2 = self.service_matcher.utils._check_service_classes([], self.service_matcher.db._get_all_service_classes())
        self.assertEqual(len(service_classes2), 226)
        service_classes2 = self.service_matcher.utils._check_service_classes(["nonsense"], self.service_matcher.db._get_all_service_classes())
        self.assertEqual(len(service_classes2), 226)

    def test_service_class_and_life_event_name_recognition(self):
        found_service_classes = self.service_matcher.utils._get_service_classes_from_intent_name("p12_asd")
        self.assertCountEqual(found_service_classes, ["P12"])
        found_service_classes = self.service_matcher.utils._get_service_classes_from_intent_name("p12_P4.12_asd")
        self.assertCountEqual(found_service_classes, ["P4.12", "P12"])
        found_service_classes = self.service_matcher.utils._get_service_classes_from_intent_name("p12_P4.12_P12_asd")
        self.assertCountEqual(found_service_classes, ["P4.12", "P12"])
        found_service_classes = self.service_matcher.utils._get_service_classes_from_intent_name("asd")
        self.assertEqual(found_service_classes, [])
        found_service_classes = self.service_matcher.utils._get_service_classes_from_intent_name("ke1_asd")
        self.assertEqual(found_service_classes, [])

        found_life_events = self.service_matcher.utils._get_life_events_from_intent_name("ke4_asd")
        self.assertCountEqual(found_life_events, ["KE4"])
        found_life_events = self.service_matcher.utils._get_life_events_from_intent_name("ke4_KE5.5_asd")
        self.assertCountEqual(found_life_events, ["KE5.5", "KE4"])
        found_life_events = self.service_matcher.utils._get_life_events_from_intent_name("ke4_KE5.5_KE4_asd")
        self.assertCountEqual(found_life_events, ["KE5.5", "KE4"])
        found_life_events = self.service_matcher.utils._get_life_events_from_intent_name("asd")
        self.assertEqual(found_life_events, [])
        found_life_events = self.service_matcher.utils._get_life_events_from_intent_name("p1_asd")
        self.assertEqual(found_life_events, [])

    @patch('requests.post', side_effect=mocked_requests_post)
    def test_get_matching_services(self, mock_post):

        # Barely tests the threshold check, score and vector scales are not necessarily realistic
        matches1 = self.service_matcher._get_matching_services(text="Jotain", municipalities=["853"], life_events=None, service_classes=None, match_service_classes=False, top_k=5, score_threshold=54610, text_recommender="nlp", language="fi", translate_missing_texts=True)
        self.assertEqual(len(matches1), 1)
        matches2 = self.service_matcher._get_matching_services(text="Jotain", municipalities=["853"], life_events=None, service_classes=None, match_service_classes=False, top_k=5, score_threshold=54612, text_recommender="nlp", language="fi", translate_missing_texts=True)
        self.assertEqual(len(matches2), 1)
        matches3 = self.service_matcher._get_matching_services(text="Jotain", municipalities=["853"], life_events=None, service_classes=None, match_service_classes=False, top_k=5, score_threshold=54650, text_recommender="nlp", language="fi", translate_missing_texts=True)
        self.assertEqual(len(matches3), 0)

        
    @patch('requests.post', side_effect=mocked_requests_post)
    def test_get_service_recommendations_by_conversation(self, mock_post):
        
        recommendations = self.service_matcher.get_service_recommendations_by_conversation(self.conversation_id, models.ServiceRecommendConversationQuery(mode="infer"))
        self.assertEqual(recommendations[0]['service'].id, self.test_service_data[0]['id'])
        
        recommendations = self.service_matcher.get_service_recommendations_by_conversation(self.conversation_id2, models.ServiceRecommendConversationQuery(mode="infer"))
        self.assertEqual(recommendations[0]['service'].id, self.test_service_data[0]['id'])
        
        recommendations = self.service_matcher.get_service_recommendations_by_conversation(self.conversation_id2, models.ServiceRecommendConversationQuery(mode="infer"))
        self.assertEqual(len(recommendations), 0)
        
        recommendations = self.service_matcher.get_service_recommendations_by_conversation(self.conversation_id2, models.ServiceRecommendConversationQuery(mode="infer"))
        self.assertEqual(len(recommendations), 0)
        
        recommendations = self.service_matcher.get_service_recommendations_by_conversation(self.conversation_id2, models.ServiceRecommendConversationQuery(mode="infer"))
        self.assertEqual(len(recommendations), 0)

        recommendations = self.service_matcher.get_service_recommendations_by_conversation(self.conversation_id2, models.ServiceRecommendConversationQuery(mode="infer"))
        self.assertEqual(recommendations[0]['service'].id, self.test_service_data[0]['id'])

        recommendations = self.service_matcher.get_service_recommendations_by_conversation(self.conversation_id2, models.ServiceRecommendConversationQuery(mode="infer"))
        self.assertEqual(recommendations[0]['service'].id, self.test_service_data[0]['id'])

        recommendations = self.service_matcher.get_service_recommendations_by_conversation(self.conversation_id2, models.ServiceRecommendConversationQuery(mode="infer"))
        self.assertEqual(recommendations[0]['service'].id, self.test_service_data[0]['id'])
        
        recommendations = self.service_matcher.get_service_recommendations_by_conversation(self.conversation_id2, models.ServiceRecommendConversationQuery(mode="infer"))
        self.assertEqual(recommendations[0]['service'].id, self.test_service_data[0]['id'])
        
        recommendations = self.service_matcher.get_service_recommendations_by_conversation(self.conversation_id2, models.ServiceRecommendConversationQuery(mode="infer"))
        self.assertEqual(recommendations[0]['service'].id, self.test_service_data[0]['id'])
        
        recommendations = self.service_matcher.get_service_recommendations_by_conversation(self.conversation_id2, models.ServiceRecommendConversationQuery(mode="infer"))
        self.assertEqual(len(recommendations), 0)
        
        recommendations = self.service_matcher.get_service_recommendations_by_conversation(self.conversation_id2, models.ServiceRecommendConversationQuery(mode="infer"))
        self.assertEqual(recommendations[0]['service'].id, self.test_service_data[0]['id'])
        
        recommendations = self.service_matcher.get_service_recommendations_by_conversation(self.conversation_id2, models.ServiceRecommendConversationQuery(mode="infer"))
        self.assertEqual(recommendations[0]['service'].id, self.test_service_data[0]['id'])
        
        recommendations = self.service_matcher.get_service_recommendations_by_conversation(self.conversation_id2, models.ServiceRecommendConversationQuery(mode="infer"))
        self.assertEqual(recommendations[0]['service'].id, self.test_service_data[0]['id'])
        
        recommendations = self.service_matcher.get_service_recommendations_by_conversation(self.conversation_id2, models.ServiceRecommendConversationQuery(mode="infer"))
        self.assertEqual(recommendations[0]['service'].id, self.test_service_data[0]['id'])
        
        recommendations = self.service_matcher.get_service_recommendations_by_conversation(self.conversation_id2, models.ServiceRecommendConversationQuery(mode="infer"))
        self.assertEqual(recommendations[0]['service'].id, self.test_service_data[0]['id'])
        
        recommendations = self.service_matcher.get_service_recommendations_by_conversation(self.conversation_id2, models.ServiceRecommendConversationQuery(mode="infer"))
        self.assertEqual(recommendations[0]['service'].id, self.test_service_data[0]['id'])

        recommendations = self.service_matcher.get_service_recommendations_by_conversation(self.conversation_id2, models.ServiceRecommendConversationQuery(mode="infer"))
        self.assertEqual(len(recommendations), 0)
        
    @patch('requests.post', side_effect=mocked_requests_post)
    def test_get_service_recommendations_by_intent(self, mock_post):
        
        recommendations = self.service_matcher.get_service_recommendations_by_intent(models.ServiceRecommendIntentQuery(intent="p1_greet"))
        self.assertEqual(recommendations[0]['service'].id, self.test_service_data[0]['id'])

        recommendations = self.service_matcher.get_service_recommendations_by_intent(models.ServiceRecommendIntentQuery(intent="ke6_something"))
        self.assertEqual(recommendations[0]['service'].id, self.test_service_data[0]['id'])
        
        recommendations = self.service_matcher.get_service_recommendations_by_intent(models.ServiceRecommendIntentQuery(intent="p2_greet"))
        self.assertEqual(len(recommendations), 0)      

        recommendations = self.service_matcher.get_service_recommendations_by_intent(models.ServiceRecommendIntentQuery(intent="p1_greet",
                                                                                                                        municipalities=["Turku"]))
        self.assertEqual(recommendations[0]['service'].id, self.test_service_data[0]['id'])

        recommendations = self.service_matcher.get_service_recommendations_by_intent(models.ServiceRecommendIntentQuery(intent="p1_greet",
                                                                                                                        municipalities=["Naantali"]))
        self.assertEqual(len(recommendations), 0)

    @patch('requests.post', side_effect=mocked_requests_post)
    def test_get_service_recommendations_by_intent_and_options(self, mock_post):

        recommendations = self.service_matcher.get_service_recommendations_by_intent_and_options(models.ServiceRecommendIntentAndOptionsQuery(intent="ke7_something"))
        self.assertEqual(len(recommendations), 1) 
        self.assertEqual(recommendations[0]['service'].id, self.test_service_data[0]['id'])

        recommendations = self.service_matcher.get_service_recommendations_by_intent_and_options(models.ServiceRecommendIntentAndOptionsQuery(intent="p2_greet"))
        self.assertEqual(len(recommendations), 0) 
        
    @patch('requests.post', side_effect=mocked_requests_post)
    def test_get_service_recommendations(self, mock_post):
        os.environ['NLP_VECTORIZER_HOST'] = 'request_success'
        service_r = self.service_matcher.get_service_recommendations(models.ServiceRecommendQuery(need_text="Jotain", municipalities=["Turku"]))
        self.assertEqual(service_r[0]["service"].id, self.test_service_data[0]["id"])

    @patch('requests.post', side_effect=mocked_requests_post)
    def test_get_service_class_recommendations(self, mock_post):
        os.environ['NLP_VECTORIZER_HOST'] = 'request_success'
        service_r = self.service_matcher.get_service_class_recommendations(models.ServiceClassRecommendQuery(need_text="Jotain"))
        self.assertEqual(service_r[0]["service_class_code"], "P1")

if __name__ == '__main__':
    unittest.main()
