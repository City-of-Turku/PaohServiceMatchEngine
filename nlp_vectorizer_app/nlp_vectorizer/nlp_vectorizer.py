import os
from typing import Optional
import re
from sentence_transformers import SentenceTransformer
from .models import *
from .data_cleaner import *

class NlpVectorizer():
    """
    A class used to vectorize text with SentenceTransformer model.

    Args
    ----------
    vectorizer : SentenceTransformer (default None)
        SentenceTransformer vectorizer object


    Methods
    -------
    vectorize(VectorizeQuery: VectorizeQuery)
        Returns vectorized text as a list
    """

    def __init__(self, vectorizer: Optional[SentenceTransformer] = None) -> None:
        if vectorizer is None:
            self.vectorizer = SentenceTransformer(
                os.environ.get('NLP_MODEL_NAME'), cache_folder=os.environ.get('NLP_MODELS_MOUNT_PATH'))
        else:
            self.vectorizer = vectorizer
        self.data_cleaner = DataCleaner()

    def vectorize(self, VectorizeQuery: VectorizeQuery) -> VectorResponse:
        cleaned_text = self.data_cleaner.clean_text(VectorizeQuery.text)
        vector = self.vectorizer.encode(
            cleaned_text, convert_to_tensor=True, normalize_embeddings=True)
        return VectorResponse(
            vector=vector.tolist()
        )
