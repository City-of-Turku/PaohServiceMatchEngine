import os
import logging
import math
import heapq
from collections import OrderedDict
from typing import Tuple
from .db import ServiceMatcherDB
import numpy as np
import requests
from fastapi import HTTPException


class FreeTextRecommender():
    """
    A class for free text service recommendation of service matcher

    Args
    ----------
    service_matcher_db : ServiceMatcherDB
        ServiceMatcher's MongoDB client where service data is stored

    Methods
    -------
    recommend_services(text: str, municipalities: list, life_events: list, service_classes: list, match_service_classes: bool, top_k: int, score_threshold: float, text_recommender="all")
        Recommend services by free text and different filters

    recommend_service_classes(text: str, top_k: int)
        Recommend service classes by free text

    """

    def __init__(self, service_matcher_db: ServiceMatcherDB) -> None:
        self.db = service_matcher_db

    def _nlp_vectorize_text(self, text: str) -> list:
        body = {'text': text}
        r = requests.post(
            os.environ['NLP_VECTORIZER_HOST']+'/vectorize', json=body)
        if r.status_code != 200:
            logging.error(r.text)
            raise HTTPException(status_code=500, detail=r.text)
        text_vector = r.json()['vector']
        return(text_vector)

    def _get_service_vectors_and_filters(self, vector: list, municipalities: list, life_events: list, service_classes: list, match_service_classes: bool) -> Tuple[list, list]:
        if match_service_classes:
            n_classes = len(self.db._get_all_service_classes())
            top_70_percent_classes = math.ceil(0.7*n_classes)

            service_class_scores, _ = self._get_service_class_scores_by_nlp_search(
                vector)
            top_k_service_class_scores = self._get_top_k_scores(
                service_class_scores, top_70_percent_classes)

            service_class_recommendations = list(
                top_k_service_class_scores.keys())
            filtered_service_class_recommendations = list(
                set(service_classes).intersection(set(service_class_recommendations)))
            service_desc_vectors = self.db._get_service_desc_vectors(
                filtered_service_class_recommendations, municipalities, life_events)
        else:
            service_desc_vectors = self.db._get_service_desc_vectors(
                service_class_codes_filter=service_classes, municipality_ids_filter=municipalities, life_events_filter=life_events)

        filter_service_ids = [service["id"]
                              for service in service_desc_vectors]

        return service_desc_vectors, filter_service_ids

    def _get_service_class_scores_by_nlp_search(self, vector: list) -> Tuple[dict, dict]:
        service_class_vectors = self.db._get_service_class_vectors()
        vectors_array = np.array([service_class["vector"]
                                 for service_class in service_class_vectors])
        if len(vectors_array.shape) == 1:
            vectors_array.shape = (0, len(vector))
        dot_products = np.dot(
            np.array(vector), vectors_array.T).tolist()

        scores = {service_class_vectors[idx]["code"]: dot_products[idx] for idx in range(
            len(dot_products))}
        names = {service_class["code"]: service_class["name"]
                 for service_class in service_class_vectors}
        return(scores, names)

    def _get_service_scores_by_lexical_text_search(self, text: str, language: str, filter_service_ids: list) -> dict:
        # set top_k to 0 to get scores for all services
        body = {'text': text, 'language': language,'top_k': 0}
        r = requests.post(
            os.environ['LEXICAL_TEXT_SEARCH_HOST']+'/searchServices', json=body)
        if r.status_code != 200:
            logging.error(r.text)
            raise HTTPException(status_code=500, detail=r.text)
        services = r.json()['services']

        scores = {service["id"]: service["score"]
                  for service in services if service["id"] in filter_service_ids}
        return(scores)

    def _get_service_scores_by_nlp_search(self, vector: list, service_desc_vectors: list) -> dict:
        vectors_array = np.array([service["vector"]
                                 for service in service_desc_vectors])
        if len(vectors_array.shape) == 1:
            vectors_array.shape = (0, len(vector))

        # get cosine similarity between query vector and service vectors
        dot_products = np.dot(
            np.array(vector), vectors_array.T).tolist()

        scores = {service_desc_vectors[idx]["id"]: dot_products[idx]
                  for idx in range(len(dot_products))}
        return (scores)

    def _combine_nlp_and_lexical_scores(self, nlp_scores: dict, lexical_scores: dict) -> dict:
        combined_scores = {}

        top_10_nlp = self._get_top_k_scores(nlp_scores, 10)
        top_10_lexical = self._get_top_k_scores(lexical_scores, 10)

        for service_id in set(nlp_scores) | set(lexical_scores):
            nlp_score = nlp_scores.get(service_id, 0.01) * 100
            lexical_score = lexical_scores.get(service_id, 1) if lexical_scores.get(service_id, 1) > 0 else 1

            if service_id in top_10_nlp:
                nlp_score = nlp_score * nlp_score
            if service_id in top_10_lexical and lexical_score >= 55:
                lexical_score = lexical_score * lexical_score

            combined_scores[service_id] = nlp_score * lexical_score

        return combined_scores

    def _get_top_k_scores(self, scores: dict, top_k: int, score_threshold: float = 0.0) -> OrderedDict:
        if len(scores) < top_k:
            top_k = len(scores)

        top_k_keys = heapq.nlargest(top_k, scores, key=scores.get)
        return OrderedDict((key, scores[key]) for key in top_k_keys if scores[key] >= score_threshold)

    def recommend_services(self, text: str, municipalities: list, life_events: list, service_classes: list, match_service_classes: bool, top_k: int, score_threshold: float, text_recommender="all", language=None) -> dict:
        if not language:
            language = "fi"
        # Don't use BM25 if language is English or Swedish
        #if language in ["sv", "en"] and text_recommender == "all":
        #    text_recommender_checked = "nlp"
        #else:
        #    text_recommender_checked = text_recommender
        text_recommender_checked = text_recommender
            
        # for filtering service classes, let's only use NLP matching so we need to vectorize text anyway even though only lexical service search were used
        vector = self._nlp_vectorize_text(text)
        service_desc_vectors, filter_service_ids = self._get_service_vectors_and_filters(
            vector, municipalities, life_events, service_classes, match_service_classes)

        if text_recommender_checked == "lexical":
            lexical_scores = self._get_service_scores_by_lexical_text_search(
                text, language, filter_service_ids)
            top_k_scores = self._get_top_k_scores(
                lexical_scores, top_k, score_threshold)
        elif text_recommender_checked == "nlp":
            nlp_scores = self._get_service_scores_by_nlp_search(
                vector, service_desc_vectors)
            top_k_scores = self._get_top_k_scores(
                nlp_scores, top_k, score_threshold)
        else:
            lexical_scores = self._get_service_scores_by_lexical_text_search(
                text, language, filter_service_ids)
            nlp_scores = self._get_service_scores_by_nlp_search(
                vector, service_desc_vectors)
            combined_scores = self._combine_nlp_and_lexical_scores(
                nlp_scores, lexical_scores)
            top_k_scores = self._get_top_k_scores(
                combined_scores, top_k, score_threshold)

        return top_k_scores

    def recommend_service_classes(self, text: str, top_k: int) -> list:
        vector = self._nlp_vectorize_text(text)
        service_class_scores, service_class_names = self._get_service_class_scores_by_nlp_search(
            vector)
        top_k_service_class_scores = self._get_top_k_scores(
            service_class_scores, top_k)
        return [{"name": service_class_names[class_code], "service_class_code": class_code,
                 "score": top_k_service_class_scores[class_code]} for class_code in top_k_service_class_scores]
