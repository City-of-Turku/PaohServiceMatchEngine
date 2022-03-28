import os
from pymongo import MongoClient
from .models import *
from typing import Optional
from datetime import datetime, timedelta


class LexicalTextSearchDB():
    """
    A class for database operations of lexical text search

    Args
    ----------
    mongo_client : MongoClient (default None)
        MongoDB client where service data is stored

    """

    def __init__(self, mongo_client: Optional[MongoClient] = None, supported_languages: list = ['fi', 'en', 'sv']) -> None:
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

        self.supported_languages = supported_languages
        self.services = []
        self._get_all_services_from_db()

    def _get_all_services_from_db(self, start_datetime: Optional[datetime] = None) -> int:
        if start_datetime:
            all_services = list(self.mongo_client.service_db.services.find(
                {"lastUpdated": {"$gte": start_datetime}}))
        else:
            all_services = list(self.mongo_client.service_db.services.find())

        translations = list(self.mongo_client.service_db.translations.find({}))
        self.translation_dict = {'en': {}, 'sv': {}}
        for translation in translations:
            if translation.get('source_language') == 'fi':
                self.translation_dict[translation.get('target_language')][translation.get(
                    'source_text')] = translation.get('target_text')

        all_services = [Service(**service) for service in all_services]
        updated_services_count = 0
        for service in all_services:
            service_updated = False
            text_el = {}
            for language in self.supported_languages:
                lan_name = self._get_translation_if_missing(
                    service.name[language], service.name["fi"], language)
                lan_desc = [desc["value"]
                            for desc in service.descriptions[language] if desc["value"] is not None and desc["type"] == "Description"]
                if len(lan_desc) == 0:
                    lan_desc = [self._get_translation_if_missing(None, desc["value"], language)
                                for desc in service.descriptions["fi"] if desc["value"] is not None and desc["type"] == "Description"]

                org = [org["name"] for org in service.organizations
                       if org["name"] is not None]

                lan_desc.insert(0, lan_name)
                lan_desc = lan_desc + org
                lan_desc = [text for text in lan_desc if text]
                text_el[language] = ' '.join(lan_desc)
            if any([text_el[lan] for lan in text_el.keys()]):
                existing_service_index = self._get_service_index_by_id(
                    service.id)
                if existing_service_index:
                    self.services[existing_service_index] = {
                        "id": service.id, "text": text_el}
                else:
                    self.services.append({"text": text_el, "id": service.id})
                service_updated = True
            if service_updated:
                updated_services_count += 1

        return updated_services_count

    def _get_translation_if_missing(self, text: str, finnish_text: str, language: str) -> str:
        if text is not None or language == 'fi':
            return(text)
        elif finnish_text is not None:
            translation = self.translation_dict[language].get(finnish_text)
            return(translation)
        else:
            return(None)

    def _get_service_index_by_id(self, service_id: str) -> int:
        return next((index for (index, d) in enumerate(self.services) if d["id"] == service_id), None)

    def update_services(self) -> str:
        if len(self.services) > 0:
            start_datetime = datetime.utcnow() - timedelta(hours=24)
            updated_services_count = self._get_all_services_from_db(
                start_datetime)
            return f"Updated {updated_services_count} services"
        else:
            updated_services_count = self._get_all_services_from_db()
            return f"Added {updated_services_count} services"

    def get_services(self) -> list:
        return self.services

    def get_services_by_index(self, index: int) -> dict:
        return self.services[index]
