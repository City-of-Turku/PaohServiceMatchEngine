import os
import logging
import re
import copy
from pymongo import MongoClient
from .classifications import SERVICE_CLASSES, LIFE_EVENT_CODES, MUNICIPALITIES
from .models import *
from typing import Optional

class ServiceMatcherDB():
    """
    A class for database operations of service matcher

    Args
    ----------
    mongo_client : MongoClient (default None)
        MongoDB client where service data is stored

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
        self._update_desc_vectors()
        self._update_translations()
        
    def _get_service_desc_vectors(self, service_class_codes_filter: Optional[list] = None, municipality_ids_filter: Optional[list] = None, life_events_filter: Optional[list] = None) -> list:
        #filter_dict = {}
        #if (service_class_codes_filter is not None) and len(service_class_codes_filter) < len(SERVICE_CLASSES):
        #    filter_dict["service_class_codes"] = {"$in": service_class_codes_filter}
        #if (municipality_ids_filter is not None) and len(municipality_ids_filter) < len(MUNICIPALITIES):
        #    filter_dict["municipality_codes"] = {"$in": municipality_ids_filter}            
        #if (life_events_filter is not None) and len(life_events_filter) < len(LIFE_EVENT_CODES):
        #    filter_dict["life_event_codes"] = {"$in": life_events_filter}
        #vectors = list(self.mongo_client.service_db.service_vectors.find(filter_dict))
        vectors = self.service_vectors
        if (service_class_codes_filter is not None) and len(service_class_codes_filter) < len(SERVICE_CLASSES):
            vectors = [vect for vect in vectors if len(set(vect.get("service_class_codes")).intersection(set(service_class_codes_filter))) != 0]
        if (municipality_ids_filter is not None) and len(municipality_ids_filter) < len(MUNICIPALITIES):
            vectors = [vect for vect in vectors if len(set(vect.get("municipality_codes")).intersection(set(municipality_ids_filter))) != 0]          
        if (life_events_filter is not None) and len(life_events_filter) < len(LIFE_EVENT_CODES):
            vectors = [vect for vect in vectors if len(set(vect.get("life_event_codes")).intersection(set(life_events_filter))) != 0]  
        return vectors
    
    def _get_service_ids_by_filters(self, service_class_codes_filter: Optional[list] = None, municipality_ids_filter: Optional[list] = None, life_events_filter: Optional[list] = None) -> list:
        #filter_dict = {}
        #if (service_class_codes_filter is not None) and len(service_class_codes_filter) < len(SERVICE_CLASSES):
        #    filter_dict["service_class_codes"] = {"$in": service_class_codes_filter}
        #if (municipality_ids_filter is not None) and len(municipality_ids_filter) < len(MUNICIPALITIES):
        #    filter_dict["municipality_codes"] = {"$in": municipality_ids_filter}            
        #if (life_events_filter is not None) and len(life_events_filter) < len(LIFE_EVENT_CODES):
        #    filter_dict["life_event_codes"] = {"$in": life_events_filter}
        #services = list(self.mongo_client.service_db.classifications.find(filter_dict))
        classifications = self.classifications
        if (service_class_codes_filter is not None) and len(service_class_codes_filter) < len(SERVICE_CLASSES):
            classifications = [cl for cl in classifications if len(set(cl.get("service_class_codes")).intersection(set(service_class_codes_filter))) != 0]
        if (municipality_ids_filter is not None) and len(municipality_ids_filter) < len(MUNICIPALITIES):
            classifications = [cl for cl in classifications if len(set(cl.get("municipality_codes")).intersection(set(municipality_ids_filter))) != 0]          
        if (life_events_filter is not None) and len(life_events_filter) < len(LIFE_EVENT_CODES):
            classifications = [cl for cl in classifications if len(set(cl.get("life_event_codes")).intersection(set(life_events_filter))) != 0]  
        service_ids = [cl.get('id') for cl in classifications]
        return service_ids
    
    def _update_desc_vectors(self) -> None:
        self.service_vectors = list(self.mongo_client.service_db.service_vectors.find({}))
        self.classifications = [{i:ser[i] for i in ser if i!='vector'} for ser in self.service_vectors]

    def _update_translations(self) -> None:
        translations = list(self.mongo_client.service_db.translations.find({}))
        self.translation_dict = {'en':{}, 'sv': {}}
        for translation in translations:
            if translation.get('source_language') == 'fi':
                self.translation_dict[translation.get('target_language')][translation.get('source_text')] = translation.get('target_text')

    def _get_service_class_vectors(self) -> list:
        return list(self.mongo_client.service_db.service_class_vectors.find({}))

    def _get_all_service_classes(self) -> list:
        return([ServiceClass(**sc) for sc in SERVICE_CLASSES])
    
    def _get_all_life_event_codes(self) -> list:
        return(LIFE_EVENT_CODES)

    def _get_all_municipalities(self) -> list:
        return(MUNICIPALITIES)

    def _get_all_services(self, include_channels: bool = False, translate_missing_texts: bool = False) -> list:
        res = []
        all_services = list(self.mongo_client.service_db.services.find())
        all_services = [self._fill_translation_indicators(service) for service in all_services]
        if translate_missing_texts:
            all_services = [self._translate_missing_texts(service) for service in all_services]
        all_services = [Service(**service) for service in all_services]
        if include_channels:
            service_ids = [ser.id for ser in all_services]
            found_channels = list(
                self.mongo_client.service_db.channels.find({"serviceIds": {"$in": service_ids}}))
            found_channels = [ServiceChannel(**channel) for channel in found_channels]
            for service in all_services:
                ser_channels = [cha for cha in found_channels if cha.serviceIds is not None and (service.id in cha.serviceIds)]
                res = res + [{'service': service, 'channels': ser_channels}]
        else:
            res = [{'service': ser} for ser in all_services]
        return(res)

    def _get_services_by_ids(self, service_ids: list, include_channels: bool = False, translate_missing_texts: bool = False) -> list:
        res = []
        fetched_services = list(self.mongo_client.service_db.services.find({"id": {"$in": service_ids}}))
        filtered_services = []
        for s_id in service_ids:
            ser = [service for service in fetched_services if service.get('id') == s_id]
            if len(ser) > 0:
                filtered_services = filtered_services + ser
        filtered_services = [ser for ser in filtered_services if ser.get("id") in service_ids]
        filtered_services = [self._fill_translation_indicators(service) for service in filtered_services]
        if translate_missing_texts:
            filtered_services = [self._translate_missing_texts(service) for service in filtered_services]
        filtered_services = [Service(**service) for service in filtered_services]
        if include_channels:
            service_ids = [ser.id for ser in filtered_services]
            found_channels = list(
                self.mongo_client.service_db.channels.find({"serviceIds": {"$in": service_ids}}))
            found_channels = [ServiceChannel(**channel) for channel in found_channels]
            for service in filtered_services:
                ser_channels = [cha for cha in found_channels if cha.serviceIds is not None and (service.id in cha.serviceIds)]
                res = res + [{'service': service, 'channels': ser_channels}]
        else:
            res = [{'service': ser} for ser in filtered_services]
        return(res)

    def _get_service(self, service_id: str, translate_missing_texts: bool = False) -> Service:
        found_services = list(
            self.mongo_client.service_db.services.find({"id": service_id}))
        found_services = [self._fill_translation_indicators(service) for service in found_services]
        if translate_missing_texts:
            found_services = [self._translate_missing_texts(service) for service in found_services]
        found_services = [Service(**service) for service in found_services]
        filtered_services = [
            service for service in found_services if service.id == service_id]
        if len(filtered_services) > 0:
            return(filtered_services[0])
        else:
            return(None)
        
    def _get_service_ids_by_ptv_ids(self, service_ptv_ids: list) -> list:
        if service_ptv_ids is not None and len(service_ptv_ids) > 0:
            found_services = []
            found_services_list = list(
                self.mongo_client.service_db.services.find({"id": {"$in": service_ptv_ids }}))
            for s_id in service_ptv_ids:
                ser = [service for service in found_services_list if service.get('id') == s_id]
                found_services = found_services + ser
            service_ids = [service.get('id') for service in found_services if service.get('id') is not None] # Check is here for testing purpose
            return(service_ids)
        else:
            return([])

    def _get_all_service_channels(self) -> list:
        all_channels = list(self.mongo_client.service_db.channels.find())
        all_channels = [ServiceChannel(**channel) for channel in all_channels]
        return(all_channels)

    def _get_service_channels_by_service_id(self, service_id: str) -> list:
        found_channels = list(
            self.mongo_client.service_db.channels.find({"serviceIds": service_id}))
        found_channels = [ServiceChannel(**channel)
                          for channel in found_channels]

        if len(found_channels) > 0:
            return(found_channels)
        else:
            all_service_ids = [cl.get('id') for cl in self.classifications]
            if service_id in all_service_ids:
                return([])
            else:
                return(None)


    def _get_policy_filters(self) -> dict:
        policies_query = self.mongo_client.bf.core_policies.find()
        policies = list(policies_query)
        if policies is not None and len(policies) > 0 and 'policies' in policies[0]:
            policies_text = policies[0]['policies']
            splitted = policies_text.split('\n')
            splitted = [el.strip() for el in splitted]
            dis_trigger_text = [
                el for el in splitted if 'disambiguation_trigger' in el]
        else:
            dis_trigger_text = []
            splitted = []
        if len(dis_trigger_text) > 0:
            dis_trigger_splitted = dis_trigger_text[0].split(': ')
            if len(dis_trigger_splitted) == 2:
                dis_filter = dis_trigger_splitted[1].replace("'", "")
                matches = re.findall(pattern=r'(\$\d+)', string=dis_filter)
                for match in matches:
                    match_number = match[1:]
                    match_element = 'confidences[{}]'.format(str(match_number))
                    dis_filter = dis_filter.replace(match, match_element)
            else:
                dis_filter = 'False'
        else:
            dis_filter = 'False'

        def dis_func(confidences): return eval(dis_filter)

        fallback_trigger_text = [
            el for el in splitted if 'fallback_trigger' in el]
        if len(fallback_trigger_text) > 0:
            fallback_trigger_splitted = fallback_trigger_text[0].split(': ')
            if len(fallback_trigger_splitted) == 2:
                fallback_filter_threshold = fallback_trigger_splitted[1].replace(
                    "'", "").strip()
            else:
                fallback_filter_threshold = '0'
        else:
            fallback_filter_threshold = '0'

        def fallback_func(confidences): return confidences[0] < eval(
            fallback_filter_threshold)

        funcs = {"disambiguation": dis_func, "fallback": fallback_func}
        return(funcs)

    def _get_conversation_by_id(self, conversation_id: str) -> dict:
        conversation_query = self.mongo_client.bf.conversations.find(
            {'_id': conversation_id})
        conversation = list(conversation_query)
        if len(conversation) == 1:
            return(conversation[0])
        else:
            return None

    def _get_activities_by_conversation(self, conversation_id: str) -> dict:
        activities_query = self.mongo_client.bf.activity.find(
            {'conversation_id': conversation_id})
        activities = list(activities_query)
        return(activities)

    def _get_service_ids_by_intent_name(self, intent_name: str) -> dict:
        if intent_name is not None and type(intent_name) == str:
            intent_to_service = list(self.mongo_client.service_db.intent_to_services.find({}))
            intent_to_service = [intent_to_service_el for intent_to_service_el in intent_to_service if intent_to_service_el.get('intent') is not None and intent_to_service_el.get('intent').lower() == intent_name.lower()]
        else:
            intent_to_service = []

        services = []
        ptv_services = []
        text = None
        classes = None
        priorization = None
        if intent_to_service is not None and len(intent_to_service) > 0:
            text = intent_to_service[0].get('intent_text')
            priorization = intent_to_service[0].get('intent_priorization')
            classes = intent_to_service[0].get('intent_service_classes')
            services = intent_to_service[0].get('services') if intent_to_service[0].get('services') is not None else []
            ptv_services = intent_to_service[0].get('ptv_services') if intent_to_service[0].get('ptv_services') is not None else []

        # Map PTV IDs to generic IDs
        ptv_service_ids = self._get_service_ids_by_ptv_ids(ptv_services)
        services = list(dict.fromkeys(services + ptv_service_ids))

        return({'services': services, 'intent_text': text, 'intent_service_classes': classes, 'intent_priorization': priorization})
    
    def _fill_translation_indicators(self, service_orig: dict) -> dict:
        languages = ['fi', 'en', 'sv']
        service = copy.deepcopy(service_orig)
        service["nameAutoTranslated"] = {"fi": False, "en": False, "sv": False}
        for language in languages:
            for desc in service["descriptions"][language]:
                desc["autoTranslated"] = False
        return(service)
          
    def _translate_missing_texts(self, service_orig: dict) -> dict:
        translated = False
        service = copy.deepcopy(service_orig)
        languages = ['en', 'sv']
        for language in languages:
            
            if not service.get('name').get(language):
                name_translated = self.translation_dict[language].get(service.get('name').get('fi'))
                service['name'][language] = name_translated
                service["nameAutoTranslated"][language] = True
                
            lang_desc = [desc["value"] for desc in service.get('descriptions').get(language) if desc["value"] is not None and desc["type"] == "Description"]
            if len(lang_desc) == 0:
                fi_desc = [desc["value"] for desc in service.get('descriptions').get('fi')
                           if desc["value"] is not None and desc["type"] == "Description"]
                descs_translated = [self.translation_dict[language].get(fi_desc_el) for fi_desc_el in fi_desc]
                descs_translated = [{"value":desc, "type": "Description", "autoTranslated": True} for desc in descs_translated if desc is not None]
                service['descriptions'][language] = service['descriptions'][language] + descs_translated
                
            lang_gdesc = [gdesc["value"] for gdesc in service.get('descriptions').get(language) if gdesc["value"] is not None and gdesc["type"] == "GD_Description"]
            if len(lang_gdesc) == 0:
                fi_gdesc = [gdesc["value"] for gdesc in service.get('descriptions').get('fi')
                           if gdesc["value"] is not None and gdesc["type"] == "GD_Description"]
                gdescs_translated = [self.translation_dict[language].get(fi_gdesc_el) for fi_gdesc_el in fi_gdesc]
                gdescs_translated = [{"value":gdesc, "type": "GD_Description", "autoTranslated": True} for gdesc in gdescs_translated if gdesc is not None]
                service['descriptions'][language] = service['descriptions'][language] + gdescs_translated
                
            lang_summ = [summ["value"] for summ in service.get('descriptions').get(language) if summ["value"] is not None and summ["type"] == "Summary"]
            if len(lang_summ) == 0:
                fi_summ = [summ["value"] for summ in service.get('descriptions').get('fi')
                           if summ["value"] is not None and summ["type"] == "Summary"]
                summs_translated = [self.translation_dict[language].get(fi_summ_el) for fi_summ_el in fi_summ]
                summs_translated = [{"value":summ, "type": "Summary", "autoTranslated": True} for summ in summs_translated if summ is not None]
                service['descriptions'][language] = service['descriptions'][language] + summs_translated
                
            lang_gsumm = [gsumm["value"] for gsumm in service.get('descriptions').get(language) if gsumm["value"] is not None and gsumm["type"] == "GD_Summary"]
            if len(lang_gsumm) == 0:
                fi_gsumm = [gsumm["value"] for gsumm in service.get('descriptions').get('fi')
                           if gsumm["value"] is not None and gsumm["type"] == "GD_Summary"]
                gsumms_translated = [self.translation_dict[language].get(fi_gsumm_el) for fi_gsumm_el in fi_gsumm]
                gsumms_translated = [{"value":gsumm, "type": "GD_Summary", "autoTranslated": True} for gsumm in gsumms_translated if gsumm is not None]
                service['descriptions'][language] = service['descriptions'][language] + gsumms_translated
                
        return(service)
       
        
        

