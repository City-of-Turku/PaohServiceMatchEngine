import os
import uuid, json
from typing import Optional
from pymongo import MongoClient
import requests
from datetime import datetime, timedelta

class Translator():
    """
    A class to call translator to translate names and descriptions to English and Swedish

    Args
    ----------
    mongo_client : MongoClient ( default None )
        MongoDB client where service data is stored

    api_session : requests.Session ( default None )
        A requests session to send requests to Microsoft Translator API


    Methods
    -------
        
    translate( text: str, source_language: str, target_languages: list )
        Translate text from language to other, use DB cache as default
    save_new_translations( )
        Persist new translations to database
        
    """
    
    def __init__(self, mongo_client: Optional[MongoClient] = None, api_session: Optional[requests.Session] = None) -> None:
        if mongo_client is None:
            self.mongo_client = MongoClient("mongodb://{}:{}@{}:{}/{}".format(
                os.environ.get("MONGO_USERNAME"),
                os.environ.get("MONGO_PASSWORD"),
                os.environ.get("MONGO_HOST"),
                os.environ.get("MONGO_PORT"),
                os.environ.get("MONGO_DB")),
                ssl=True,
                tlsInsecure=True,
                replicaSet="globaldb",
                retrywrites=False,
                maxIdleTimeMS=120000,
                appName="@{}@".format(os.environ.get("MONGO_USERNAME"))
                )
        else:
            self.mongo_client = mongo_client
        
        location = 'westeurope'
        if api_session is None:
            self.api_session = requests.Session()
            self.api_session.auth = None
            self.api_session.cert = None
            self.api_session.verify = True
            self.api_session.headers = {
                                        'Ocp-Apim-Subscription-Key': os.environ.get("TRANSLATOR_SUBSCRIPTION_KEY"),
                                        'Ocp-Apim-Subscription-Region': location,
                                        'Content-type': 'application/json',
                                        'X-ClientTraceId': str(uuid.uuid4())
                                        }
        else:
            self.api_session = api_session
        self._load_translations()
        self.translations_to_save =[]
        self.latest_translation_time = None
           
    def _load_translations(self) -> None:        
        translations = list(self.mongo_client.service_db.translations.find({}))
        self.translation_dict = {'en':{}, 'sv': {}}
        for translation in translations:
            if translation.get('source_language') == 'fi':
                self.translation_dict[translation.get('target_language')][translation.get('source_text')] = translation.get('target_text')

    def save_new_translations(self) -> None:
        if len(self.translations_to_save) > 0:
            self.mongo_client.service_db.translations.insert_many(self.translations_to_save)
                
    def _add_translation(self, source_language: str, target_language: str, source_text: str, target_text: str) -> None:
        if source_language == 'fi':
            if source_text not in self.translation_dict[target_language].keys():
                self.translation_dict[target_language][source_text] = target_text
                translation_object = {'source_language': source_language,
                                      'target_language': target_language,
                                      'source_text': source_text,
                                      'target_text': target_text}
                self.translations_to_save.append(translation_object)
        
    def _call_translator(self, source_text: str, source_language: str, target_language: str):
        
        # Add your location, also known as region. The default is global.
        # This is required if using a Cognitive Services resource.
        endpoint = "https://api.cognitive.microsofttranslator.com"
        
        path = '/translate'
        constructed_url = endpoint + path
        
        params = {
            'api-version': '3.0',
            'from': source_language,
            'to': [target_language]
        }
        constructed_url = endpoint + path
        
        # You can pass more than one object in body.
        body = [{
            'text': source_text
        }]
        
        ## Pick translation
        while self.latest_translation_time is not None and (datetime.now() - self.latest_translation_time).seconds < 2:
            pass
        response = self.api_session.post(constructed_url, params=params, json=body)
        self.latest_translation_time = datetime.now()
        if response.status_code == 200:
            translated = response.json()
            if len(translated) > 0:
                translations = translated[0].get("translations")
                if len(translations) > 0:
                    translated_text = translations[0].get("text")
                else:
                    translated_text = None
            else:
                translated_text = None
            return(translated_text)
        

    def translate(self, source_text: str, source_language: str, target_language: str) -> bool:
        if source_text is not None:
            if source_text in self.translation_dict[target_language].keys():
                return(False)
            else:
                translated_text = self._call_translator(source_text, source_language, target_language)
                if translated_text is not None:
                    self._add_translation(source_language, target_language, source_text, translated_text)
                    return(True)
                else:
                    return(False)
        else:
            return(False)
                