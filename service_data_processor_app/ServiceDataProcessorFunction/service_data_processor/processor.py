import os
from typing import Optional
from pymongo import MongoClient
import requests
from datetime import datetime, timedelta
from .translator import *
LIFE_EVENT_CODES = ['KE1', 'KE1.1', 'KE2', 'KE3', 'KE4', 'KE4.1', 'KE4.2', 'KE4.3', 'KE4.4',
                    'KE5', 'KE6', 'KE7', 'KE8', 'KE9', 'KE10', 'KE11', 'KE12', 'KE13', 'KE14']

class ServiceDataProcessor():
    """
    A class used to process service data for the service matcher's needs

    Args
    ----------
    mongo_client : MongoClient (default None)
        MongoDB client where service data is stored


    Methods
    -------
    process_service_descriptions()
        Processes service descriptions

    process_service_classes()
        Processes service classes

    """

    def __init__(self, mongo_client: Optional[MongoClient] = None) -> None:
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
        self.municipality_codes = self._get_all_municipality_codes()
        self.translator = Translator(mongo_client=self.mongo_client)
        self.n_translated = 0

    def process_service_descriptions(self) -> str:
        print("start preprocessing service desc")
        if self._get_service_desc_vectors_count() > 0:
            start_datetime = datetime.utcnow() - timedelta(hours=24)
            all_services = self._get_all_services(start_datetime)
        else:
            all_services = self._get_all_services()

        print(len(all_services), "new services found")

        if len(all_services) == 0:
            msg = "no new services to process"
            print(msg)
            return msg

        service_desc_vectors = []
        classifications = []
        for service in all_services:
            vector_text = None
            if next((item for item in service["descriptions"]["fi"] if item["type"] == "Description"), None) is not None and next((item for item in service["descriptions"]["fi"] if item["type"] == "Description"), None)["value"] is not None:
                vector_text = '. '.join(filter(
                    None,
                    (
                        service["name"]["fi"],
                        next((item for item in service["descriptions"]["fi"] if item["type"] == "Description"), None)["value"]
                        #,next((item["name"] for item in service["organizations"] if item["name"] is not None), None)
                    )
                ))
            elif service["name"]["fi"] is not None:
                vector_text = service["name"]["fi"]
            else:
                continue

            municipality_codes = [area["code"] for area in service["areas"]["fi"] if area.get(
                'type') == 'Municipality']
            life_event_codes = [life_event["code"]
                                for life_event in service["lifeEvents"]["fi"]]
            service_class_codes = [service_class["code"] for service_class in service["serviceClasses"]["fi"]]
            if len(municipality_codes) == 0:
                municipality_codes = self.municipality_codes

            service_desc_vectors.append({"id": service["id"],
                                         "service_class_codes": service_class_codes,
                                         "vector_text": vector_text,
                                         "municipality_codes": municipality_codes,
                                         "life_event_codes": life_event_codes
                                         })
            classifications.append({"id": service["id"],
                                         "service_class_codes": service_class_codes,
                                         "municipality_codes": municipality_codes,
                                         "life_event_codes": life_event_codes
                                         })

            self._translate_missing_texts(service)

        for index, service in enumerate(service_desc_vectors):
            body = {"text": service["vector_text"]}
            r = requests.post(
                os.environ["NLP_VECTORIZER_HOST"]+"/vectorize", json=body)
            if r.status_code != 200:
                print(r.text)
            else:
                vector = r.json()["vector"]
                service_desc_vectors[index]["vector"] = vector
                service_desc_vectors[index].pop("vector_text", None)

        self._write_service_desc_vectors(service_desc_vectors)
        self._write_classifications(classifications)
        self._save_new_translations()
        
        # Remove classifications and vectors of services that have been removed entirely
        db_ids = self._get_current_classification_ids()
        services = self._get_all_services()
        current_ids = [ser["id"] for ser in services]
        removed_ids = [db_id for db_id in db_ids if db_id not in current_ids]
        # Only remove if there really was a proper set of services fetched from database
        if len(current_ids) > 0:
            self._remove_old_classifications(removed_ids)
            self._remove_old_service_desc_vectors(removed_ids)
        
        # Sync vectors to service matcher microservice
        r = requests.get(os.environ["SERVICE_MATCHER_HOST"]+"/syncVectors")
        # Sync services to lexical text search microservice
        r = requests.get(os.environ["LEXICAL_TEXT_SEARCH_HOST"]+"/syncServices")

        msg = f"{len(service_desc_vectors)} new services processed"
        print(msg)
        msg2 = f"{self.n_translated} new translations processed"
        print(msg2)
        msg3 = f"{len(removed_ids)} old service vectors of removed services removed"
        print(msg3)
        return msg

    def process_service_classes(self) -> str:
        print("start preprocessing service classes")
        if self._get_service_class_vectors_count() > 0:
            start_datetime = datetime.utcnow() - timedelta(hours=24)
            all_services = self._get_all_services(start_datetime)
        else:
            all_services = self._get_all_services()

        print(len(all_services), "new services found")

        if len(all_services) == 0:
            msg = "no new services to process"
            print(msg)
            return msg

        service_class_vectors = [
            {"name": serviceClass["name"], "code": serviceClass["code"], "description": serviceClass["description"]} for service in all_services for serviceClass in service["serviceClasses"]["fi"]]
        service_class_vectors = list(
            {v["code"]: v for v in service_class_vectors}.values())

        service_class_vectors = [
            service_class for service_class in service_class_vectors if not self._get_service_class_vector_exists(service_class["code"])]

        if len(service_class_vectors) > 0:
            for index, service_class in enumerate(service_class_vectors):
                body = {"text": '. '.join(
                    filter(None, (service_class["name"], service_class["description"])))}
                r = requests.post(
                    os.environ["NLP_VECTORIZER_HOST"]+"/vectorize", json=body)
                if r.status_code != 200:
                    print(r.text)
                else:
                    vector = r.json()["vector"]
                    service_class_vectors[index]["vector"] = vector
                    service_class_vectors[index].pop("description", None)

            self._write_service_class_vectors(service_class_vectors)

        msg = f"{len(service_class_vectors)} new service classes processed"
        print(msg)
        return msg
    
    def _translate_missing_texts(self, service: dict) -> None:
        languages = ['en', 'sv']
        for language in languages:
            
            if not service.get('name').get(language):
                name_translated = self.translator.translate(service.get('name').get('fi'), 'fi', language)
                self.n_translated = self.n_translated + sum([name_translated])
    
            lang_desc = [desc["value"] for desc in service.get('descriptions').get(language) if desc["value"] is not None and desc["type"] == "Description"]
            if len(lang_desc) == 0:
                fi_desc = [desc["value"] for desc in service.get('descriptions').get('fi')
                           if desc["value"] is not None and desc["type"] == "Description"]
                desc_translated = [self.translator.translate(fi_desc_el, 'fi', language) for fi_desc_el in fi_desc]
                self.n_translated = self.n_translated + sum(desc_translated)

            lang_gdesc = [desc["value"] for desc in service.get('descriptions').get(language) if desc["value"] is not None and desc["type"] == "GD_Description"]
            if len(lang_gdesc) == 0:
                fi_gdesc = [desc["value"] for desc in service.get('descriptions').get('fi')
                           if desc["value"] is not None and desc["type"] == "GD_Description"]
                gdesc_translated = [self.translator.translate(fi_gdesc_el, 'fi', language) for fi_gdesc_el in fi_gdesc]
                self.n_translated = self.n_translated + sum(gdesc_translated)
                
            lang_summ = [desc["value"] for desc in service.get('descriptions').get(language) if desc["value"] is not None and desc["type"] == "Summary"]
            if len(lang_summ) == 0:
                fi_summ = [desc["value"] for desc in service.get('descriptions').get('fi')
                           if desc["value"] is not None and desc["type"] == "Summary"]
                summ_translated = [self.translator.translate(fi_summ_el, 'fi', language) for fi_summ_el in fi_summ]
                self.n_translated = self.n_translated + sum(summ_translated)
                
            lang_gsumm = [desc["value"] for desc in service.get('descriptions').get(language) if desc["value"] is not None and desc["type"] == "GD_Summary"]
            if len(lang_gsumm) == 0:
                fi_gsumm = [desc["value"] for desc in service.get('descriptions').get('fi')
                           if desc["value"] is not None and desc["type"] == "GD_Summary"]
                gsumm_translated = [self.translator.translate(fi_gsumm_el, 'fi', language) for fi_gsumm_el in fi_gsumm]
                self.n_translated = self.n_translated + sum(gsumm_translated)

    def _get_all_services(self, start_datetime: Optional[datetime] = None) -> list:
        if start_datetime:
            all_services = list(self.mongo_client.service_db.services.find(
                {"lastUpdated": {"$gte": start_datetime}}))
            return(all_services)

        all_services = list(self.mongo_client.service_db.services.find())
        return(all_services)

    def _get_service_desc_vectors_count(self) -> int:
        return self.mongo_client.service_db.service_vectors.estimated_document_count()

    def _get_service_class_vectors_count(self) -> int:
        return self.mongo_client.service_db.service_class_vectors.estimated_document_count()

    def _get_service_class_vector_exists(self, service_class_code: str) -> bool:
        found_service_classes = list(
            self.mongo_client.service_db.service_class_vectors.find({"code": service_class_code}))
        if len(found_service_classes) > 0:
            return True
        else:
            return False

    def _get_all_municipality_codes(self) -> list:
        all_municipalities = self.mongo_client.service_db.municipalities.find({
        })
        all_municipalities = list(all_municipalities)
        codes = [municipality.get('id') for municipality in all_municipalities]
        return(codes)

    def _remove_old_classifications(self, delete_ids: list) -> None:
        del_count = 0
        delete_result = self.mongo_client.service_db.classifications.delete_many(
            {"id": {"$in": delete_ids}})
        del_count = delete_result.deleted_count
        print(del_count, "old classifications deleted")
        
    def _remove_old_service_desc_vectors(self, delete_ids: list) -> None:
        del_count = 0
        delete_result = self.mongo_client.service_db.service_vectors.delete_many(
            {"id": {"$in": delete_ids}})
        del_count = delete_result.deleted_count
        print(del_count, "old service desc vectors deleted")

    def _remove_old_service_class_vectors(self, delete_ids: list) -> None:
        del_count = 0
        delete_result = self.mongo_client.service_db.service_class_vectors.delete_many(
            {"code": {"$in": delete_ids}})
        del_count = delete_result.deleted_count
        print(del_count, "old service class vectors deleted")

    def _write_classifications(self, classifications: list) -> None:
        ids_to_delete = [classification["id"]
                         for classification in classifications]
        self._remove_old_classifications(ids_to_delete)
        self.mongo_client.service_db.classifications.insert_many(
            classifications)
        
    def _write_service_desc_vectors(self, service_desc_vectors: list) -> None:
        ids_to_delete = [service_desc_vector["id"]
                         for service_desc_vector in service_desc_vectors]
        self._remove_old_service_desc_vectors(ids_to_delete)
        self.mongo_client.service_db.service_vectors.insert_many(
            service_desc_vectors)

    def _write_service_class_vectors(self, service_class_vectors: list) -> None:
        ids_to_delete = [service_class_vector["code"]
                         for service_class_vector in service_class_vectors]
        self._remove_old_service_class_vectors(ids_to_delete)
        self.mongo_client.service_db.service_class_vectors.insert_many(
            service_class_vectors)
        
    def _get_current_classification_ids(self) -> None:
        classifications = list(self.mongo_client.service_db.classifications.find({}))
        ids = [classification["id"] for classification in classifications]
        return(ids)

    def _save_new_translations(self) -> None:
        self.translator.save_new_translations()
