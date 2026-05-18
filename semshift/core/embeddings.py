"""Embedding backends for semantic matching."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import numpy as np

DEFAULT_MODEL = "tfidf"
TFIDF_ALIASES = {"tfidf", "local", "local-tfidf", "heuristic"}


@dataclass(frozen=True)
class EmbeddingResult:
    """Vectors and backend metadata."""

    vectors: np.ndarray
    backend: str
    warnings: tuple[str, ...] = ()


def embed_texts(texts: list[str], model_name: str = DEFAULT_MODEL) -> EmbeddingResult:
    """Embed texts with SentenceTransformers, falling back to local TF-IDF."""
    if not texts:
        return EmbeddingResult(vectors=np.zeros((0, 0)), backend="empty")

    requested = model_name.strip() if model_name else DEFAULT_MODEL
    if requested.lower() in TFIDF_ALIASES:
        return _tfidf_embeddings(texts, backend="tfidf")

    try:
        model = _load_sentence_transformer(requested)
        vectors = model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return EmbeddingResult(vectors=np.asarray(vectors, dtype=float), backend=requested)
    except Exception as exc:  # pragma: no cover - depends on local model availability
        warning = (
            f"Could not load SentenceTransformer model '{requested}' ({exc}). "
            "Falling back to local TF-IDF embeddings."
        )
        fallback = _tfidf_embeddings(texts, backend="tfidf-fallback")
        return EmbeddingResult(
            vectors=fallback.vectors,
            backend=fallback.backend,
            warnings=(warning,),
        )


@lru_cache(maxsize=4)
def _load_sentence_transformer(model_name: str):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def _tfidf_embeddings(texts: list[str], backend: str) -> EmbeddingResult:
    from sklearn.feature_extraction.text import TfidfVectorizer

    if not any(text.strip() for text in texts):
        return EmbeddingResult(vectors=np.zeros((len(texts), 1)), backend=backend)

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), lowercase=True)
    try:
        matrix = vectorizer.fit_transform(texts)
    except ValueError:
        return EmbeddingResult(vectors=np.zeros((len(texts), 1)), backend=backend)
    return EmbeddingResult(vectors=matrix.astype(float).toarray(), backend=backend)

