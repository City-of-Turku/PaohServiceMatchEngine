from .models import *
from .db import LexicalTextSearchDB
from .stopwords import stopwords
from rank_bm25 import BM25Plus
import nltk
from nltk.tokenize import word_tokenize
from nltk import ngrams
import numpy as np
import re

SUPPORTED_LANGUAGES = {'fi': 'finnish', 'en': 'english', 'sv': 'swedish'}


class LexicalTextSearch():
    """
    A class used to search text using BM25.

    Args
    ----------
    db : LexicalTextSearchDB (default None)
        Database connection to use

    Methods
    -------
    search_services(ServiceSearchQuery: ServiceSearchQuery)
        Returns list of found services
    """

    def __init__(self, db: Optional[LexicalTextSearchDB] = None) -> None:
        # download nltk punkt
        nltk.download('punkt')

        self.tokenized_service_texts = []
        if db is None:
            self.db = LexicalTextSearchDB(
                supported_languages=list(SUPPORTED_LANGUAGES.keys()))
        else:
            self.db = db
        self.create_bm25(CreateBM25())

    def _tokenize_service_texts(self) -> None:
        self.tokenized_service_texts = {language: []
                                        for language in SUPPORTED_LANGUAGES}
        for service in self.db.get_services():
            for language in self.tokenized_service_texts.keys():
                self.tokenized_service_texts[language].append(
                    self._tokenize_text(service["text"][language], language))

    def _create_ngrams(self, text: str, ngram_min: int, ngram_max: int) -> list:
        text_ngrams_total = []
        for i in range(ngram_min, ngram_max + 1):
            text_ngrams_total.append([''.join(gram)
                                     for gram in ngrams(text, i)])
        return list(set([item for sublist in text_ngrams_total for item in sublist]))

    def _clean_text(self, text: str) -> list:

        transl_table = dict([(ord(x), ord(y))
                             for x, y in zip(u"‘’´“”–-",  u"'''\"\"--")])
        text_mod = text.translate(transl_table)
        text_mod = re.sub(r"[^a-zA-Z0-9À-ÿ '%&#€$£=@+()!?%]", " ", text_mod)
        cleant_text = ' '.join(text_mod.split())
        cleant_text = cleant_text.lower()
        return(cleant_text)

    def _tokenize_text(self, text: str, language: str) -> list:
        cleant_text = self._clean_text(text)
        tokenized_text = word_tokenize(
            cleant_text, language=SUPPORTED_LANGUAGES.get(language))
        tokenized_text = [
            text for text in tokenized_text if text.isalpha() and text not in stopwords[language]]
        tokenized_text_ngrams = [self._create_ngrams(
            text, self.ngram_min.get(language, 0), self.ngram_max.get(language, 0)) for text in tokenized_text]
        tokenized_text_ngrams = [
            item for sublist in tokenized_text_ngrams for item in sublist]
        return list(set(tokenized_text + tokenized_text_ngrams))

    def create_bm25(self, CreateBM25: CreateBM25) -> None:
        self.ngram_min = CreateBM25.ngram_min
        self.ngram_max = CreateBM25.ngram_max
        self.bm25_k1 = CreateBM25.bm25_k1
        self.bm25_b = CreateBM25.bm25_b
        self._tokenize_service_texts()
        self.bm25 = {}
        for language in SUPPORTED_LANGUAGES:
            self.bm25[language] = BM25Plus(self.tokenized_service_texts[language],
                                           k1=CreateBM25.bm25_k1, b=CreateBM25.bm25_b)
        return "Successfully created BM25 models"

    def search_services(self, ServiceSearchQuery: ServiceSearchQuery) -> ServiceSearchResponse:
        tokenized_text = self._tokenize_text(
            ServiceSearchQuery.text, ServiceSearchQuery.language)
        scores = self.bm25[ServiceSearchQuery.language].get_scores(
            tokenized_text)
        if ServiceSearchQuery.top_k <= 0:
            top_k = np.argsort(scores)[::-1]
        else:
            top_k = np.argsort(scores)[::-1][:ServiceSearchQuery.top_k]
        results = [{"score": scores[i], "text": self.db.get_services_by_index(
            i)["text"][ServiceSearchQuery.language], "id": self.db.get_services_by_index(i)["id"]} for i in top_k]
        return ServiceSearchResponse(
            services=results
        )

    def update_services(self) -> str:
        updated_services_msg = self.db.update_services()
        # Update also BM25 index with new services
        # Use existing BM25 parameters so that if user has called /createBM25 endpoint to update their values
        # they won't get overrided with the defaults
        self.create_bm25(CreateBM25(
            ngram_min=self.ngram_min, ngram_max=self.ngram_max, bm25_k1=self.bm25_k1, bm25_b=self.bm25_b))
        return updated_services_msg
