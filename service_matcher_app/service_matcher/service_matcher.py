import re
from pymongo import MongoClient
from .models import *
from .utils import *
from .db import *
from .free_text_recommender import *
from typing import Optional

class ServiceMatcher():
    """
    A class used to provide service match API functions to create service recommendations and fetch and filter data

    Args
    ----------
    mongo_client : MongoClient (default None)
        MongoDB client where service data is stored


    Methods
    -------
    get_services_filtered( serviceQuery: ServiceQuery )
        Get services filtered by municipality, service class and life event filters

    get_service_recommendations_by_conversation( conversation_id: str, serviceRecommendConversationQuery: ServiceRecommendConversationQuery )
        Get service recommendations by conversation ID

    get_service_recommendations_by_intent( conversation_id: str, serviceRecommendIntentQuery: ServiceRecommendIntentQuery )
        Get service recommendations by intent name

    get_service_recommendations_by_intentAndOptions( conversation_id: str, serviceRecommendIntentAndOptionsQuery: ServiceRecommendIntentAndOptionsQuery )
        Get service recommendations by intent name and options defined in database

    get_service_recommendations( serviceRecommendQuery: ServiceRecommendQuery )
        Get service recommendations by free text parameters given to the function

    get_service_class_recommendations_by_conversation( conversation_id: str, serviceClassRecommendConversationQuery: ServiceClassRecommendConversationQuery )
        Get service class recommendations by conversation ID

    get_service_class_recommendations( serviceClassRecommendQuery: ServiceClassRecommendQuery )
        Get service class recommendations by free text

    """

    def __init__(self, mongo_client: Optional[MongoClient] = None) -> None:
        self.db = ServiceMatcherDB(mongo_client)
        self.utils = ServiceMatcherUtils()
        self.free_text_recommender = FreeTextRecommender(self.db)
            
    def update_desc_vectors(self) -> None:
        self.db._update_desc_vectors()
        self.db._update_translations()

    def get_service(self, service_id: str, translate_missing_texts: bool = False) -> Service:
        return(self.db._get_service(service_id, translate_missing_texts=translate_missing_texts))

    def get_all_services(self, translate_missing_texts: bool = False) -> list:
        return(self.db._get_all_services(translate_missing_texts=translate_missing_texts))

    def get_all_service_channels(self) -> list:
        return(self.db._get_all_service_channels())

    def get_service_channels_by_service_id(self, service_id: str) -> list:
        return(self.db._get_service_channels_by_service_id(service_id))

    def get_all_service_classes(self) -> list:
        return(self.db._get_all_service_classes())

    def get_all_services_filtered(self, serviceQuery: ServiceQuery) -> list:
        
        # Set up values from query
        if len(serviceQuery.municipalities) > 0:
            municipalities = serviceQuery.municipalities
        else:
            municipalities = []
        if len(serviceQuery.life_events) > 0:
            life_events = serviceQuery.life_events
        else:
            life_events = []
        if len(serviceQuery.service_classes) > 0:
            service_classes = serviceQuery.service_classes
        else:
            service_classes = []
        priorization = serviceQuery.priorization

        # Get municipality filter
        municipality_ids = self.utils._get_municipality_ids_by_names(municipalities, self.db._get_all_municipalities())

        # Get life event filter
        life_events = self.utils._check_life_events(life_events, self.db._get_all_life_event_codes())

        # Get service class filter
        service_classes = self.utils._check_service_classes(service_classes, self.db._get_all_service_classes())
        
        filtered_ids = self.db._get_service_ids_by_filters(
            service_class_codes_filter=service_classes, municipality_ids_filter=municipality_ids, life_events_filter=life_events)
        
        filtered_services = self.db._get_services_by_ids(filtered_ids, include_channels=True, translate_missing_texts=serviceQuery.translate_missing_texts)
        
        # Split by region vs no region
        services_with_area = [ser for ser in filtered_services if ser.get("service").areas["fi"] is not None and len(ser.get("service").areas["fi"]) > 0]
        services_without_area = [ser for ser in filtered_services if not (ser.get("service").areas["fi"] is not None and len(ser.get("service").areas["fi"]) > 0)]
        
        # Sort groups by service class existence
        services_with_area.sort(key = lambda service: service.get("service").serviceClasses["fi"] is not None and len(service.get("service").serviceClasses["fi"]) > 0)
        services_with_area.reverse()
        services_without_area.sort(key = lambda service: service.get("service").serviceClasses["fi"] is not None and len(service.get("service").serviceClasses["fi"]) > 0)
        services_without_area.reverse()
        if priorization == "local":
            filtered_services = services_with_area + services_without_area
        else:
            filtered_services = services_without_area + services_with_area

        # Limit number of services
        filtered_services = filtered_services[0:serviceQuery.limit_k]
        
        final_services = []
        if len(serviceQuery.municipalities) > 0:
            if serviceQuery.include_channels:
                final_services = [{
                "service":self.utils._filter_service_data_by_municipality(
                    service.get("service"), municipality_ids),
                "channels": [self.utils._filter_service_channel_data_by_municipality(cha, municipality_ids) for cha in service.get("channels")] if (service.get("channels") is not None) else []}
                for service in filtered_services]
            else:
                final_services = [{
                "service":self.utils._filter_service_data_by_municipality(
                    service.get("service"), municipality_ids)}
                for service in filtered_services]
        else:
            final_services = filtered_services       

        return(final_services)


    def _get_conversation_info(self, conversation_id: str) -> dict:

        conversation = self.db._get_conversation_by_id(conversation_id)
        policy_filters = self.db._get_policy_filters()
        disambiguation_filter = policy_filters.get('disambiguation')
        fallback_filter = policy_filters.get('fallback')
        slots = {}
        events = []
        all_intents = []
        intent_events = []
        if conversation is not None:
            if conversation.get('tracker').get('events') is not None:
                events = conversation.get('tracker').get('events')
                # Remove intent reference if the bot is inferring disambiguation or fallback
                events_mod = []
                for event in events:
                    if 'parse_data' in event.keys() and 'intent_ranking' in event['parse_data'].keys() and \
                            len(event['parse_data']['intent_ranking']) > 1 and \
                            disambiguation_filter([el['confidence'] for el in event['parse_data']['intent_ranking']]):
                        event['parse_data']['intent'] = {
                            'name': 'disambiguation'}
                    elif 'parse_data' in event.keys() and 'intent_ranking' in event['parse_data'].keys() and \
                            len(event['parse_data']['intent_ranking']) > 0 and \
                            fallback_filter([el['confidence'] for el in event['parse_data']['intent_ranking']]):
                        event['parse_data']['intent'] = {'name': 'fallback'}
                    else:
                        pass
                    events_mod.append(event)
                events = events_mod

            # Reverse action_execution_rejected and its' previous events order
            is_excecution_rejected = [
                evt.get('event') == 'action_execution_rejected' for evt in events]
            rejected_indices = [i for i, j in enumerate(
                is_excecution_rejected) if j == True]
            for ix in rejected_indices:
                events = self.utils._swap(events, ix - 1, ix)
            
            # Nest form events
            events = self.utils._nest_form_events(events)
            
            # Slots
            if conversation.get('tracker').get('slots') is not None:
                slots = conversation.get('tracker').get('slots')
                
            # Filter in events that are related to user intent or search form intents, skip disambiguations, forms not related to intents etc.
            intent_events = [event for event in events if
                          'parse_data' in event.keys() and 'intent' in event.get('parse_data').keys() and \
                          (re.search('service_search$', event['parse_data']['intent']['name']) is not None or len(self.utils._get_service_classes_from_intent_name(event['parse_data']['intent']['name'])) > 0 or len(self.utils._get_life_events_from_intent_name(event['parse_data']['intent']['name'])) > 0)]

            # Intent names
            all_intents = [ev.get('parse_data').get('intent').get('name') for ev in intent_events]

        # Handle life events' recognition
        if slots is not None and 'life_event' in slots.keys():
            life_events = [slots.get('life_event')]
            life_events = [le.upper()
                           for le in life_events if le is not None and type(le) == str]
            life_events = list(set(life_events))
        else:
            life_events = []
        if len(all_intents) > 0:
            intent = all_intents[-1]
            life_events = self.utils._get_life_events_from_intent_name(intent)

        # Handle service classes' recognition
        service_classes = []
        if len(all_intents) > 0:
            intent = all_intents[-1]
            service_classes = self.utils._get_service_classes_from_intent_name(
                intent)

        activities = self.db._get_activities_by_conversation(conversation_id)
        messages = []
        for activity in activities:
            text = activity.get('text')
            messages.append(text)
        conv_info = {'slots': slots,
                     'events': intent_events,
                     'intents': all_intents,
                     'messages': messages,
                     'life_events': life_events,
                     'service_classes': service_classes}
        return(conv_info)


    def _get_matching_services(self, text: list, municipalities: list, life_events: list, service_classes: list, match_service_classes: bool, top_k: int, score_threshold: float, text_recommender: str, language: str, translate_missing_texts: bool) -> list:
        scored_services = self.free_text_recommender.recommend_services(text, municipalities, life_events, service_classes, match_service_classes, top_k, score_threshold, text_recommender, language)

        services = self.db._get_services_by_ids(list(scored_services.keys()), include_channels=True, translate_missing_texts=translate_missing_texts)
        services = [ser for ser in services if ser.get("service") is not None]

        matches = [{
        "service":self.utils._filter_service_data_by_municipality(
            service.get("service"), municipalities),
        "channels": [self.utils._filter_service_channel_data_by_municipality(cha, municipalities) for cha in service.get("channels")] if (service.get("channels") is not None) else [],
        "score": scored_services.get(service.get("service").id)}
        for service in services]

        return(matches)


    def get_service_recommendations_by_conversation(self, conversation_id: str, serviceRecommendConversationQuery: ServiceRecommendConversationQuery) -> list:
        """Uses conversation info in the database"""

        # Set up values from query
        municipalities = None
        if len(serviceRecommendConversationQuery.municipalities) > 0:
            municipalities = serviceRecommendConversationQuery.municipalities
        life_events = None
        if len(serviceRecommendConversationQuery.life_events) > 0:
            life_events = serviceRecommendConversationQuery.life_events
        service_classes = None
        if len(serviceRecommendConversationQuery.service_classes) > 0:
            service_classes = serviceRecommendConversationQuery.service_classes

        conversation_info = self._get_conversation_info(conversation_id)

        # Secondly try to get them from slots if not gotten from query
        if municipalities == None:
            municipalities = [conversation_info.get('slots').get('municipality')] if (conversation_info.get(
                'slots') is not None and conversation_info.get('slots').get('municipality') is not None) else []
        if service_classes == None:
            service_classes = conversation_info.get('service_classes')
        if life_events == None:
            life_events = conversation_info.get('life_events')

        # Get municipality filter
        municipality_ids = self.utils._get_municipality_ids_by_names(municipalities, self.db._get_all_municipalities())

        # Get life event filter
        life_events = self.utils._check_life_events(life_events, self.db._get_all_life_event_codes())

        # Get service class filter
        service_classes = self.utils._check_service_classes(service_classes, self.db._get_all_service_classes())

        # Set recommendation mode
        is_free_text_search = False
        if serviceRecommendConversationQuery.mode == "search":
            is_free_text_search = True
            
            # Find out text search prefix
            form_events = [ev for ev in conversation_info.get('events') if 'form_events' in ev.keys() and 
                ('parse_data' in ev.keys() and re.search('service_search$', ev['parse_data']['intent']['name']) is not None)]
            if len(form_events) > 0:
                latest_form_events = form_events[-1]['form_events']
            else:
                latest_form_events = []
            form_name_prefixes = [re.findall(r'(.*?)service_search_form', event.get('name'))[0] for event in latest_form_events if 'name' in event.keys() and event.get('name') is not None and len(re.findall(r'(.*?)service_search_form', event.get('name'))) > 0]
            if len(form_name_prefixes) > 0:
                form_name_prefix = form_name_prefixes[0]
            else:
                form_name_prefix = ''

            # Find the slot corresponding to the search form
            search_text = conversation_info.get('slots').get(form_name_prefix + 'service_search_text') if conversation_info.get(
                'slots').get(form_name_prefix + 'service_search_text') else conversation_info.get('slots').get('service_search_text')

        is_intent_search = False
        if serviceRecommendConversationQuery.mode == "intent":
            is_intent_search = True

        is_conversation_search = False
        if serviceRecommendConversationQuery.mode == "conversation":
            is_conversation_search = True

        if serviceRecommendConversationQuery.mode == "infer":

            events = conversation_info.get('events')

            # Check if the latest intent is search intent
            search_on = (len(events) > 0) and ('form_events' in events[-1].keys() and len(events[-1]['form_events']) > 0)

            # If there was a form, find its name
            form_name_prefix = ''
            if search_on:
                fts_form_events = events[-1]['form_events']
                form_name_prefixes = [re.findall(r'(.*?)service_search_form', event.get('name'))[0] for event in fts_form_events if 'name' in event.keys() and event.get('name') is not None and len(re.findall(r'(.*?)service_search_form', event.get('name'))) > 0]
                if len(form_name_prefixes) > 0:
                    form_name_prefix = form_name_prefixes[0]

            search_text = conversation_info.get('slots').get(form_name_prefix + 'service_search_text') if conversation_info.get(
                'slots').get(form_name_prefix + 'service_search_text') else conversation_info.get('slots').get('service_search_text')

            # Infer the mode
            if (search_text is not None and search_text != '') and search_on:
                is_free_text_search = True
            elif not search_on:
                is_intent_search = True
            else:
                # If method is not one of these 2 skip recommendation
                return([])

        # Get the actual recommendations
        if is_free_text_search:
            if search_text is not None and search_text != '':
                matches = self._get_matching_services(
                    search_text, municipality_ids, life_events, service_classes, False, serviceRecommendConversationQuery.top_k, serviceRecommendConversationQuery.score_threshold, serviceRecommendConversationQuery.text_recommender, serviceRecommendConversationQuery.language, translate_missing_texts=serviceRecommendConversationQuery.translate_missing_texts)
            else:
                matches = []
            return(matches)
        elif is_conversation_search:
            user_text = ' '.join(conversation_info.get('messages'))

            if user_text is not None and user_text != '':
                matches = self._get_matching_services(
                    user_text, municipality_ids, life_events, service_classes, False, serviceRecommendConversationQuery.top_k, serviceRecommendConversationQuery.score_threshold, serviceRecommendConversationQuery.text_recommender, serviceRecommendConversationQuery.language, translate_missing_texts=serviceRecommendConversationQuery.translate_missing_texts)
            else:
                matches = []
            return(matches)

        elif is_intent_search:

            if conversation_info.get('intents') is not None and len(conversation_info.get('intents')) > 0:
                intent_info = self.db._get_service_ids_by_intent_name(conversation_info.get('intents')[-1])
                if intent_info.get('intent_text') is not None or intent_info.get('intent_service_classes') is not None:
                    intent_matches = self.get_service_recommendations_by_intent_and_options(ServiceRecommendIntentAndOptionsQuery(intent=conversation_info.get('intents')[-1],
                                                                               municipalities=municipalities,
                                                                               life_events=[],
                                                                               score_threshold=serviceRecommendConversationQuery.score_threshold,
                                                                               limit_k=serviceRecommendConversationQuery.top_k,
                                                                               translate_missing_texts=serviceRecommendConversationQuery.translate_missing_texts),
                                                                            intentInfo=intent_info)
                else:
                    intent_matches = self.get_service_recommendations_by_intent(ServiceRecommendIntentQuery(intent=conversation_info.get('intents')[-1],
                                                                               municipalities=municipalities,
                                                                               life_events=[],
                                                                               translate_missing_texts=serviceRecommendConversationQuery.translate_missing_texts),
                                                                            intentInfo=intent_info)
                intent_matches = intent_matches[0:serviceRecommendConversationQuery.top_k]
            else:
                intent_matches = []
                
            if len(intent_matches) > 0:
                # Straight intent matches found
                return(intent_matches)
            else:
                # Secondarily, just try to find services by category or life event
                intents = conversation_info.get('intents').copy()
                found_service_classes = []
                if len(intents) > 0:
                    for intent in reversed(intents):
                        found_service_classes = self.utils._get_service_classes_from_intent_name(
                            intent)
                        found_life_events = self.utils._get_life_events_from_intent_name(
                            intent)
                        if len(found_service_classes) > 0:
                            break
                        elif len(found_life_events) > 0:
                            break

                # So far only found service classes is used because life event data is not good at PTV
                if len(found_service_classes) > 0:
                    category_matches = self.get_all_services_filtered(ServiceQuery(include_channels=True,
                                                                                   municipalities=municipalities,
                                                                                   life_events=[],
                                                                                   service_classes=found_service_classes,
                                                                                   limit_k=serviceRecommendConversationQuery.top_k,
                                                                                   translate_missing_texts=serviceRecommendConversationQuery.translate_missing_texts))
                    category_matches = category_matches[0:
                                                        serviceRecommendConversationQuery.top_k]
                    return(category_matches)
                else:
                    return([])
        else:
            raise Exception("No mode found, something went wrong")
            
    def get_service_recommendations_by_intent(self, serviceRecommendIntentQuery: ServiceRecommendIntentQuery, intentInfo: Optional[dict] = None) -> list:
        
        # Get municipality filter
        municipality_ids = self.utils._get_municipality_ids_by_names(
            serviceRecommendIntentQuery.municipalities, self.db._get_all_municipalities())

        # Get life event filter
        life_events = self.utils._check_life_events(
            serviceRecommendIntentQuery.life_events, self.db._get_all_life_event_codes())

        # Get service class filter
        service_classes = self.utils._check_service_classes(
            serviceRecommendIntentQuery.service_classes, self.db._get_all_service_classes())

        if not intentInfo:
            intent_recommendation_obj = self.db._get_service_ids_by_intent_name(serviceRecommendIntentQuery.intent)
        else:
            intent_recommendation_obj = intentInfo
        service_ids = intent_recommendation_obj.get("services")
        
        if len(service_ids) > 0:
            # Straight intent matches found
            filtered_ids = self.db._get_service_ids_by_filters(
                service_class_codes_filter=service_classes, municipality_ids_filter=municipality_ids, life_events_filter=life_events)

            services = self.db._get_services_by_ids(service_ids, include_channels=True, translate_missing_texts=serviceRecommendIntentQuery.translate_missing_texts)
            services = [ser for ser in services if ser.get("service") is not None and ser.get("service").id in filtered_ids]
            intent_matches = [{
            "service":self.utils._filter_service_data_by_municipality(
                service.get("service"), municipality_ids),
            "channels": [self.utils._filter_service_channel_data_by_municipality(cha, municipality_ids) for cha in service.get("channels")] if (service.get("channels") is not None) else []}
            for service in services]

            return(intent_matches)
        else:
            return([])


    def get_service_recommendations_by_intent_and_options(self, serviceRecommendIntentAndOptionsQuery: ServiceRecommendIntentAndOptionsQuery, intentInfo: Optional[dict] = None) -> list:
        
        # Get municipality filter
        municipality_ids = self.utils._get_municipality_ids_by_names(
            serviceRecommendIntentAndOptionsQuery.municipalities, self.db._get_all_municipalities())

        # Get life event filter
        life_events = self.utils._check_life_events(
            serviceRecommendIntentAndOptionsQuery.life_events, self.db._get_all_life_event_codes())
        
        # Get all_service_classes
        all_service_classes = [sc.code for sc in self.db._get_all_service_classes()]

        if not intentInfo:
            intent_recommendation_obj = self.db._get_service_ids_by_intent_name(serviceRecommendIntentAndOptionsQuery.intent)
        else:
            intent_recommendation_obj = intentInfo
        service_ids = intent_recommendation_obj.get("services")
        text = serviceRecommendIntentAndOptionsQuery.need_text
        if not text:
            text = intent_recommendation_obj.get("intent_text")
        service_classes_0 = serviceRecommendIntentAndOptionsQuery.service_classes
        if not service_classes_0:
            service_classes_0 = intent_recommendation_obj.get("intent_service_classes")
        priorization = serviceRecommendIntentAndOptionsQuery.priorization
        if not priorization:
            priorization = intent_recommendation_obj.get("intent_priorization")

        # Check service classes
        use_service_class_filter = True
        if service_classes_0 is None:
            service_classes_0 = []
            use_service_class_filter = False
        service_classes = self.utils._check_service_classes(service_classes_0, self.db._get_all_service_classes())
        if len(service_classes) > len(service_classes_0):
            use_service_class_filter = False

        # If text is present priorization parameter isn't relevant
        if text:
            priorization = None

        combined_matches = []
        intent_matches = []
        # Fetch services by intent
        if len(service_ids) > 0:
            # Straight intent matches found
            filtered_ids = self.db._get_service_ids_by_filters(
                service_class_codes_filter=all_service_classes, municipality_ids_filter=municipality_ids, life_events_filter=life_events)

            services = self.db._get_services_by_ids(service_ids, include_channels=True, translate_missing_texts=serviceRecommendIntentAndOptionsQuery.translate_missing_texts)
            services = [ser for ser in services if ser.get("service") is not None and ser.get("service").id in filtered_ids]
            intent_matches = [{
            "service":self.utils._filter_service_data_by_municipality(
                service.get("service"), municipality_ids),
            "channels": [self.utils._filter_service_channel_data_by_municipality(cha, municipality_ids) for cha in service.get("channels")] if (service.get("channels") is not None) else []}
            for service in services]
            combined_matches = intent_matches

        if text is not None:
            text_matches = []
            # Fetch services by text
            if text is not None and text != '':
                if use_service_class_filter:
                    text_matches = self._get_matching_services(
                        text, municipality_ids, life_events, service_classes, False, serviceRecommendIntentAndOptionsQuery.limit_k + len(intent_matches), serviceRecommendIntentAndOptionsQuery.score_threshold, serviceRecommendIntentAndOptionsQuery.text_recommender, serviceRecommendIntentAndOptionsQuery.language, translate_missing_texts=serviceRecommendIntentAndOptionsQuery.translate_missing_texts)
                else:
                    text_matches = self._get_matching_services(
                        text, municipality_ids, life_events, all_service_classes, False, serviceRecommendIntentAndOptionsQuery.limit_k + len(intent_matches), serviceRecommendIntentAndOptionsQuery.score_threshold, serviceRecommendIntentAndOptionsQuery.text_recommender, serviceRecommendIntentAndOptionsQuery.language, translate_missing_texts=serviceRecommendIntentAndOptionsQuery.translate_missing_texts)                    
            # Filter out duplicates
            filtered_text_matches = [ser for ser in text_matches if not (ser.get('service').id in service_ids)]
            filtered_text_matches = filtered_text_matches[0:serviceRecommendIntentAndOptionsQuery.limit_k]
            combined_matches = combined_matches + filtered_text_matches

        elif use_service_class_filter: 
            class_matches = []
            if priorization not in ["national", "local"]:
                priorization = "local"
            # Fetch services by class
            if service_classes is not None and len(service_classes) > 0:
                class_matches = self.get_all_services_filtered(ServiceQuery(include_channels=True,
                                                                               priorization=priorization,
                                                                               municipalities=serviceRecommendIntentAndOptionsQuery.municipalities,
                                                                               life_events=life_events,
                                                                               service_classes=service_classes,
                                                                               limit_k=serviceRecommendIntentAndOptionsQuery.limit_k + len(intent_matches),
                                                                               translate_missing_texts=serviceRecommendIntentAndOptionsQuery.translate_missing_texts))

            # Filter out duplicates
            filtered_class_matches = [ser for ser in class_matches if not (ser.get('service').id in service_ids)]
            filtered_class_matches = filtered_class_matches[0:serviceRecommendIntentAndOptionsQuery.limit_k]
            combined_matches = combined_matches + filtered_class_matches


        return(combined_matches)

              
    def get_service_recommendations(self, serviceRecommendQuery: ServiceRecommendQuery) -> list:

        # Get municipality filter
        municipality_ids = self.utils._get_municipality_ids_by_names(
            serviceRecommendQuery.municipalities, self.db._get_all_municipalities())

        # Get life event filter
        life_events = self.utils._check_life_events(
            serviceRecommendQuery.life_events, self.db._get_all_life_event_codes())

        # Get service class filter
        service_classes = self.utils._check_service_classes(
            serviceRecommendQuery.service_classes, self.db._get_all_service_classes())
            
        if serviceRecommendQuery.need_text is not None and serviceRecommendQuery.need_text != '':
            matches = self._get_matching_services(
                serviceRecommendQuery.need_text, municipality_ids, life_events, service_classes, False, serviceRecommendQuery.top_k, serviceRecommendQuery.score_threshold, serviceRecommendQuery.text_recommender, serviceRecommendQuery.language, serviceRecommendQuery.translate_missing_texts)
        else:
            matches = []
        return(matches)

    def get_service_class_recommendations_by_conversation(self, conversation_id: str, serviceClassRecommendConversationQuery: ServiceClassRecommendConversationQuery) -> list:

        conversation_info = self._get_conversation_info(conversation_id)

        user_text = ' '.join(conversation_info.get('messages'))
        if user_text is not None and user_text != '':
            matches = self.free_text_recommender.recommend_service_classes(
                user_text, serviceClassRecommendConversationQuery.top_k)
        else:
            matches = []
        return(matches)

    def get_service_class_recommendations(self, serviceClassRecommendQuery: ServiceClassRecommendQuery) -> list:
        if serviceClassRecommendQuery.need_text is not None and serviceClassRecommendQuery.need_text != '':
            matches = self.free_text_recommender.recommend_service_classes(
                serviceClassRecommendQuery.need_text, serviceClassRecommendQuery.top_k)
        else:
            matches = []
        return(matches)
