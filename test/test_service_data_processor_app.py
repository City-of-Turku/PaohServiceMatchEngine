import sys
sys.path.append(
    'service_data_processor_app/ServiceDataProcessorFunction')
from service_data_processor.processor import ServiceDataProcessor
from unittest.mock import MagicMock, patch
import unittest
import json
import os


NLP_VECTORIZER_JSON_RESPONSE_SUCCESS = {"vector": [123, 123, 123, 123]}
NLP_VECTORIZER_JSON_RESPONSE_ERROR = {
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
    elif args[0] == 'request_error/vectorize':
        return MockResponse(NLP_VECTORIZER_JSON_RESPONSE_ERROR, 400)
    
# This method will be used by the mock to replace requests.get to service matcher API
def mocked_requests_get(*args, **kwargs):

    class MockResponse:
        def __init__(self, status_code):
            self.status_code = status_code

    if args[0] == 'request_success/syncVectors':
        return MockResponse(200)


class ServiceDataProcessortTest(unittest.TestCase):

    def setUp(self):
        with open('test/example_service_data.json') as json_file:
            self.raw_services = json.load(json_file)
        self.mongo_client_instance = MagicMock()
        self.mongo_client_instance.service_db = MagicMock()
        self.mongo_client_instance.service_db.ytr_services = MagicMock()
        self.mongo_client_instance.service_db.services.find = MagicMock()
        self.mongo_client_instance.service_db.services.find.return_value = self.raw_services
        self.mongo_client_instance.service_db.service_vectors = MagicMock()
        self.mongo_client_instance.service_db.service_vectors.estimated_document_count = MagicMock()
        self.mongo_client_instance.service_db.service_vectors.estimated_document_count.return_value = 1
        self.mongo_client_instance.service_db.service_class_vectors = MagicMock()
        self.mongo_client_instance.service_db.service_class_vectors.estimated_document_count = MagicMock()
        self.mongo_client_instance.service_db.service_class_vectors.estimated_document_count.return_value = 1
        self.mongo_client_instance.service_db.service_class_vectors.find = MagicMock()
        self.mongo_client_instance.service_db.service_class_vectors.find.return_value = []

        self.data_processor = ServiceDataProcessor(self.mongo_client_instance)
        
        translator_instance = MagicMock()
        translator_instance.translate = MagicMock()
        translator_instance.translate.return_value = True
        translator_instance.save_new_translations = MagicMock()
        translator_instance.save_new_translations.return_value = None
        self.data_processor.translator = translator_instance
        
    @patch('requests.get', side_effect=mocked_requests_get)
    @patch('requests.post', side_effect=mocked_requests_post)
    def test_process_service_descriptions(self, mock_get, mock_post):
        os.environ['NLP_VECTORIZER_HOST'] = 'request_success'
        os.environ['SERVICE_MATCHER_HOST'] = 'request_success'
        os.environ['LEXICAL_TEXT_SEARCH_HOST'] = 'request_success'
        response = self.data_processor.process_service_descriptions()
        self.assertEqual(response, "2 new services processed")

    @patch('requests.get', side_effect=mocked_requests_get)
    @patch('requests.post', side_effect=mocked_requests_post)
    def test_process_service_classes(self, mock_get, mock_post):
        os.environ['NLP_VECTORIZER_HOST'] = 'request_success'
        os.environ['SERVICE_MATCHER_HOST'] = 'request_success'
        os.environ['LEXICAL_TEXT_SEARCH_HOST'] = 'request_success'
        response = self.data_processor.process_service_classes()
        self.assertEqual(response, "3 new service classes processed")


if __name__ == '__main__':
    unittest.main()
