import logging
import re
import numpy as np
from typing import Optional
from .models import *
PROVINCE_CODES = ["02"]

class ServiceMatcherUtils():
    """
    A class for various auxillary functions related to service matching


    """

    def __init__(self) -> None:
        pass

    def _filter_service_data_by_municipality(self, service: Service, municipality_ids: list) -> list:
        languages = ['en', 'fi', 'sv']
        service_filtered = service.copy(deep=True)
        for language in languages:
            service_areas = service_filtered.areas[language]
            if len(service_areas) > 0:
                area_municipalities = [area for area in service_areas if area.get(
                    'type') == 'Municipality' and area.get('code') in municipality_ids]
                area_provinces = [area for area in service_areas if (area.get(
                    'type') == 'Province' or area.get('type') == 'Region') and area.get('code') in PROVINCE_CODES]
                other_area_elements = [area for area in service_areas if area.get(
                    'type') != 'Province' and area.get('type') != 'Municipality' and area.get('type') != 'Region']
                filtered_areas = area_municipalities + area_provinces + other_area_elements
                service_filtered.areas[language] = filtered_areas
        return(service_filtered)

    def _filter_service_channel_data_by_municipality(self, channel: ServiceChannel, municipality_ids: list) -> list:
        languages = ['en', 'fi', 'sv']
        channel_filtered = channel.copy(deep=True)
        for language in languages:
            channel_areas = channel_filtered.areas[language]
            channel_addresses = channel_filtered.addresses[language]
            if len(channel_areas) > 0:
                area_municipalities = [area for area in channel_areas if area.get(
                    'type') == 'Municipality' and area.get('code') in municipality_ids]
                area_provinces = [area for area in channel_areas if (area.get(
                    'type') == 'Province' or area.get('type') == 'Region') and area.get('code') in PROVINCE_CODES]
                other_area_elements = [area for area in channel_areas if area.get(
                    'type') != 'Province' and area.get('type') != 'Municipality' and area.get('type') != 'Region']
                filtered_areas = area_municipalities + area_provinces + other_area_elements
                channel_filtered.areas[language] = filtered_areas
            if len(channel_addresses) > 0:
                filtered_addresses = [add for add in channel_addresses if add.get(
                    'municipalityCode') is None or add.get('municipalityCode') in municipality_ids]
                channel_filtered.addresses[language] = filtered_addresses
        return(channel_filtered)


    def _nest_form_events(self, events: list) -> list:
        nested_events = []
        form_on = False
        start_events = 0
        for event in events:
            event = event.copy()
            is_form_starting_event = ('parse_data' in event.keys() and re.search('service_search$', event['parse_data']['intent']['name']) is not None) or (event.get('name') is not None and re.search('_form$', event.get('name')) is not None)
            is_form_ending_event = (event.get('event') == 'active_loop' and event.get('name') is None) or event.get('event') == 'action_execution_rejected'
            if is_form_starting_event and not form_on:
                form_on = True
                start_events =   start_events + 1
                event['form_events'] = []
                nested_events.append(event)
            elif form_on:
                nested_events[-1]['form_events'].append(event)
                if is_form_ending_event:
                    form_on = False
            elif not form_on:
                nested_events.append(event)
            else:
                raise Exception("Something went wrong, event has not type")
        return(nested_events)


    def _get_municipality_ids_by_names(self, municipality_names: list, all_municipalities: list) -> list:
        matching_municipality_ids = []
        if municipality_names is not None and len(municipality_names) > 0:
            input_names_lower = [mun_name.lower()
                                 for mun_name in municipality_names]
            for municipality in all_municipalities:
                municipality_real_names_lower = [
                    mun_name_l.lower() for mun_name_l in list(municipality.get('name').values())]
                is_match = any(
                    [True for input_name_lower in input_names_lower if input_name_lower in municipality_real_names_lower])
                if is_match:
                    matching_municipality_ids.append(municipality.get('id'))
        # If no info, don't limit by municipalities
        if len(matching_municipality_ids) == 0:
            for municipality in all_municipalities:
                matching_municipality_ids.append(municipality.get('id'))
        return(matching_municipality_ids)

    def _check_life_events(self, life_events: list, all_life_events: list) -> list:
        filtered_life_events = [
            le for le in life_events if le in all_life_events]
        # If no info, don't limit by life events
        if len(filtered_life_events) == 0:
            filtered_life_events = all_life_events
        return(filtered_life_events)

    def _check_service_classes(self, service_classes: list, all_service_classes: list) -> list:
        all_service_classes = [sc.code for sc in all_service_classes]
        filtered_service_classes = [
            sc for sc in service_classes if sc in all_service_classes]
        # If no info, don't limit by service classes
        if len(filtered_service_classes) == 0:
            filtered_service_classes = all_service_classes
        return(filtered_service_classes)


    def _swap(self, list_1: list, i: int, j: int) -> list:
        list_1[i], list_1[j] = list_1[j], list_1[i]
        return(list_1)


    def _get_service_classes_from_intent_name(self, intent: Optional[str]) -> list:
        if intent is not None:
            service_class_regex = re.compile(
                'p\d{1,2}(?:[.]\d{1,2}){0,1}', re.IGNORECASE)
            found_service_classes = re.findall(service_class_regex, intent)
            if len(found_service_classes) > 0:
                found_service_classes = list(set([found_service_class.upper(
                ) for found_service_class in found_service_classes]))
            return (found_service_classes)
        else:
            return([])

    def _get_life_events_from_intent_name(self, intent: Optional[str]) -> list:
        if intent is not None:
            life_event_regex = re.compile(
                'ke\d{1,2}(?:[.]\d{1,2}){0,1}', re.IGNORECASE)
            found_life_events = re.findall(life_event_regex, intent)
            if len(found_life_events) > 0:
                found_life_events = list(set([found_life_event.upper()
                                              for found_life_event in found_life_events]))
            return (found_life_events)
        else:
            return([])
